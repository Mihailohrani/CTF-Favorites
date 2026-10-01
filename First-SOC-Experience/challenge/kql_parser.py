import re

SCHEMA = {
    "SigninLogs": {
        "Timestamp", "User", "IPAddress", "ResultType", "Location", "Application"
    },
    "EmailEvents": {
        "Timestamp", "Sender", "Recipient", "Subject", "DeliveryAction",
        "Url", "AttachmentName", "MessageId"
    },
    "DeviceLogonEvents": {
        "Timestamp", "DeviceName", "AccountName", "LogonType",
        "RemoteIP", "ActionType"
    },
    "DeviceProcessEvents": {
        "Timestamp", "DeviceName", "AccountName", "ProcessName",
        "ProcessCommandLine", "ParentProcessName"
    },
    "DeviceNetworkEvents": {
        "Timestamp", "DeviceName", "AccountName", "InitiatingProcessFileName",
        "RemoteIP", "RemotePort", "RemoteUrl", "ActionType"
    },
}

MAX_LIMIT = 500


class KQLError(ValueError):
    pass


def _identifier(name: str, table: str) -> str:
    name = name.strip()

    # only allow columns we actually know about
    if name not in SCHEMA[table]:
        raise KQLError(f"unknown column: {name}")

    return f'"{name}"'


def _split_csv(value: str):
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_literal(raw: str):
    raw = raw.strip()

    if len(raw) >= 2:
        if raw[0] == raw[-1] and raw[0] in ('"', "'"):
            return raw[1:-1]

    if re.fullmatch(r"-?\d+", raw):
        return int(raw)

    if re.fullmatch(r"-?\d+\.\d+", raw):
        return float(raw)

    raise KQLError("values must be quoted strings or numbers")


def _split_and(expression: str):
    parts = []
    current = []
    quote = None
    i = 0

    # cant just split normally because and could be inside a string
    while i < len(expression):
        ch = expression[i]

        if quote:
            current.append(ch)

            if ch == quote and (i == 0 or expression[i - 1] != "\\"):
                quote = None

            i += 1
            continue

        if ch in ('"', "'"):
            quote = ch
            current.append(ch)
            i += 1
            continue

        if expression.startswith("&&", i):
            parts.append("".join(current).strip())
            current = []
            i += 2
            continue

        if expression[i:i + 5].lower() == " and ":
            parts.append("".join(current).strip())
            current = []
            i += 5
            continue

        current.append(ch)
        i += 1

    if quote:
        raise KQLError("unterminated quoted string")

    parts.append("".join(current).strip())

    return [part for part in parts if part]


def _parse_condition(condition: str, table: str):
    string_pattern = (
        r"^([A-Za-z_][A-Za-z0-9_]*)\s+"
        r"(contains|has|startswith|endswith)\s+(.+)$"
    )

    compare_pattern = (
        r"^([A-Za-z_][A-Za-z0-9_]*)\s*"
        r"(==|!=|>=|<=|>|<)\s*(.+)$"
    )

    match = re.match(string_pattern, condition, flags=re.IGNORECASE)

    if match:
        column = _identifier(match.group(1), table)
        operator = match.group(2).lower()
        value = _parse_literal(match.group(3))

        if not isinstance(value, str):
            raise KQLError(f"{operator} requires a string value")

        if operator in ("contains", "has"):
            value = f"%{value}%"
        elif operator == "startswith":
            value = f"{value}%"
        elif operator == "endswith":
            value = f"%{value}"

        return f"{column} LIKE ?", [value]

    match = re.match(compare_pattern, condition, flags=re.IGNORECASE)

    if match:
        column = _identifier(match.group(1), table)
        operator = match.group(2)
        value = _parse_literal(match.group(3))

        if operator == "==":
            operator = "="

        return f"{column} {operator} ?", [value]

    raise KQLError(f"unsupported where condition: {condition}")


def translate_kql_to_sql(kql: str):
    if not isinstance(kql, str) or not kql.strip():
        raise KQLError("query is empty")

    parts = [part.strip() for part in kql.split("|") if part.strip()]

    table = parts[0]

    if table not in SCHEMA:
        raise KQLError("invalid table")

    select = "*"
    where_clauses = []
    params = []

    group_by = ""
    order_by = ""
    limit = ""

    distinct = False

    for part in parts[1:]:
        lower = part.lower()

        if lower.startswith("where "):
            expression = part[6:].strip()

            for condition in _split_and(expression):
                sql_condition, values = _parse_condition(condition, table)
                where_clauses.append(sql_condition)
                params.extend(values)

        elif lower.startswith("project "):
            columns = _split_csv(part[8:])

            if not columns:
                raise KQLError("project requires at least one column")

            select = ", ".join(
                _identifier(column, table)
                for column in columns
            )

        elif lower.startswith("distinct "):
            columns = _split_csv(part[9:])

            if not columns:
                raise KQLError("distinct requires at least one column")

            select = ", ".join(
                _identifier(column, table)
                for column in columns
            )

            distinct = True

        elif lower == "count":
            select = "COUNT(*) AS count"
            group_by = ""

        elif lower.startswith("summarize "):
            expression = part[10:].strip()

            # this one is kinda annoying but should work tbh
            match = re.fullmatch(
                r"count\(\)(?:\s+by\s+(.+))?",
                expression,
                flags=re.IGNORECASE,
            )

            if not match:
                raise KQLError(
                    "only summarize count() [by col1, col2] is supported"
                )

            group_text = match.group(1)

            if group_text:
                columns = _split_csv(group_text)

                quoted_columns = [
                    _identifier(column, table)
                    for column in columns
                ]

                select = (
                    ", ".join(quoted_columns)
                    + ", COUNT(*) AS count"
                )

                group_by = "GROUP BY " + ", ".join(quoted_columns)

            else:
                select = "COUNT(*) AS count"
                group_by = ""

        elif lower.startswith("sort by "):
            sort_text = part[8:].strip()

            match = re.fullmatch(
                r"([A-Za-z_][A-Za-z0-9_]*|count)"
                r"(?:\s+(asc|desc))?",
                sort_text,
                flags=re.IGNORECASE,
            )

            if not match:
                raise KQLError("invalid sort expression")

            column = match.group(1)
            direction = (match.group(2) or "asc").upper()

            if column.lower() == "count":
                sort_column = "count"
            else:
                sort_column = _identifier(column, table)

            order_by = f"ORDER BY {sort_column} {direction}"

        elif lower.startswith("top "):
            match = re.fullmatch(
                r"top\s+(\d+)\s+by\s+"
                r"([A-Za-z_][A-Za-z0-9_]*|count)"
                r"(?:\s+(asc|desc))?",
                part,
                flags=re.IGNORECASE,
            )

            if not match:
                raise KQLError(
                    "top syntax is: top N by Column [asc|desc]"
                )

            amount = int(match.group(1))
            amount = min(amount, MAX_LIMIT)

            column = match.group(2)
            direction = (match.group(3) or "desc").upper()

            if column.lower() == "count":
                sort_column = "count"
            else:
                sort_column = _identifier(column, table)

            order_by = f"ORDER BY {sort_column} {direction}"
            limit = f"LIMIT {amount}"

        elif lower.startswith("limit ") or lower.startswith("take "):
            raw = part.split(None, 1)[1].strip()

            if not raw.isdigit():
                raise KQLError(
                    "limit/take requires a positive integer"
                )

            amount = int(raw)

            if amount < 1:
                raise KQLError(
                    "limit/take must be at least 1"
                )

            # dont let queries return some massive amount
            amount = min(amount, MAX_LIMIT)
            limit = f"LIMIT {amount}"

        else:
            raise KQLError(f"unsupported operator: {part}")

    where = ""

    if where_clauses:
        where = "WHERE " + " AND ".join(where_clauses)

    distinct_sql = "DISTINCT " if distinct else ""

    query_parts = [
        f"SELECT {distinct_sql}{select}",
        f'FROM "{table}"',
        where,
        group_by,
        order_by,
        limit,
    ]

    sql = " ".join(
        query_part
        for query_part in query_parts
        if query_part
    )

    return sql, params
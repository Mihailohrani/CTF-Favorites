from flask import Flask, jsonify, render_template, request
import duckdb

from kql_parser import KQLError, translate_kql_to_sql

app = Flask(__name__)
db = duckdb.connect("logs.db", read_only=True)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/query")
def query():
    payload = request.get_json(silent=True) or {}
    kql = payload.get("query", "")

    try:
        sql, params = translate_kql_to_sql(kql)
        result = db.execute(sql, params).fetchall()
        columns = [column[0] for column in db.description]

        return jsonify({
            "columns": columns,
            "rows": result[:500],
        })

    except KQLError as exc:
        return jsonify({"error": str(exc)}), 400
    except duckdb.Error:
        return jsonify({"error": "query could not be executed"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001)

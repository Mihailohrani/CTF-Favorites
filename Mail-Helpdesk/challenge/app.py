from flask import Flask, render_template, request
import os
import subprocess

app = Flask(__name__)

FLAG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flag.txt")

@app.route("/", methods=["GET"])
def index():
    return render_template("support_form.html")

@app.route("/support", methods=["POST"])
def support():
    to_addr = request.form.get("to", "")
    subject = request.form.get("subject", "")
    message = request.form.get("message", "")
    from_addr = request.form.get("from", "")
    mail_options = request.form.get("mail_options", "")

    cmd = f"/usr/sbin/sendmail -t -i {mail_options}"
    
    email_body = f"""To: {to_addr}
From: {from_addr}
Subject: {subject}

{message}
"""
    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = proc.communicate(input=email_body, timeout=10)
        if stderr:
            result = stderr
        else:
            result = "Message queued for delivery."
    except subprocess.TimeoutExpired:
        result = "Request timed out."
    except Exception as e:
        result = f"Error: {str(e)}"

    return render_template("result.html", result=result, cmd=cmd)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6789, debug=False)

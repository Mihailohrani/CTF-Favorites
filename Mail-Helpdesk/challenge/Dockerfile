FROM python:3.11-slim

RUN rm -f /usr/sbin/sendmail && \
    printf '#!/bin/sh\necho "Message queued"\nexit 0\n' > /usr/sbin/sendmail && \
    chmod +x /usr/sbin/sendmail

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ ./templates/
COPY flag.txt /app/flag.txt

RUN chmod 444 /app/flag.txt && \
    chown root:root /app/flag.txt

RUN useradd -m -s /bin/bash ctfuser

USER ctfuser

EXPOSE 6789

CMD ["python", "app.py"]

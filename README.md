# CTF Favorites

A collection of CTF challenges, write-ups, and projects I've enjoyed working on.

The hard part is actually writing and posting them here... but eventually I'm sure the good ones will be here.

## Projects

### First SOC Experience

A blue team CTF challenge I built to give beginners a small taste of what investigating an incident in a SOC can look like.

It includes a small KQL-inspired query language called MQL (Misha Query Language), synthetic security logs, and an investigation that involves pivoting between different telemetry sources to reconstruct an attack.

### Mail Helpdesk

A web CTF challenge I built around a small internal IT helpdesk portal.

The challenge is based around a command injection vulnerability in the way user-controlled mail options are passed to `sendmail`. Getting command execution is fairly straightforward, but getting the flag back requires paying attention to how the application handles stdout and stderr, as well as how the payload is encoded before reaching the shell.

More CTFs and write-ups will be added here over time.
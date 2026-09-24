
⚠️ Le service est sur le **port 5001**, pas 80/443.

## Découverte

Page d'accueil (`http://10.10.0.49:5001/`) renvoie vers `/homework` : un formulaire d'upload de fichier `.hs`, censé être envoyé à un "outil d'autocorrection" Haskell. Le pitch de la page ("c'est sécurisé car c'est Haskell") est un piège du challenge.

## Exploitation — RCE via upload Haskell

Le fichier uploadé est réellement compilé et exécuté côté serveur (`ghc`, output visible dans la réponse). `System.Process.callCommand` permet l'exécution de commandes shell arbitraires, en tant que `www-data`.

Payload minimal qui marche :

```haskell
import System.Process

main :: IO ()
main = do
  putStrLn "I love Haskell"
  callCommand "<COMMANDE>"
```

⚠️ Le serveur gère mal plusieurs commandes enchaînées dans un seul `callCommand` (renvoie `Couldn't compile your haskell program`). Il faut décomposer : **une commande simple par upload**.

## Chemin jusqu'à user.txt
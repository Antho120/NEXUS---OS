# NEXUS-OS 0.3.0 — Android / Termux

## Installation sûre

1. Télécharge l'archive ZIP.
2. Dans Termux, décompresse-la dans `~/NEXUS-OS` (remplace le chemin du ZIP si nécessaire) :
   ```sh
   cd ~/NEXUS-OS
   unzip -o ~/storage/downloads/NEXUS-OS-v0.3.0.zip
   bash install.sh
   ```
3. Lance le serveur :
   ```sh
   python src/core/server.py
   ```
4. Ouvre `http://127.0.0.1:8080` dans ton navigateur.

Le script sauvegarde les fichiers existants avant de les remplacer. La sauvegarde `~/NEXUS-OS-backup.tar.gz` n'est pas touchée.

## Inclus

- Bureau NEXUS responsive
- API de statut et de santé
- Explorateur limité au dossier du projet : navigation, création, lecture, édition, renommage, suppression
- Terminal de diagnostic avec liste blanche de commandes
- Serveur local lié à `127.0.0.1:8080`
- Python standard library uniquement

## Sécurité et limites

L'explorateur est confiné à la racine du projet. Le terminal refuse toute commande non autorisée. Le serveur écoute uniquement sur localhost.

Cette version est une base logicielle locale fonctionnelle, pas un système Android natif ni un remplacement du système d'exploitation du téléphone. NEXUS AI, la surveillance système avancée, le réseau et l'automatisation sont les prochaines étapes.

#!/data/data/com.termux/files/usr/bin/bash
set -e
ROOT="$HOME/NEXUS-OS"
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -d "$ROOT" ] || { echo "Dossier ~/NEXUS-OS introuvable."; exit 1; }
[ -d "$HERE/payload" ] || { echo "Dossier payload introuvable. Décompresse l'archive complète."; exit 1; }
cd "$ROOT"
STAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p ".nexus-backups/$STAMP"
for f in src/core/server.py src/core/main.py src/interface/web/index.html; do
  if [ -f "$f" ]; then
    mkdir -p ".nexus-backups/$STAMP/$(dirname "$f")"
    cp -p "$f" ".nexus-backups/$STAMP/$f"
  fi
done
cp -R "$HERE/payload/." "$ROOT/"
echo
echo "NEXUS-OS 0.3.0 installé."
echo "Sauvegarde précédente : $ROOT/.nexus-backups/$STAMP"
echo "Lancement : cd ~/NEXUS-OS && python src/core/server.py"

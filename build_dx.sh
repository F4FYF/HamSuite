#!/bin/bash

# Configuration
APP_NAME="dxcluster_f4fyf"
SCRIPT_FILE="dxcluster_f4fyf.py"
DATA_FILE="cty.dat"
URL_CTY="https://www.country-files.com/cty/cty.dat"

echo "--- Préparation de la compilation (F4FYF Terminal) ---"

# 1. Mise à jour de la base de données CTY
echo "[1/5] Mise à jour de $DATA_FILE depuis country-files.com..."
curl -s -o "$DATA_FILE" "$URL_CTY"

if [ $? -eq 0 ]; then
    echo "      Base de données mise à jour avec succès."
else
    echo "      AVERTISSEMENT : Échec du téléchargement. Utilisation du fichier local si présent."
fi

# 2. Nettoyage des anciennes compilations
echo "[2/5] Nettoyage des dossiers build/ et dist/..."
rm -rf build dist *.spec

# 3. Vérification finale du fichier DATA
if [ ! -f "$DATA_FILE" ]; then
    echo "ERREUR : Le fichier $DATA_FILE est absent et n'a pas pu être téléchargé !"
    exit 1
fi

# 4. Lancement de PyInstaller
echo "[3/5] Création de l'exécutable (Patientez...)"
pyinstaller --noconsole \
            --onefile \
            --add-data "$DATA_FILE:." \
            --name "$APP_NAME" \
            "$SCRIPT_FILE"

# 5. Finalisation
if [ $? -eq 0 ]; then
    echo "[4/5] Compilation réussie !"
    echo "[5/5] Application des permissions d'exécution..."
    chmod +x dist/"$APP_NAME"
    echo "----------------------------------------------------"
    echo "TERMINÉ : Ton exécutable est prêt dans 'dist/'"
    echo "Version du cluster configurée pour : dxc.f5len.org:7000"
else
    echo "ERREUR : La compilation a échoué."
fi

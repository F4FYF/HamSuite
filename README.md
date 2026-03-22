# HamSuite
Dxcluster and CAT control


DXcluster_F4fyf est un client DX Cluster léger et performant écrit en Python. Il permet de visualiser en temps réel les spots radioamateurs tout en offrant une intégration CAT (via Hamlib/rigctld) pour un pilotage direct de votre émetteur-récepteur.
🚀 Fonctionnalités

    . Real-Time DX Spotting : Connexion Telnet aux clusters mondiaux (par défaut dxc.f5len.org).

    . Intégration RIG (Hamlib) :

    . Lecture de la fréquence en temps réel.

    . QSY Instantané : Double-cliquez sur un spot dans la liste pour caler automatiquement votre radio sur la fréquence du contact.

     . Filtrage Intelligent :

     . Filtres par bandes (de 160m à 23cm).

     . Filtres par modes (détection auto FT8, CW, SSB).

     . Filtres géographiques (continent, pays).

     . Calculs Géodésiques : Calcul automatique de la distance et de l'azimut (Beam Heading) entre votre locator et le spot.

    Interface High-Tech : Design sombre optimisé pour la fatigue oculaire lors des sessions nocturnes, avec code couleur par continent.

🛠️ Installation
Prérequis

    Python 3.x

    Les bibliothèques standards de Python (tkinter, telnetlib, socket, etc.).

    Un serveur rigctld (Hamlib) lancé si vous souhaitez utiliser le contrôle de la radio.

Fichiers nécessaires

Assurez-vous d'avoir le fichier de base de données DXCC dans le même répertoire :

    cty.dat : Fichier de définition des préfixes mondiaux (indispensable pour l'identification des pays).

Lancement
Bash

python3 dxcluster_f4fyf.py

⚙️ Configuration

Au premier lancement, renseignez vos informations dans le panneau SYSTEM CONFIG :

    Cluster Host/Port : Serveur de cluster préféré.

    Callsign : Votre indicatif pour le login.

    My Locator : Votre Locator SUR 2 DIGITS !!  (ex: JN25) pour les calculs de distance.

    Rig Host/Port : Adresse de votre instance rigctld (généralement 127.0.0.1 port 4532).

Les réglages sont automatiquement sauvegardés dans un fichier config_radio.json.
🎨 Code Couleurs (Continents)

L'application utilise un code couleur spécifique pour identifier rapidement la provenance des spots :

    🔵 EU : Europe

    🟠 NA : Amérique du Nord

    💗 AF : Afrique

    🟣 AS : Asie

    🟢 SA : Amérique du Sud

    💎 OC : Océanie

INSTALLATION : 

    $ git clone https://github.com/F4FYF/HamSuite
    $ cd HamSuite
    $ chmod +x build_dx.sh
    $ ./build_dx.sh

LANCEMENT DE L'APPLICATION :

    $ ./dist/dxcluster_f4fyf
    ou directement dans HamSuite :
    $ python3 dxcluster_f4fyf.py

Plus d'infos ici : https://f4fyf.blogspot.com/

73 de Jeff F4FYF

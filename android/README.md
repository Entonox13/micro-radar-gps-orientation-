# Micro Radar — Application Android

Portage Kivy de l'application desktop Python : mêmes options, même moteur radar et même client OpenSky.

## Fonctionnalités

| Option | Description |
|--------|-------------|
| Position GPS | Latitude / longitude, collage depuis Google Maps |
| Rayon | En degrés (max 2,5) |
| OpenSky | Client ID / Secret (optionnel) |
| Rotation boussole | Fait tourner la carte (cap simulé pour l'instant) |
| Cap | Boussole interne du téléphone (rotation vector / magnétomètre) ou slider de secours |
| Offset boussole | Correction en degrés si le nord est décalé |
| Mode batterie | Intervalle API allongé |
| Ligne de balayage | Active/désactive le sweep |
| Triangles directionnels | Affiche la trajectoire des avions |
| Infos avion | Indicatif + altitude |
| Plein écran | Bouton **Plein écran** sur le radar |
| Quitter plein écran | **Double tap** sur le radar |

## APK via GitHub Actions

À chaque push sur `main` (ou manuellement via **Actions → Build Android APK → Run workflow**), le workflow compile une APK debug installable.

1. Ouvrez l'onglet **Actions** du dépôt
2. Sélectionnez le run **Build Android APK**
3. Téléchargez l'artifact **micro-radar-debug-apk**
4. Installez sur Android : autorisez les sources inconnues, puis ouvrez l'APK

La première compilation peut prendre ~30–60 min (téléchargement SDK/NDK). Les runs suivants sont plus rapides grâce au cache.

## Build local

Prérequis : Linux (ou WSL), Java 17, dépendances buildozer.

```bash
cd android
cp -r ../microradar_core ./microradar_core
pip install buildozer cython==0.29.36
buildozer android debug
```

L'APK se trouve dans `android/bin/`.

## Test UI sur bureau (sans build Android)

```bash
pip install -r android/requirements.txt
python android/main.py
```

## Configuration

Les réglages sont sauvegardés dans le stockage interne de l'app (`config.json`). Les identifiants OpenSky peuvent aussi être placés dans `credentials.json` (export compte OpenSky).

## Prochaine étape

- GPS du téléphone comme centre du radar

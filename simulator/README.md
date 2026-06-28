# Micro Radar — Simulateur desktop

Application Python/Tkinter pour tester le radar **sans matériel** : même API OpenSky, même projection et même logique de suivi que le firmware ESP32.

## Prérequis

- Python 3.10+
- Connexion internet

## Installation

```bash
cd simulator
pip install -r requirements.txt
```

## Lancement

```bash
python app.py
```

## Utilisation

1. Cliquez sur **Ma position (IP)** pour centrer le radar sur votre zone (approximation via IP).
2. Ajustez le **rayon** (en degrés, max 2.5 comme sur l'appareil).
3. Optionnel : renseignez vos identifiants **OpenSky** pour passer de 400 à 4000 requêtes/jour (~22 s entre chaque mise à jour).
4. Cliquez sur **Rafraîchir** ou attendez le fetch automatique.
5. Lisez le panneau **Statut / fiabilité** pour savoir si le projet serait animé chez vous.

## Options testables

| Option | Effet |
|--------|-------|
| Rotation boussole | Fait tourner la carte comme sur l'appareil portable |
| Cap simulé | Slider 0–360° pour simuler l'orientation |
| Mode batterie | Même intervalle API allongé que le firmware |
| Ligne de balayage | Active/désactive le sweep |

La configuration est sauvegardée dans `simulator/config.json`.

## Limites

- La géolocalisation IP est approximative (ville/région, pas le mètre près).
- Pas de GPS/boussole réels : utilisez lat/lon manuels pour une position exacte.
- Même source de données que l'appareil (OpenSky) : si le simulateur voit peu d'avions, l'appareil aussi.

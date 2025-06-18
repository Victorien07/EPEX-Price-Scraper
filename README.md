# 📊 EPEX Price Scraper

Ce projet automatise la collecte quotidienne des **prix de l'électricité (EPEX Spot - France Day-Ahead)**, du **gaz (PEG Day-Ahead)** et du **CO₂ (EUA Futures)**.  
Les données sont extraites depuis les sites officiels, archivées en HTML, puis converties automatiquement en fichier Excel.

---

## 🔄 Fonctionnement

- 🕒 Tous les jours à **15h00 (heure de Paris)**, le scraper télécharge les pages HTML suivantes :
  - ⚡ Électricité : prix Day-Ahead du **lendemain (J+1)**
  - 🔥 Gaz : prix PEG Day-Ahead de la **veille (J-1)**
  - 🌿 CO₂ : prix "Last Price" EUA de la **veille (J-1)**

- 🧹 À **15h15 (heure de Paris)** :
  - Les données sont extraites depuis les fichiers HTML
  - Les prix sont insérés dans un fichier Excel multi-feuilles :
    - Feuille 1 : `Prix Spot` (électricité heure par heure)
    - Feuille 2 : `Gaz` (Last Price, Last Volume, End of Day Index)
    - Feuille 3 : `CO2` (Last Price)

- 📁 Les fichiers HTML sont archivés dans :
  - `archives/html` pour l’électricité
  - `archives/html_gaz` pour le gaz
  - `archives/html_co2` pour le CO₂

- 📈 Le fichier de données final est généré automatiquement :
  👉 [`data/epexspot_prices.xlsx`](data/epexspot_prices.xlsx)

⚠️ **Remarques** :
- Si les données ne sont pas encore publiées au moment de la récupération, elles sont marquées par un tiret `-` dans l’Excel.
- En cas de doublon HTML pour une même date, seul le fichier **le plus récent** est pris en compte.
- L’automatisation repose sur GitHub Actions, et peut subir un retard selon la charge des serveurs.

---

## 📬 Contact

Pour toute question ou contribution :  
📧 victorien.ficheux@edf.fr

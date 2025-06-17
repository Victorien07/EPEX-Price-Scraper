# 📊 EPEX Price Scraper

Ce projet automatise la collecte quotidienne des **prix de l'électricité sur EPEX Spot (France - Day-Ahead)**.  
Les données sont extraites depuis le site officiel, archivées en HTML et converties automatiquement en CSV.

---

## 🔄 Fonctionnement

- 🕒 Le scraper se lance tous les jours à **15h00 (Paris)** pour récupérer la page HTML.
- 🧹 À **15h15 (Paris)**, un second job extrait les **prix horaires** et les ajoute à un fichier CSV.
- 📁 Les fichiers HTML sont archivés dans [`archives/html`](archives/html).
- 📈 Le fichier de données final est disponible ici :  
  👉 [`data/epexspot_prices.csv`](data/epexspot_prices.csv)
  👉 [`data/epexspot_prices.xlsx`](data/epexspot_prices.xlsx)

⚠️ **Note** : l'exécution automatique peut avoir du retard, en raison des files d’attente GitHub Actions.

---

## 📬 Contact

Pour toute question ou contribution :  
📧 victorien.ficheux@edf.fr


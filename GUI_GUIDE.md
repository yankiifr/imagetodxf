# Guide d'Utilisation de la GUI

## Lancement

```bash
python gui.py
```

## Interface

L'interface graphique offre :

### Zone de Fichiers
- 📁 **Drag & Drop** : Glissez-déposez vos images directement
- ➕ **Ajouter** : Bouton pour sélectionner des fichiers
- 🗑️ **Supprimer** : Retirer les fichiers sélectionnés
- 🧹 **Vider** : Vider toute la liste

### Options
- **Profil** : Sélectionnez scan/photo/drawing pour appliquer des préréglages
- **Checkboxes** :
  - 🧹 Clean : Active les filtres de nettoyage
  - 🔍 HQ : Mode Haute Qualité (upscaling x2)
  - 🤖 AI : Nettoyage par IA (Rembg)
  - 📦 Batch : Traite plusieurs fichiers

### Paramètres Avancés
- **Min Area** : Seuil de suppression des petits objets
- **Max Thick** : Épaisseur maximale des lignes à filtrer

### Bouton de Conversion
- 🚀 **CONVERTIR** : Lance le traitement

### Journal
- Affiche les logs en temps réel
- Résumé des succès/échecs

## Démo

```
1. Glissez plan1.jpg et plan2.jpg dans la zone
2. Sélectionnez "scan" dans Profil
3. Cochez "Batch"
4. Cliquez sur CONVERTIR
5. Les DXF sont générés dans le même dossier
```

## Dépendance

```bash
pip install tkinterdnd2
```

Si tkinterdnd2 n'est pas installé, le Drag & Drop sera désactivé mais le reste fonctionne normalement.

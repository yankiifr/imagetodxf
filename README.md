# 📐 Image to DXF/DWG Converter

> Convertisseur intelligent d'images (plans, scans) vers des fichiers DXF/DWG pour CAO.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

## 🎯 Fonctionnalités

- ✅ **Conversion automatique** : JPG/PNG → DXF/DWG
- 🧠 **IA de nettoyage** : Suppression intelligente du fond (R embg)
- 🔍 **Mode Haute Qualité** : Upscaling x2 + seuillage adaptatif
- 🗑️ **Filtrage avancé** : Suppression du texte, cotes, et bruit
- 📦 **Mode Batch** : Traiter plusieurs fichiers d'un coup
- 🎨 **Profils prédéfinis** : Scan, Photo, Dessin
- 🤖 **Expérimental** : Génération via Gemini API

## 📋 Prérequis

### Dépendances Système

1. **Python 3.8+**
2. **Potrace** (inclus dans `potrace-1.16.win64/`)

```bash
python convert_plan.py plan.jpg
```

### Mode Recommandé (Qualité maximale)

```bash
python convert_plan.py plan.jpg --clean --hq
```

### Avec IA (Suppression de fond)

```bash
python convert_plan.py scan.jpg --clean --hq --ai
```

| `--ai` | Nettoyage par IA (Rembg). Supprime intelligemment le fond |
| `--gemini` | Génération par Gemini API (Expérimental) |
| `--batch` | Mode traitement multiple |
| `--preset <name>` | Utilise un profil prédéfini (scan, photo, drawing) |
| `--min-area N` | Supprime les objets < N px² (défaut: 20) |
| `--max-thickness N` | Supprime les lignes < N px d'épaisseur |
| `--min-len N` | Supprime les traits < N px de longueur |
| `--keep-temp` | Garde les fichiers temporaires (BMP, SVG) |
| `--output-dir DIR` | Dossier de sortie (mode batch) |

## 📊 Exemples de Résultats

### Comparaison des Modes

| Mode | Temps | Qualité | Usage recommandé |
|------|-------|---------|------------------|
| Standard | ~2s | ⭐⭐⭐ | Dessins propres |
| `--clean` | ~3s | ⭐⭐⭐⭐ | Scans avec texte |
| `--clean --hq` | ~8s | ⭐⭐⭐⭐⭐ | Photos/Scans complexes |
| `--clean --hq --ai` | ~15s | ⭐⭐⭐⭐⭐ | Scans de mauvaise qualité |

## 🔧 Configuration

Le fichier `config.json` permet de personnaliser les profils :

```json
{
  "presets": {
    "mon_profil": {
      "description": "Mon profil custom",
      "clean": true,
      "hq": true,
      "min_area": 75,
      "max_thickness": 6
    }
  }
}
```

## 🤔 FAQ

### Le fichier DXF est vide ?
- Vérifiez que l'image contient des lignes noires sur fond blanc.
- Essayez avec `--clean --hq` pour améliorer la détection.

### Trop de bruit dans le DXF ?
- Augmentez `--min-area 100` (supprime les petits objets).
- Ajoutez `--max-thickness 8` (supprime les lignes fines).

### Les cotes sont conservées ?
- Utilisez `--clean --max-thickness 5` pour les supprimer.

### Erreur "potrace not found" ?
- Vérifiez que le dossier `potrace-1.16.win64` est présent.
- Ou installez Potrace globalement : [http://potrace.sourceforge.net](http://potrace.sourceforge.net)

### Comment utiliser Gemini ?
1. Créez une clé API : [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Ajoutez-la dans `.env` : `GEMINI_API_KEY=votre_cle`
3. Lancez avec `--gemini`

**Note** : Les résultats Gemini sont expérimentaux et souvent imprécis pour la CAO.

## 📂 Structure du Projet

```
imagetodxf/
├── convert_plan.py          # Script principal
├── config.json              # Configuration et profils
├── requirements.txt         # Dépendances Python
├── .gitignore              # Fichiers ignorés
├── .env                    # Clés API (ne pas commiter)
├── gemini_prompt.txt       # Prompt personnalisable
├── potrace-1.16.win64/     # Binaire Potrace
└── README.md               # Ce fichier
```

## 🛠️ Développement

### Architecture

1. **Pré-traitement** : OpenCV / Rembg (IA)
2. **Vectorisation** : Potrace
3. **Conversion** : SVG → DXF (ezdxf)
4. **Export** : DXF → DWG (ODA)

### Ajouter un Profil

Éditez `config.json` :

```json
"presets": {
  "nouveau_profil": {
    "description": "Description",
    "clean": true,
    "hq": false,
    " min_area": 30
  }
}
```

## 📜 Licence

MIT License - Libre d'utilisation et de modification.

## 🙏 Remerciements

- [Potrace](http://potrace.sourceforge.net/) - Peter Selinger
- [ezdxf](https://ezdxf.readthedocs.io/) - Manfred Moitzi
- [Rembg](https://github.com/danielgatis/rembg) - Daniel Gatis
- [OpenCV](https://opencv.org/) - Open Source Computer Vision Library

---

**Made with ❤️ for CAD professionals**

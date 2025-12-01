# 📦 Build Exécutable Windows

Ce guide explique comment créer des exécutables Windows (.exe) pour le projet.

## 🚀 Build Automatique

### Windows

```bash
# Exécuter le script de build
build_exe.bat
```

Cette commande créera deux exécutables dans le dossier `dist/` :
- `ImageToDXF_GUI.exe` : Interface graphique (recommandé pour débutants)
- `ImageToDXF.exe` : Ligne de commande (pour utilisateurs avancés)

## 🛠️ Build Manuel

### Prérequis

```bash
pip install pyinstaller
```

### GUI Executable

```bash
pyinstaller --onefile --windowed ^
    --name ImageToDXF_GUI ^
    --add-data "config.json;." ^
    --add-data "potrace-1.16.win64;potrace-1.16.win64" ^
    --hidden-import=tkinterdnd2 ^
    --hidden-import=rembg ^
    --hidden-import=cv2 ^
    gui.py
```

### CLI Executable

```bash
pyinstaller --onefile --console ^
    --name ImageToDXF ^
    --add-data "config.json;." ^
    --add-data "potrace-1.16.win64;potrace-1.16.win64" ^
    convert_plan_v10.py
```

## 📋 Options PyInstaller

| Option | Description |
|--------|-------------|
| `--onefile` | Crée un seul fichier .exe |
| `--windowed` | Mode GUI (sans console) |
| `--console` | Mode CLI (avec console) |
| `--name` | Nom de l'exécutable |
| `--add-data` | Inclure fichiers de données |
| `--hidden-import` | Forcer import de modules |
| `--icon` | Icône personnalisée (.ico) |

## 📦 Distribution

### Taille des Fichiers

- **ImageToDXF_GUI.exe** : ~120 MB
- **ImageToDXF.exe** : ~100 MB

La taille importante est due à :
- OpenCV (~60 MB)
- Rembg + modèles IA (~40 MB)
- Bibliothèques Tkinter (~20 MB)

### Réduire la Taille

Pour créer des versions plus légères sans IA :

```bash
# Version Light (sans Rembg)
pyinstaller --onefile --console ^
    --name ImageToDXF_Light ^
    --add-data "config.json;." ^
    --add-data "potrace-1.16.win64;potrace-1.16.win64" ^
    --exclude-module rembg ^
    convert_plan_v10.py
```

## 🌐 Releases GitHub

Pour publier les exécutables sur GitHub :

1. Créer un tag de version :
```bash
git tag -a v10.0 -m "Version 10.0 - Batch, Profils, GUI"
git push origin v10.0
```

2. Aller sur GitHub → Releases → "Create a new release"

3. Uploader les fichiers :
   - `ImageToDXF_GUI.exe`
   - `ImageToDXF.exe`
   - `config.json` (exemple)

4. Publier avec notes de release

## ⚠️ Notes Importantes

### Antivirus
Les exe PyInstaller peuvent être signalés comme faux positifs par certains antivirus. C'est normal.

**Solutions** :
- Signer l'exe avec un certificat
- Ajouter exception antivirus
- Expliquer dans README que c'est open-source

### Dépendances
Les exe incluent TOUTES les dépendances Python, mais **PAS** :
- ODA File Converter (DWG export)
- Modèles Rembg (téléchargés au premier lancement)

### Performance
L'exe est légèrement plus lent au démarrage (~2s) que Python direct.

## 🔧 Troubleshooting

### Erreur "Failed to execute script"
→ Vérifier que tous les `--add-data` sont corrects

### Module manquant
→ Ajouter `--hidden-import=nom_module`

### Exe trop volumineux
→ Utiliser UPX compression :
```bash
pip install pyinstaller[compression]
pyinstaller ... --upx-dir=C:\upx
```

---

**Build testé sur** : Windows 10/11 x64  
**PyInstaller** : v6.0+

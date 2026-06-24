# 🚀 Release v10.0 - Complete Package

## 📦 Windows Executables

**Two standalone executables (no Python required):**

### ImageToDXF_GUI.exe (Recommended)
- 💻 **Size**: 586 MB
- 🖱️ **Interface**: Graphical with drag & drop
- 👥 **For**: Non-technical users
- ✨ **Features**: Profile selection, batch processing, real-time logs

### ImageToDXF.exe
- 💻 **Size**: 591 MB
- ⌨️ **Interface**: Command line
- 👥 **For**: Power users, automation
- ✨ **Features**: All CLI options available

---

## ✨ What's New in v10

### Major Features
- ✅ **Batch Processing**: Convert multiple files at once
- ✅ **Smart Profiles**: Pre-configured settings (scan, photo, drawing)
- ✅ **GUI Application**: Drag & drop interface with Tkinter
- ✅ **Centralized Config**: `config.json` for custom profiles
- ✅ **Portable**: Potrace bundled, works anywhere

### Technical Improvements
- 🔧 UTF-8 encoding fix for Windows emoji support
- 🚀 Performance optimizations (transform function)
- 📝 Comprehensive documentation (README, ROADMAP, BUILD_EXE)
- 🎯 Better error handling and user feedback

---

## 📥 Download & Install

### Option 1: Executables (Easiest)
1. Download `ImageToDXF_GUI.exe` (for GUI) or `ImageToDXF.exe` (for CLI)
2. Run directly - no installation needed!
3. ⚠️ Windows might show a warning (click "More info" → "Run anyway")

### Option 2: Python Source
```bash
git clone https://github.com/yankiifr/imagetodxf.git
cd imagetodxf
pip install -r requirements.txt
python gui.py  # or python convert_plan_v10.py
```

---

## 🚀 Quick Start

### GUI Mode
1. Double-click `ImageToDXF_GUI.exe`
2. Drag & drop your images
3. Select profile (scan/photo/drawing)
4. Click **CONVERT**
5. Done! DXF files are in the same folder

### CLI Mode
```bash
# Single file
ImageToDXF.exe plan.jpg --clean --hq

# Batch with profile
ImageToDXF.exe *.jpg --batch --preset scan

# Custom settings
ImageToDXF.exe image.png --clean --hq --ai --min-area 100
```

---

## 📋 System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4 GB minimum, 8 GB recommended
- **Disk**: 1.5 GB free space (executables + temp files)
- **Optional**: ODA File Converter for DWG export

---

## 🐛 Known Issues

- First launch may be slow (~5s) due to unpacking
- Antivirus false positives (PyInstaller common issue)
- Large file size due to bundled AI libraries (TensorFlow, OpenCV)

---

## 🗺️ Roadmap

See [ROADMAP.md](https://github.com/yankiifr/imagetodxf/blob/main/ROADMAP.md) for future plans:
- v11: Multi-threading, REST API, Docker
- v12: AI auto-detection, OCR, additional formats
- v13: Advanced AI (ControlNet, Super-Resolution)
- v14: AutoCAD/QGIS plugins, Marketplace

---

## 📚 Documentation

- [README.md](https://github.com/yankiifr/imagetodxf/blob/main/README.md) - User guide
- [BUILD_EXE.md](https://github.com/yankiifr/imagetodxf/blob/main/BUILD_EXE.md) - Build executables yourself
- [ROADMAP.md](https://github.com/yankiifr/imagetodxf/blob/main/ROADMAP.md) - Future features

---

## 🙏 Credits

- **Potrace** - Peter Selinger
- **ezdxf** - Manfred Moitzi
- **Rembg** - Daniel Gatis
- **OpenCV** - Open Source Computer Vision

---

## 📄 License

MIT License - Free to use and modify

---

**Made with ❤️ for CAD professionals**

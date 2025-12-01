@echo off
:: Script de build pour créer les exécutables Windows
:: Nécessite: pip install pyinstaller

echo ========================================
echo   Build EXE - Image to DXF Converter
echo ========================================
echo.

:: Vérifier si PyInstaller est installé
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [1/4] Installation de PyInstaller...
    pip install pyinstaller
) else (
    echo [1/4] PyInstaller deja installe
)

echo.
echo [2/4] Build GUI (ImageToDXF_GUI.exe)...
python -m PyInstaller --onefile --windowed ^
    --name ImageToDXF_GUI ^
    --icon=NONE ^
    --add-data "config.json;." ^
    --add-data "potrace-1.16.win64;potrace-1.16.win64" ^
    --hidden-import=tkinterdnd2 ^
    --hidden-import=rembg ^
    --hidden-import=cv2 ^
    gui.py

echo.
echo [3/4] Build CLI (ImageToDXF.exe)...
python -m PyInstaller --onefile --console ^
    --name ImageToDXF ^
    --icon=NONE ^
    --add-data "config.json;." ^
    --add-data "potrace-1.16.win64;potrace-1.16.win64" ^
    convert_plan_v10.py

echo.
echo [4/4] Nettoyage...
if exist build rmdir /s /q build
if exist *.spec del /q *.spec

echo.
echo ========================================
echo   BUILD TERMINE !
echo ========================================
echo.
echo Fichiers generes dans le dossier 'dist/' :
dir /b dist\*.exe 2>nul
if errorlevel 1 (
    echo ERREUR : Aucun exe genere. Verifiez les erreurs ci-dessus.
) else (
    echo.
    echo Taille approximative: ~150 MB par exe (avec toutes les dependances)
)
echo.
pause


@echo off
echo Installation des dependances pour ImageToDXF...
echo.
echo 1. Installation des librairies de base (Pillow, ezdxf, opencv, dotenv)...
pip install Pillow ezdxf svgelements opencv-python python-dotenv

echo.
echo 2. Installation de l'IA (Rembg) pour le mode --ai ...
echo Cela peut prendre un peu de temps (telechargement des modeles)...
pip install rembg

echo.
echo 3. Installation de l'API Gemini pour le mode --gemini ...
pip install google-generativeai

echo.
echo Installation terminee !
echo Vous pouvez maintenant utiliser : python convert_plan.py image.jpg --clean --ai --gemini
pause

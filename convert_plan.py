#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de conversion d'image (JPG/PNG) vers DXF/DWG pour CAO.

Ce script effectue les opérations suivantes :
1. Lit une image raster.
2. Nettoyage avancé avec OpenCV (suppression texte/bruit) si demandé.
3. Mode HQ (Optionnel) : Upscaling x2 et seuillage adaptatif.
4. Mode AI (Optionnel) : Utilise 'rembg' pour supprimer le fond via Deep Learning.
5. Mode Gemini (Optionnel) : Utilise l'API Gemini pour générer le SVG (Expérimental).
6. Convertit en BMP noir et blanc (préparation pour Potrace).
7. Utilise 'potrace' pour vectoriser en SVG (si pas Gemini).
8. Convertit le SVG résultant en DXF.
9. Convertit le DXF en DWG (si ODA File Converter est installé).

Dépendances Python :
    pip install Pillow ezdxf svgelements opencv-python rembg google-generativeai python-dotenv

Dépendances Système :
    - Potrace (Vectorisation) : http://potrace.sourceforge.net/
    - ODA File Converter (Optionnel, pour DWG) : https://www.opendesign.com/guestfiles/oda_file_converter
"""

import sys
import os
import subprocess
import argparse
import shutil
import re
import json
import glob
from pathlib import Path as FilePath
from PIL import Image
import ezdxf
from svgelements import SVG, Path, Line, Polyline, Polygon, Circle, Ellipse, Rect, QuadraticBezier, CubicBezier, Move

# Chargement des variables d'environnement (.env)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass # On continue, peut-être que la clé est dans l'OS

# Tentative d'import OpenCV
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

# Tentative d'import Rembg (AI)
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

# Tentative d'import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Configuration des chemins externes
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POTRACE_PATH = os.path.join(SCRIPT_DIR, "potrace-1.16.win64")
if os.path.exists(POTRACE_PATH):
    os.environ["PATH"] += os.pathsep + POTRACE_PATH

# Recherche automatique de ODA File Converter
ODA_PATHS = [
    r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe",
    r"C:\Program Files (x86)\ODA\ODAFileConverter\ODAFileConverter.exe"
]
ODA_EXE = None
for p in ODA_PATHS:
    if os.path.exists(p):
        ODA_EXE = p
        break

def check_dependencies():
    """Vérifie les dépendances système."""
    # Potrace
    try:
        subprocess.run(["potrace", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except FileNotFoundError:
        print("ERREUR CRITIQUE : 'potrace' n'est pas trouvé dans le PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur lors de la vérification de potrace : {e}")
        sys.exit(1)
    
    # ODA (Info seulement)
    if ODA_EXE:
        print(f"ODA File Converter détecté : {ODA_EXE}")
    else:
        print("ODA File Converter non détecté (Conversion DWG impossible).")

def clean_image_ai(input_path, output_path):
    """Utilise Rembg pour supprimer le fond (Deep Learning)."""
    if not REMBG_AVAILABLE:
        print("ERREUR : 'rembg' n'est pas installé. Installez-le avec : pip install rembg")
        return False
    
    print("Nettoyage AI (Rembg)...")
    try:
        with open(input_path, 'rb') as i:
            input_data = i.read()
            output_data = remove(input_data)
            
        # Sauvegarde temporaire du PNG transparent
        temp_png = output_path + ".rembg.png"
        with open(temp_png, 'wb') as o:
            o.write(output_data)
            
        # Conversion en image blanche avec fond blanc (pour OpenCV)
        # Rembg sort du RGBA. On doit composer sur blanc.
        with Image.open(temp_png) as img:
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3]) # 3 is the alpha channel
            background.save(output_path)
            
        if os.path.exists(temp_png):
            os.remove(temp_png)
            
        print("  - Fond supprimé avec succès.")
        return True
    except Exception as e:
        print(f"Erreur Rembg : {e}")
        return False

def clean_image_opencv(input_path, output_bmp_path, min_area=50, hq_mode=False, ai_mode=False):
    """Nettoyage OpenCV (Binarisation + Filtre taille)."""
    
    # Si AI mode, on pré-traite avec Rembg
    processed_input = input_path
    if ai_mode:
        ai_output = input_path + ".ai.jpg"
        if clean_image_ai(input_path, ai_output):
            processed_input = ai_output
        else:
            print("  -> Fallback sur nettoyage standard.")

    if not OPENCV_AVAILABLE:
        print("ATTENTION : OpenCV non installé. Nettoyage avancé ignoré.")
        preprocess_image_pil(processed_input, output_bmp_path)
        return

    print(f"Nettoyage avancé OpenCV (min_area={min_area}, HQ={hq_mode})...")
    img = cv2.imread(processed_input, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Erreur : Impossible de lire {processed_input}")
        sys.exit(1)

    # Upscaling en mode HQ
    if hq_mode:
        print("  - Upscaling x2 (Bicubic)...")
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        min_area = min_area * 4

    # Binarisation
    if hq_mode:
        print("  - Binarisation Adaptative...")
        binary = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY_INV, 11, 2)
    else:
        _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    new_binary = np.zeros_like(binary)

    removed_count = 0
    kept_count = 0

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_area:
            new_binary[labels == i] = 255
            kept_count += 1
        else:
            removed_count += 1

    print(f"  - Composants supprimés (< {min_area}px) : {removed_count}")
    print(f"  - Composants conservés : {kept_count}")

    final_img = cv2.bitwise_not(new_binary)
    cv2.imwrite(output_bmp_path, final_img)
    print(f"Image nettoyée sauvegardée : {output_bmp_path}")
    
    # Nettoyage fichier temp AI
    if ai_mode and os.path.exists(processed_input) and processed_input != input_path:
        os.remove(processed_input)

def preprocess_image_pil(input_path, output_bmp_path):
    """Conversion simple PIL (Fallback)."""
    print(f"Traitement simple (PIL) : {input_path}")
    try:
        with Image.open(input_path) as img:
            gray = img.convert("L")
            bw = gray.point(lambda x: 0 if x < 128 else 255, '1')
            bw.save(output_bmp_path, "BMP")
    except Exception as e:
        print(f"Erreur PIL : {e}")
        sys.exit(1)

def run_potrace(bmp_path, svg_path, turdsize=2, hq_mode=False):
    """Vectorisation Potrace."""
    print(f"Vectorisation (turdsize={turdsize}, HQ={hq_mode})...")
    try:
        cmd = ["potrace", bmp_path, "-s", "-o", svg_path, "-t", str(turdsize)]
        
        if hq_mode:
            cmd.extend(["--opttolerance", "0.1", "--alphamax", "1.2"])
            
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erreur Potrace : {e}")
        sys.exit(1)

def generate_svg_gemini(input_path, svg_path):
    """Utilise l'API Gemini pour générer le SVG."""
    if not GEMINI_AVAILABLE:
        print("ERREUR : 'google-generativeai' non installé.")
        return False
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERREUR : Clé API 'GEMINI_API_KEY' introuvable dans le fichier .env ou les variables d'environnement.")
        return False

    print("Génération SVG via Gemini API (Expérimental)...")
    try:
        genai.configure(api_key=api_key)
        
        # Utilisation de Gemini 2.0 Flash (disponible selon list_models.py)
        model_name = 'gemini-2.0-flash'
        try:
            model = genai.GenerativeModel(model_name)
        except:
            # Fallback sur un autre modèle si celui-ci échoue
            model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Lecture de l'image
        img = Image.open(input_path)

        # Lecture du prompt depuis le fichier externe
        prompt_file = os.path.join(os.path.dirname(__file__), "gemini_prompt.txt")
        if os.path.exists(prompt_file):
            with open(prompt_file, "r", encoding="utf-8") as f:
                prompt = f.read()
            print(f"Utilisation du prompt personnalisé : {prompt_file}")
        else:
            # Fallback prompt
            prompt = """
            You are an expert CAD drafter.
            Analyze this floor plan image.
            Generate a clean, simple SVG code representing ONLY the structural walls.
            - Ignore furniture, text, dimensions, and grid lines.
            - Use black lines (stroke="black") with a stroke-width of 2.
            - Ensure the SVG viewBox matches the image aspect ratio.
            - Output ONLY the raw SVG code (starts with <svg, ends with </svg>).
            - Do NOT use markdown code blocks.
            """

        response = model.generate_content([prompt, img])
        content = response.text

        # Nettoyage du code (au cas où il y a du markdown)
        content = content.replace("```svg", "").replace("```xml", "").replace("```", "").strip()
        
        # Extraction simple si le modèle a bavardé
        start = content.find("<svg")
        end = content.find("</svg>") + 6
        if start != -1 and end != -1:
            svg_code = content[start:end]
        else:
            svg_code = content # On espère que c'est bon

        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_code)
            
        print(f"SVG généré par Gemini : {svg_path}")
        return True

    except Exception as e:
        print(f"Erreur Gemini API : {e}")
        return False

def svg_to_dxf(svg_path, dxf_path, min_length=0, max_thickness=0, hq_mode=False):
    """Conversion SVG -> DXF avec filtres."""
    print("Conversion SVG vers DXF...")
    try:
        svg = SVG.parse(svg_path)
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        height = svg.height
        if height == 0: height = 1000 

        scale_factor = 0.5 if hq_mode else 1.0

        count = 0
        skipped_len = 0
        skipped_thick = 0

        for element in svg.elements():
            # Conversion de tout élément (Line, Rect, Circle...) en Path pour traitement uniforme
            try:
                if not isinstance(element, Path):
                    element = Path(element)
            except:
                continue

            if isinstance(element, Path):
                try:
                    # Filtre 1: Longueur
                    if min_length > 0 and element.length() < min_length:
                        skipped_len += 1
                        continue

                    if max_thickness > 0:
                        bbox = element.bbox()
                        if bbox:
                            w = bbox[2] - bbox[0]
                            h = bbox[3] - bbox[1]
                            thickness = min(w, h)
                            length = max(w, h)
                            aspect_ratio = length / thickness if thickness > 0 else 0

                            eff_max_thickness = max_thickness * 2 if hq_mode else max_thickness

                            if thickness < eff_max_thickness and aspect_ratio > 5:
                                skipped_thick += 1
                                continue
                except:
                    pass

                for segment in element:
                    if isinstance(segment, Move): continue
                    
                    def transform(p):
                        return (p.x * scale_factor, (height - p.y) * scale_factor)

                    if isinstance(segment, Line):
                        msp.add_line(transform(segment.start), transform(segment.end))
                    elif isinstance(segment, (QuadraticBezier, CubicBezier)):
                        if isinstance(segment, QuadraticBezier):
                            msp.add_spline([transform(segment.start), transform(segment.control), transform(segment.end)], degree=2)
                        else:
                            msp.add_spline([transform(segment.start), transform(segment.control1), transform(segment.control2), transform(segment.end)], degree=3)
                    elif isinstance(segment, (Polyline, Polygon)):
                        points = [transform(p) for p in segment.points]
                        if isinstance(segment, Polygon): points.append(points[0])
                        msp.add_lwpolyline(points)
                count += 1

        doc.saveas(dxf_path)
        print(f"DXF sauvegardé : {dxf_path}")
        print(f"Stats : {count} convertis, {skipped_len} trop petits, {skipped_thick} trop fins.")

    except Exception as e:
        print(f"Erreur DXF : {e}")
        sys.exit(1)

def dxf_to_dwg(dxf_path):
    """Convertit DXF -> DWG via ODA File Converter."""
    if not ODA_EXE:
        print("NOTE : ODA File Converter non trouvé. Pas de conversion DWG.")
        print("Télécharger : https://www.opendesign.com/guestfiles/oda_file_converter")
        return

    print("Conversion DXF vers DWG (ODA)...")
    
    input_dir = os.path.dirname(dxf_path)
    output_dir = input_dir 
    
    temp_oda_in = os.path.join(input_dir, "temp_oda_in")
    if not os.path.exists(temp_oda_in): os.makedirs(temp_oda_in)
    
    temp_dxf = os.path.join(temp_oda_in, os.path.basename(dxf_path))
    shutil.copy(dxf_path, temp_dxf)
    
    cmd = [ODA_EXE, temp_oda_in, output_dir, "ACAD2018", "DWG", "0", "0"]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        dwg_name = os.path.splitext(os.path.basename(dxf_path))[0] + ".dwg"
        dwg_path = os.path.join(output_dir, dwg_name)
        
        if os.path.exists(dwg_path):
            print(f"DWG généré avec succès : {dwg_path}")
        else:
            print("Erreur : Le fichier DWG n'a pas été créé par ODA.")
            
    except Exception as e:
        print(f"Erreur conversion DWG : {e}")
    finally:
        if os.path.exists(temp_oda_in):
            shutil.rmtree(temp_oda_in)

def main():
    parser = argparse.ArgumentParser(description="Convertisseur Image vers DXF/DWG v9 (AI & Gemini)")
    parser.add_argument("input_image", help="Image source")
    parser.add_argument("--keep-temp", action="store_true", help="Garder fichiers temp")
    parser.add_argument("--clean", action="store_true", help="Active les filtres de nettoyage")
    parser.add_argument("--hq", action="store_true", help="Mode Haute Qualité (Upscaling x2 + Adaptatif)")
    parser.add_argument("--ai", action="store_true", help="Mode AI (Rembg) pour supprimer le fond")
    parser.add_argument("--gemini", action="store_true", help="Utilise Gemini API pour générer le SVG (Nécessite .env)")
    
    parser.add_argument("--min-area", type=int, default=20, help="OpenCV: Aire min (px)")
    parser.add_argument("--max-thickness", type=float, default=0, help="SVG: Épaisseur max lignes")
    parser.add_argument("--min-len", type=float, default=0, help="SVG: Longueur min traits")
    
    args = parser.parse_args()
    
    min_area = args.min_area
    max_thickness = args.max_thickness
    min_len = args.min_len

    if args.clean:
        if min_area == 20: min_area = 50
        if max_thickness == 0: max_thickness = 5.0
        if min_len == 0: min_len = 10.0
        print(f"Mode CLEAN : min-area={min_area}, max-thickness={max_thickness}, min-len={min_len}")
    
    if args.hq:
        print("Mode HQ activé : Upscaling x2, Seuillage Adaptatif, Potrace précis.")
        
    if args.ai:
        print("Mode AI activé : Nettoyage via Rembg (U2-Net).")

    if args.gemini:
        print("Mode GEMINI activé : Génération SVG via API.")

    input_path = os.path.abspath(args.input_image)
    if not os.path.exists(input_path):
        print(f"Fichier introuvable : {input_path}")
        sys.exit(1)

    base_name = os.path.splitext(input_path)[0]
    bmp_path = base_name + ".bmp"
    svg_path = base_name + ".svg"
    dxf_path = base_name + ".dxf"

    check_dependencies()
    
    # Pipeline
    if args.gemini:
        # Pipeline Gemini : Image -> Gemini -> SVG -> DXF
        success = generate_svg_gemini(input_path, svg_path)
        if not success:
            print("Échec Gemini. Arrêt.")
            sys.exit(1)
        # Pas de HQ mode pour Gemini, l'échelle dépend du viewBox généré
        svg_to_dxf(svg_path, dxf_path, min_length=0, max_thickness=0, hq_mode=False)
    else:
        # Pipeline Classique : Image -> [Rembg] -> [OpenCV] -> Potrace -> SVG -> DXF
        clean_image_opencv(input_path, bmp_path, min_area=min_area, hq_mode=args.hq, ai_mode=args.ai)
        run_potrace(bmp_path, svg_path, turdsize=2, hq_mode=args.hq)
        svg_to_dxf(svg_path, dxf_path, min_length=min_len, max_thickness=max_thickness, hq_mode=args.hq)
    
    # Etape Finale : DWG
    dxf_to_dwg(dxf_path)

    if not args.keep_temp:
        if os.path.exists(bmp_path): os.remove(bmp_path)
        if os.path.exists(svg_path): os.remove(svg_path)

    print("-" * 30)
    print("TERMINÉ")

if __name__ == "__main__":
    main()

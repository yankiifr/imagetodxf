#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de conversion d'image (JPG/PNG) vers DXF/DWG pour CAO - v10

Dépendances Python :
    pip install -r requirements.txt

Dépendances Système :
    - Potrace (inclus dans potrace-1.16.win64/)
    - ODA File Converter (Optionnel) : https://www.opendesign.com/guestfiles/oda_file_converter
"""

import sys
import os
import subprocess
import argparse
import shutil
import json
import glob
from pathlib import Path as FilePath
from PIL import Image
import ezdxf
from svgelements import SVG, Path, Line, Polyline, Polygon, QuadraticBezier, CubicBezier, Move

# Fix pour Windows : forcer l'encodage UTF-8 pour les émojis
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Chargement des variables d'environnement (.env)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Tentatives d'import
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POTRACE_PATH = os.path.join(SCRIPT_DIR, "potrace-1.16.win64")
if os.path.exists(POTRACE_PATH):
    os.environ["PATH"] += os.pathsep + POTRACE_PATH

ODA_PATHS = [
    r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe",
    r"C:\Program Files (x86)\ODA\ODAFileConverter\ODAFileConverter.exe"
]
ODA_EXE = None
for p in ODA_PATHS:
    if os.path.exists(p):
        ODA_EXE = p
        break

def load_config():
    """Charge la configuration depuis config.json."""
    config_path = os.path.join(SCRIPT_DIR, "config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"presets": {}}

def check_dependencies():
    """Vérifie les dépendances système."""
    try:
        subprocess.run(["potrace", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except FileNotFoundError:
        print("ERREUR CRITIQUE : 'potrace' n'est pas trouvé.")
        print("Vérifiez que le dossier 'potrace-1.16.win64' est présent.")
        sys.exit(1)
    
    if ODA_EXE:
        print(f"✓ ODA File Converter détecté")
    else:
        print("⚠ ODA File Converter non détecté (pas de conversion DWG)")

def clean_image_ai(input_path, output_path):
    """Utilise Rembg pour supprimer le fond."""
    if not REMBG_AVAILABLE:
        print("ERREUR : 'rembg' non installé. pip install rembg")
        return False
    
    print("  [AI] Suppression du fond...")
    try:
        with open(input_path, 'rb') as i:
            output_data = remove(i.read())
        
        temp_png = output_path + ".rembg.png"
        with open(temp_png, 'wb') as o:
            o.write(output_data)
        
        with Image.open(temp_png) as img:
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            background.save(output_path)
        
        if os.path.exists(temp_png):
            os.remove(temp_png)
        return True
    except Exception as e:
        print(f"  [AI] Erreur : {e}")
        return False

def clean_image_opencv(input_path, output_bmp_path, min_area=50, hq_mode=False, ai_mode=False):
    """Nettoyage OpenCV."""
    processed_input = input_path
    if ai_mode:
        ai_output = input_path + ".ai.jpg"
        if clean_image_ai(input_path, ai_output):
            processed_input = ai_output
        else:
            print("  → Fallback nettoyage standard")

    if not OPENCV_AVAILABLE:
        print("  [PIL] Conversion simple...")
        preprocess_image_pil(processed_input, output_bmp_path)
        return

    print(f"  [OpenCV] min_area={min_area}, HQ={hq_mode}")
    img = cv2.imread(processed_input, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"  ERREUR : Impossible de lire {processed_input}")
        sys.exit(1)

    if hq_mode:
        print("  [HQ] Upscaling x2...")
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        min_area = min_area * 4

    if hq_mode:
        print("  [HQ] Seuillage Adaptatif...")
        binary = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY_INV, 11, 2)
    else:
        _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    new_binary = np.zeros_like(binary)

    removed = 0
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            new_binary[labels == i] = 255
        else:
            removed += 1

    print(f"  [OpenCV] Supprimés : {removed} composants")
    cv2.imwrite(output_bmp_path, cv2.bitwise_not(new_binary))
    
    if ai_mode and os.path.exists(processed_input) and processed_input != input_path:
        os.remove(processed_input)

def preprocess_image_pil(input_path, output_bmp_path):
    """Conversion simple PIL."""
    with Image.open(input_path) as img:
        gray = img.convert("L")
        bw = gray.point(lambda x: 0 if x < 128 else 255, '1')
        bw.save(output_bmp_path, "BMP")

def run_potrace(bmp_path, svg_path, turdsize=2, hq_mode=False):
    """Vectorisation Potrace."""
    print(f"  [Potrace] Vectorisation...")
    cmd = ["potrace", bmp_path, "-s", "-o", svg_path, "-t", str(turdsize)]
    if hq_mode:
        cmd.extend(["--opttolerance", "0.1", "--alphamax", "1.2"])
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def generate_svg_gemini(input_path, svg_path):
    """Génère SVG via Gemini API."""
    if not GEMINI_AVAILABLE:
        print("ERREUR : 'google-generativeai' non installé")
        return False
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERREUR : GEMINI_API_KEY manquante dans .env")
        return False

    print("  [Gemini] Génération SVG...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        img = Image.open(input_path)

        prompt_file = os.path.join(SCRIPT_DIR, "gemini_prompt.txt")
        if os.path.exists(prompt_file):
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt = f.read()
        else:
            prompt = "You are an expert CAD drafter. Generate clean SVG of walls only. No markdown."

        response = model.generate_content([prompt, img])
        content = response.text.replace("```svg", "").replace("```", "").strip()
        
        start = content.find("<svg")
        end = content.find("</svg>") + 6
        svg_code = content[start:end] if start != -1 and end != -1 else content

        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_code)
        return True
    except Exception as e:
        print(f"  [Gemini] Erreur : {e}")
        return False

def svg_to_dxf(svg_path, dxf_path, min_length=0, max_thickness=0, hq_mode=False):
    """Conversion SVG → DXF."""
    print("  [DXF] Conversion...")
    try:
        svg = SVG.parse(svg_path)
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        height = svg.height if svg.height else 1000
        scale_factor = 0.5 if hq_mode else 1.0
        
        # Optimisation : définir transform une seule fois
        def transform(p):
            return (p.x * scale_factor, (height - p.y) * scale_factor)

        count = 0
        skipped = 0

        for element in svg.elements():
            try:
                if not isinstance(element, Path):
                    element = Path(element)
            except:
                continue

            if isinstance(element, Path):
                try:
                    if min_length > 0 and element.length() < min_length:
                        skipped += 1
                        continue

                    if max_thickness > 0:
                        bbox = element.bbox()
                        if bbox:
                            thickness = min(bbox[2] - bbox[0], bbox[3] - bbox[1])
                            length = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
                            if thickness < (max_thickness * 2 if hq_mode else max_thickness) and length / (thickness or 1) > 5:
                                skipped += 1
                                continue
                except:
                    pass

                for segment in element:
                    if isinstance(segment, Move):
                        continue
                    
                    if isinstance(segment, Line):
                        msp.add_line(transform(segment.start), transform(segment.end))
                    elif isinstance(segment, QuadraticBezier):
                        msp.add_spline([transform(segment.start), transform(segment.control), transform(segment.end)], degree=2)
                    elif isinstance(segment, CubicBezier):
                        msp.add_spline([transform(segment.start), transform(segment.control1), transform(segment.control2), transform(segment.end)], degree=3)
                count += 1

        doc.saveas(dxf_path)
        print(f"  [DXF] {count} éléments, {skipped} filtrés")
    except Exception as e:
        print(f"  [DXF] Erreur : {e}")
        sys.exit(1)

def dxf_to_dwg(dxf_path):
    """Convertit DXF → DWG."""
    if not ODA_EXE:
        return

    print("  [DWG] Conversion...")
    input_dir = os.path.dirname(dxf_path)
    temp_oda = os.path.join(input_dir, "temp_oda_in")
    os.makedirs(temp_oda, exist_ok=True)
    
    shutil.copy(dxf_path, os.path.join(temp_oda, os.path.basename(dxf_path)))
    
    cmd = [ODA_EXE, temp_oda, input_dir, "ACAD2018", "DWG", "0", "0"]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        dwg_path = dxf_path.replace(".dxf", ".dwg")
        if os.path.exists(dwg_path):
            print(f"  [DWG] ✓ {os.path.basename(dwg_path)}")
    except:
        print("  [DWG] Échec conversion")
    finally:
        if os.path.exists(temp_oda):
            shutil.rmtree(temp_oda)

def process_single_file(input_path, args):
    """Traite un seul fichier."""
    print(f"\n{'='*60}")
    print(f"📄 Traitement : {os.path.basename(input_path)}")
    print(f"{'='*60}")
    
    if not os.path.exists(input_path):
        print(f"  ✗ Fichier introuvable")
        return False

    # Déterminer le dossier de sortie
    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        base_name = os.path.join(args.output_dir, os.path.splitext(os.path.basename(input_path))[0])
    else:
        base_name = os.path.splitext(input_path)[0]

    bmp_path = base_name + ".bmp"
    svg_path = base_name + ".svg"
    dxf_path = base_name + ".dxf"

    try:
        if args.gemini:
            if not generate_svg_gemini(input_path, svg_path):
                return False
            svg_to_dxf(svg_path, dxf_path, 0, 0, False)
        else:
            clean_image_opencv(input_path, bmp_path, args.min_area, args.hq, args.ai)
            run_potrace(bmp_path, svg_path, 2, args.hq)
            svg_to_dxf(svg_path, dxf_path, args.min_len, args.max_thickness, args.hq)
        
        dxf_to_dwg(dxf_path)

        if not args.keep_temp:
            for temp in [bmp_path, svg_path]:
                if os.path.exists(temp):
                    os.remove(temp)

        print(f"  ✓ DXF généré : {os.path.basename(dxf_path)}")
        return True
    except Exception as e:
        print(f"  ✗ Erreur : {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Convertisseur Image → DXF/DWG v10",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python convert_plan.py plan.jpg --clean --hq
  python convert_plan.py *.jpg --batch --preset scan
  python convert_plan.py photo.jpg --preset photo --output-dir ./output
        """
    )
    
    parser.add_argument("input_image", nargs='+', help="Image(s) source")
    parser.add_argument("--batch", action="store_true", help="Mode multi-fichiers")
    parser.add_argument("--preset", choices=['scan', 'photo', 'drawing'], help="Profil prédéfini")
    parser.add_argument("--output-dir", help="Dossier de sortie")
    parser.add_argument("--keep-temp", action="store_true", help="Garder fichiers temporaires")
    
    parser.add_argument("--clean", action="store_true", help="Filtres de nettoyage")
    parser.add_argument("--hq", action="store_true", help="Haute Qualité (x2 upscale)")
    parser.add_argument("--ai", action="store_true", help="Nettoyage IA (Rembg)")
    parser.add_argument("--gemini", action="store_true", help="Génération Gemini (Exp.)")
    
    parser.add_argument("--min-area", type=int, default=20)
    parser.add_argument("--max-thickness", type=float, default=0)
    parser.add_argument("--min-len", type=float, default=0)
    
    args = parser.parse_args()
    
    # Charger la config
    config = load_config()
    
    # Appliquer le preset si défini
    if args.preset and args.preset in config.get('presets', {}):
        preset = config['presets'][args.preset]
        print(f"📋 Profil: {args.preset} - {preset.get('description', '')}")
        args.clean = preset.get('clean', args.clean)
        args.hq = preset.get('hq', args.hq)
        args.ai = preset.get('ai', args.ai)
        args.min_area = preset.get('min_area', args.min_area)
        args.max_thickness = preset.get('max_thickness', args.max_thickness)
        args.min_len = preset.get('min_len', args.min_len)
    
    # Ajuster valeurs par défaut si --clean
    if args.clean:
        if args.min_area == 20: args.min_area = 50
        if args.max_thickness == 0: args.max_thickness = 5.0
        if args.min_len == 0: args.min_len = 10.0
    
    # Afficher config
    print(f"\n🔧 Configuration:")
    if args.clean: print(f"  ✓ Nettoyage (area={args.min_area}, thick={args.max_thickness})")
    if args.hq: print(f"  ✓ Haute Qualité (upscaling x2)")
    if args.ai: print(f"  ✓ IA (Rembg)")
    if args.gemini: print(f"  ✓ Gemini API")
    
    check_dependencies()
    
    # Traiter les fichiers
    files_to_process = []
    for pattern in args.input_image:
        if '*' in pattern or '?' in pattern:
            files_to_process.extend(glob.glob(pattern))
        else:
            files_to_process.append(pattern)
    
    if not files_to_process:
        print("Aucun fichier à traiter")
        sys.exit(1)
    
    if len(files_to_process) > 1 and not args.batch:
        print(f"⚠ {len(files_to_process)} fichiers détectés. Ajoutez --batch pour traiter tous.")
        files_to_process = [files_to_process[0]]
    
    # Traitement
    successes = 0
    failures = 0
    
    for file_path in files_to_process:
        if process_single_file(file_path, args):
            successes += 1
        else:
            failures += 1
    
    # Résumé
    print(f"\n{'='*60}")
    print(f"✅ Réussis : {successes}")
    if failures > 0:
        print(f"❌ Échecs : {failures}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()

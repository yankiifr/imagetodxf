#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI Tkinter pour Image to DXF/DWG Converter v10
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import subprocess
import threading
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class ConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Image to DXF/DWG Converter v10")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        # Charger config
        self.load_config()
        
        # Variables
        self.files = []
        self.processing = False
        
        # UI
        self.create_widgets()
        
    def load_config(self):
        """Charge config.json."""
        config_path = os.path.join(SCRIPT_DIR, "config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {"presets": {}}
    
    def create_widgets(self):
        """Crée l'interface."""
        # Header
        header = tk.Frame(self.root, bg="#2c3e50", height=80)
        header.pack(fill=tk.X)
        
        title = tk.Label(header, text="📐 Image to DXF/DWG", 
                        font=("Arial", 20, "bold"), bg="#2c3e50", fg="white")
        title.pack(pady=20)
        
        # Main container
        main = tk.Frame(self.root, bg="#ecf0f1")
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Drop zone
        drop_frame = tk.LabelFrame(main, text="📁 Fichiers à Convertir", 
                                   font=("Arial", 12, "bold"), bg="#ecf0f1")
        drop_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.file_listbox = tk.Listbox(drop_frame, height=8, font=("Consolas", 10),
                                       selectmode=tk.EXTENDED, bg="white")
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Drag & Drop
        try:
            self.file_listbox.drop_target_register(DND_FILES)
            self.file_listbox.dnd_bind('<<Drop>>', self.on_drop)
        except:
            pass  # TkinterDnD2 pas installé
        
        # Boutons fichiers
        btn_frame = tk.Frame(drop_frame, bg="#ecf0f1")
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Button(btn_frame, text="➕ Ajouter", command=self.add_files,
                 bg="#3498db", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Supprimer", command=self.remove_files,
                 bg="#e74c3c", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🧹 Vider", command=self.clear_files,
                 bg="#95a5a6", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        # Options
        opt_frame = tk.LabelFrame(main, text="⚙️ Options de Conversion", 
                                 font=("Arial", 12, "bold"), bg="#ecf0f1")
        opt_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Profils
        profile_frame = tk.Frame(opt_frame, bg="#ecf0f1")
        profile_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(profile_frame, text="Profil:", font=("Arial", 10), bg="#ecf0f1").pack(side=tk.LEFT)
        
        self.profile_var = tk.StringVar(value="Personnalisé")
        profiles = ["Personnalisé"] + list(self.config.get("presets", {}).keys())
        profile_combo = ttk.Combobox(profile_frame, textvariable=self.profile_var, 
                                    values=profiles, state="readonly", width=15)
        profile_combo.pack(side=tk.LEFT, padx=10)
        profile_combo.bind("<<ComboboxSelected>>", self.on_profile_change)
        
        # Checkboxes
        check_frame = tk.Frame(opt_frame, bg="#ecf0f1")
        check_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.clean_var = tk.BooleanVar(value=True)
        self.hq_var = tk.BooleanVar(value=True)
        self.ai_var = tk.BooleanVar(value=False)
        self.batch_var = tk.BooleanVar(value=True)
        
        tk.Checkbutton(check_frame, text="🧹 Clean", variable=self.clean_var, 
                      font=("Arial", 10), bg="#ecf0f1").pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(check_frame, text="🔍 HQ", variable=self.hq_var,
                      font=("Arial", 10), bg="#ecf0f1").pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(check_frame, text="🤖 AI", variable=self.ai_var,
                      font=("Arial", 10), bg="#ecf0f1").pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(check_frame, text="📦 Batch", variable=self.batch_var,
                      font=("Arial", 10), bg="#ecf0f1").pack(side=tk.LEFT, padx=10)
        
        # Paramètres avancés
        adv_frame = tk.Frame(opt_frame, bg="#ecf0f1")
        adv_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tk.Label(adv_frame, text="Min Area:", font=("Arial", 9), bg="#ecf0f1").grid(row=0, column=0, sticky=tk.W)
        self.min_area_var = tk.StringVar(value="100")
        tk.Entry(adv_frame, textvariable=self.min_area_var, width=8).grid(row=0, column=1, padx=5)
        
        tk.Label(adv_frame, text="Max Thick:", font=("Arial", 9), bg="#ecf0f1").grid(row=0, column=2, sticky=tk.W, padx=(15, 0))
        self.max_thick_var = tk.StringVar(value="8")
        tk.Entry(adv_frame, textvariable=self.max_thick_var, width=8).grid(row=0, column=3, padx=5)
        
        # Bouton de conversion
        convert_btn = tk.Button(main, text="🚀 CONVERTIR", command=self.start_conversion,
                               bg="#27ae60", fg="white", font=("Arial", 14, "bold"), height=2)
        convert_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Progress
        self.progress = ttk.Progressbar(main, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 10))
        
        # Log
        log_frame = tk.LabelFrame(main, text="📋 Journal", font=("Arial", 10, "bold"), bg="#ecf0f1")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=6, font=("Consolas", 9), bg="#2c3e50", fg="#ecf0f1",
                               state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_label = tk.Label(self.root, text="Prêt", bg="#34495e", fg="white", 
                                     font=("Arial", 9), anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def on_drop(self, event):
        """Gère le drag & drop."""
        files = self.root.tk.splitlist(event.data)
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')) and file not in self.files:
                self.files.append(file)
                self.file_listbox.insert(tk.END, os.path.basename(file))
        self.update_status(f"{len(self.files)} fichier(s) chargé(s)")
    
    def add_files(self):
        """Ajoute des fichiers manuellement."""
        files = filedialog.askopenfilenames(
            title="Sélectionner des images",
            filetypes=[("Images", "*.jpg *.jpeg *.png"), ("Tous", "*.*")]
        )
        for file in files:
            if file not in self.files:
                self.files.append(file)
                self.file_listbox.insert(tk.END, os.path.basename(file))
        self.update_status(f"{len(self.files)} fichier(s) chargé(s)")
    
    def remove_files(self):
        """Supprime les fichiers sélectionnés."""
        selected = self.file_listbox.curselection()
        for idx in reversed(selected):
            self.file_listbox.delete(idx)
            del self.files[idx]
        self.update_status(f"{len(self.files)} fichier(s) restant(s)")
    
    def clear_files(self):
        """Vide la liste."""
        self.file_listbox.delete(0, tk.END)
        self.files = []
        self.update_status("Liste vidée")
    
    def on_profile_change(self, event):
        """Change les valeurs selon le profil."""
        profile_name = self.profile_var.get()
        if profile_name == "Personnalisé":
            return
        
        preset = self.config.get("presets", {}).get(profile_name, {})
        self.clean_var.set(preset.get("clean", False))
        self.hq_var.set(preset.get("hq", False))
        self.ai_var.set(preset.get("ai", False))
        self.min_area_var.set(str(preset.get("min_area", 20)))
        self.max_thick_var.set(str(preset.get("max_thickness", 0)))
        self.log(f" Profil '{profile_name}' appliqué")
    
    def update_status(self, text):
        """Met à jour la barre de statut."""
        self.status_label.config(text=text)
    
    def log(self, message):
        """Ajoute un message au journal."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def start_conversion(self):
        """Lance la conversion."""
        if not self.files:
            messagebox.showwarning("Aucun fichier", "Ajoutez au moins un fichier à convertir.")
            return
        
        if self.processing:
            messagebox.showinfo("En cours", "Une conversion est déjà en cours.")
            return
        
        self.processing = True
        self.progress.start()
        self.update_status("Conversion en cours...")
        
        # Lancer dans un thread
        thread = threading.Thread(target=self.convert_files)
        thread.daemon = True
        thread.start()
    
    def convert_files(self):
        """Exécute la conversion."""
        script_path = os.path.join(SCRIPT_DIR, "convert_plan_v10.py")
        
        # Construire la commande
        cmd = ["python", script_path]
        
        # Ajouter les fichiers
        cmd.extend(self.files)
        
        # Options
        if self.batch_var.get():
            cmd.append("--batch")
        if self.clean_var.get():
            cmd.append("--clean")
        if self.hq_var.get():
            cmd.append("--hq")
        if self.ai_var.get():
            cmd.append("--ai")
        
        # Paramètres avancés
        try:
            min_area = int(self.min_area_var.get())
            cmd.extend(["--min-area", str(min_area)])
        except:
            cmd.extend(["--min-area", "100"])
        
        try:
            max_thick = float(self.max_thick_var.get())
            cmd.extend(["--max-thickness", str(max_thick)])
        except:
            cmd.extend(["--max-thickness", "8"])
        
        self.log(f"🚀 Commande : {' '.join(cmd[2:])}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=SCRIPT_DIR)
            
            # Afficher la sortie
            for line in result.stdout.split('\n'):
                if line.strip():
                    self.log(line)
            
            if result.returncode == 0:
                self.log("✅ Conversion terminée avec succès !")
                self.root.after(0, lambda: messagebox.showinfo("Succès", "Conversion terminée !"))
            else:
                error_msg = result.stderr if result.stderr else "Erreur inconnue"
                self.log(f"❌ Erreur : {error_msg}")
                self.root.after(0, lambda: messagebox.showerror("Erreur", error_msg[:500]))
        
        except Exception as e:
            self.log(f"❌ Exception : {e}")
            self.root.after(0, lambda: messagebox.showerror("Erreur", str(e)))
        
        finally:
            self.processing = False
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.update_status("Prêt"))

def main():
    try:
        root = TkinterDnD.Tk()
    except:
        # Fallback si TkinterDnD2 pas installé
        root = tk.Tk()
        print("⚠ TkinterDnD2 non installé. Drag & Drop désactivé.")
        print("  Install: pip install tkinterdnd2")
    
    app = ConverterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

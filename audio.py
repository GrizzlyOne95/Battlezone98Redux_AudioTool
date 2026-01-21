import os
import sys
import csv
import subprocess
import threading
import soundfile as sf
import customtkinter as ctk
from tkinter import filedialog, messagebox

# --- UTILITY FUNCTIONS ---
def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if getattr(sys, 'frozen', False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Resource Constants
FFMPEG_EXE = get_resource_path("ffmpeg.exe")
COMM_BEEP = get_resource_path("commbeep.wav")
UNIT_BEEP = get_resource_path("unitbeep.wav")

class BZRadio(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- WINDOW CONFIGURATION ---
        self.title("BZRadio - Battlezone 98 Redux Audio Tool")
        self.geometry("750x1100")
        self.custom_beep_path = None
        
        # Set the window icon (BZRadio branding)
        try:
            self.iconpath = get_resource_path("bzradio.ico")
            self.wm_iconbitmap(self.iconpath)
        except:
            pass 

        # --- HEADER SECTION ---
        self.header = ctk.CTkLabel(self, text="BZRadio", font=("Courier", 42, "bold"))
        self.header.pack(pady=(20, 5))
        self.sub = ctk.CTkLabel(self, text="Audio Architect for BZ98 Redux", font=("Arial", 13, "italic"))
        self.sub.pack(pady=(0, 15))

        # --- PROGRESS & STATUS ---
        self.prog_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.prog_frame.pack(pady=10, padx=20, fill="x")
        
        self.prog_label = ctk.CTkLabel(self.prog_frame, text="Ready to process", font=("Arial", 12))
        self.prog_label.pack()
        
        self.progress_bar = ctk.CTkProgressBar(self.prog_frame, width=600)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)

        # --- SELECTION MODE ---
        self.mode_frame = ctk.CTkFrame(self)
        self.mode_frame.pack(pady=5, padx=20, fill="x")
        self.process_mode = ctk.StringVar(value="batch")
        ctk.CTkRadioButton(self.mode_frame, text="Batch Folder", variable=self.process_mode, value="batch").grid(row=0, column=0, padx=60, pady=10)
        ctk.CTkRadioButton(self.mode_frame, text="Single File", variable=self.process_mode, value="single").grid(row=0, column=1, padx=60, pady=10)

        # --- GLOBAL SETTINGS ---
        self.global_frame = ctk.CTkFrame(self)
        self.global_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(self.global_frame, text="Privacy & Security", font=("Arial", 14, "bold")).pack(pady=5)
        
        self.strip_metadata_var = ctk.BooleanVar(value=True)
        self.strip_metadata_cb = ctk.CTkCheckBox(
            self.global_frame, 
            text="Strip all metadata & Artwork (Full PII Scrub)", 
            variable=self.strip_metadata_var
        )
        self.strip_metadata_cb.pack(pady=10)

        # --- RADIO TRANSMISSION SETTINGS (WAV) ---
        self.radio_frame = ctk.CTkFrame(self)
        self.radio_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(self.radio_frame, text="WAV: Unit VO & Radio Effects", font=("Arial", 16, "bold"), text_color="#d97706").pack(pady=5)
        
        self.fx_frame = ctk.CTkFrame(self.radio_frame, fg_color="transparent")
        self.fx_frame.pack(pady=5)

        self.phaser_var = ctk.BooleanVar(value=False)
        self.phaser_cb = ctk.CTkCheckBox(self.fx_frame, text="Phaser", variable=self.phaser_var)
        self.phaser_cb.grid(row=0, column=0, padx=10)

        self.echo_var = ctk.BooleanVar(value=False)
        self.echo_cb = ctk.CTkCheckBox(self.fx_frame, text="Doubling/Echo", variable=self.echo_var)
        self.echo_cb.grid(row=0, column=1, padx=10)

        # --- NEW: Echo Delay Slider ---
        self.echo_delay_var = ctk.DoubleVar(value=40) # Default to 40ms
        self.echo_slider = ctk.CTkSlider(
            self.radio_frame, 
            from_=10, 
            to=100, 
            variable=self.echo_delay_var,
            number_of_steps=18, # Increments of 5ms
            width=200
        )
        self.echo_slider.pack(pady=(0, 10))

        self.echo_label = ctk.CTkLabel(self.radio_frame, text="Echo Delay: 40ms", font=("Arial", 10))
        self.echo_label.pack()

        # Update label when slider moves
        self.echo_slider.configure(command=lambda v: self.echo_label.configure(text=f"Echo Delay: {int(v)}ms"))
        
        ctk.CTkLabel(self.radio_frame, text="Intro/Outro Squelch Tone:", font=("Arial", 12, "bold")).pack()
        self.beep_var = ctk.StringVar(value="commbeep.wav (Radio/Orders)")
        self.beep_dropdown = ctk.CTkComboBox(self.radio_frame, values=["commbeep.wav (Radio/Orders)", "unitbeep.wav (Unit Responses)", "Custom...", "None"], variable=self.beep_var, width=350, command=self.check_custom_beep)
        self.beep_dropdown.pack(pady=5)
        
        ctk.CTkLabel(self.radio_frame, text="Radio Effect Intensity:", font=("Arial", 12, "bold")).pack()
        self.intensity_var = ctk.StringVar(value="medium")
        self.intensity_dropdown = ctk.CTkComboBox(self.radio_frame, values=["none", "light", "medium", "heavy"], variable=self.intensity_var, width=200)
        self.intensity_dropdown.pack(pady=5)

        self.btn_radio = ctk.CTkButton(self, text="PROCESS WAV (Game Audio)", command=lambda: self.start_thread("wav"), fg_color="#d97706", hover_color="#b45309", height=50, font=("Arial", 14, "bold"))
        self.btn_radio.pack(pady=15)

        # --- MUSIC SETTINGS (OGG) ---
        self.btn_ogg = ctk.CTkButton(self, text="PROCESS OGG (Clean Music)", command=lambda: self.start_thread("ogg"), fg_color="#1f538d", hover_color="#163a63", height=50, font=("Arial", 14, "bold"))
        self.btn_ogg.pack(pady=5)

        # --- UTILITIES ---
        self.btn_csv = ctk.CTkButton(self, text="Export CSV Timing Manifest", command=self.export_csv, fg_color="#2b7a3e", hover_color="#1e562c")
        self.btn_csv.pack(pady=20)

        # --- CONSOLE LOG ---
        self.console = ctk.CTkTextbox(self, width=680, height=180, font=("Consolas", 11))
        self.console.pack(pady=10, padx=20)

    # --- LOGIC METHODS ---

    def log(self, text):
        self.console.insert("end", text + "\n")
        self.console.see("end")

    def check_custom_beep(self, choice):
        if choice == "Custom...":
            path = filedialog.askopenfilename(title="Select Custom Beep WAV", filetypes=[("WAV files", "*.wav")])
            if path:
                self.custom_beep_path = path
                self.log(f"Custom beep loaded: {os.path.basename(path)}")
            else:
                self.beep_var.set("None")

    def get_input_list(self):
        if self.process_mode.get() == "single":
            path = filedialog.askopenfilename(title="Select Audio File", filetypes=[("Audio Files", "*.wav *.mp3 *.m4a *.ogg")])
            return [path] if path else []
        folder = filedialog.askdirectory(title="Select Input Folder")
        return [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(('.wav', '.mp3', '.m4a', '.ogg'))] if folder else []

    def start_thread(self, mode):
        files = self.get_input_list()
        if not files: return
        
        # Disable buttons to prevent double-processing
        self.btn_radio.configure(state="disabled")
        self.btn_ogg.configure(state="disabled")
        
        threading.Thread(target=self.process_logic, args=(files, mode), daemon=True).start()

    def process_logic(self, files, mode):
        total = len(files)
        out_subdir = "bz98_radio_export" if mode == "wav" else "bz98_music_export"
        out_dir = os.path.join(os.path.dirname(files[0]), out_subdir)
        os.makedirs(out_dir, exist_ok=True)
        
        # Metadata and Artwork scrubbing flags
        scrub_args = ['-map_metadata', '-1', '-vn'] if self.strip_metadata_var.get() else []

        for index, f in enumerate(files):
            # Update Progress Bar and Label
            self.progress_bar.set((index + 1) / total)
            self.prog_label.configure(text=f"Processing {index+1}/{total}: {os.path.basename(f)}")
            
            out_ext = ".wav" if mode == "wav" else ".ogg"
            out_f = os.path.join(out_dir, os.path.splitext(os.path.basename(f))[0] + out_ext)
            
        if mode == "wav":
            # --- 1. DEFINE BEEP FILENAMES ---
            intensity = self.intensity_var.get()
            choice = self.beep_var.get()
            beep = COMM_BEEP if "comm" in choice else \
                   UNIT_BEEP if "unit" in choice else \
                   self.custom_beep_path if choice == "Custom..." else None
            
            # --- 2. BUILD FILTER CHAIN ---
            if intensity == 'none':
                af_chain = "aresample=22050"
            else:
                hp, lp, comp = (300, 4000, "compand=.3|.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2") if intensity == 'light' else \
                               (700, 2500, "compand=.1|.1:1|1:-90/-60|-60/-30|-30/-20|-10/-10:12:0:-90:0.1") if intensity == 'heavy' else \
                               (500, 3000, "compand=.2|.2:1|1:-90/-60|-60/-40|-40/-20|-10/-10:8:0:-90:0.15")
                af_chain = f"aresample=22050,highpass=f={hp},lowpass=f={lp},volume=2.0,{comp}"

            # Add Phaser
            if self.phaser_var.get():
                af_chain += ",aphaser=in_gain=0.8:out_gain=0.9:delay=3.0:decay=0.4:speed=0.2:type=t"

            # Add Doubling / Reverb Echo
            if self.echo_var.get():
                # Get value from slider (converted to integer)
                delay_ms = int(self.echo_delay_var.get())
                
                # aecho parameters: [in_volume]:[out_volume]:[delay]:[decay]
                # We use the slider for the 'delay' parameter
                af_chain += f",aecho=0.8:0.9:{delay_ms}:0.3"

            # Add Tremolo (only if intensity isn't none)
            if intensity != 'none':
                af_chain += ",tremolo=d=0.05:f=30"

            # --- 3. CONSTRUCT COMMAND ---
            if beep:
                # Concat beep-voice-beep
                cmd = [FFMPEG_EXE, '-y', '-i', beep, '-i', f, '-i', beep, '-filter_complex', 
                       f"[0:a]aresample=22050,volume=0.3[b1]; [1:a]{af_chain}[m]; [2:a]aresample=22050,volume=0.3[b2]; [b1][m][b2]concat=n=3:v=0:a=1[out]",
                       '-map', '[out]'] + scrub_args + ['-c:a', 'pcm_u8', '-ar', '22050', '-ac', '1', out_f]
            else:
                # Voice only
                cmd = [FFMPEG_EXE, '-y', '-i', f, '-af', af_chain] + scrub_args + ['-c:a', 'pcm_u8', '-ar', '22050', '-ac', '1', out_f]
        
        else:
            # --- 4. OGG PROCESSING ---
            # Map strictly to audio stream to discard cover art
            cmd = [FFMPEG_EXE, '-y', '-i', f, '-map', '0:a'] + scrub_args + ['-c:a', 'libvorbis', '-q:a', '5', '-ar', '44100', out_f]

        # --- 5. EXECUTION ---
        subprocess.run(cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        self.log(f"Exported: {os.path.basename(out_f)}")

        # Final UI Reset
        self.prog_label.configure(text="Batch Complete!")
        self.btn_radio.configure(state="normal")
        self.btn_ogg.configure(state="normal")
        messagebox.showinfo("Success", f"Successfully processed {total} files.")

    def export_csv(self):
        folder = filedialog.askdirectory(title="Select folder containing converted audio")
        if not folder: return
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV File", "*.csv")], initialfile="audio_manifest.csv")
        if not save_path: return
        
        with open(save_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Filename", "Duration", "Type"])
            for file in os.listdir(folder):
                if file.lower().endswith(('.wav', '.ogg')):
                    try:
                        info = sf.info(os.path.join(folder, file))
                        writer.writerow([file, round(info.duration, 3), "OGG" if file.endswith(".ogg") else "WAV"])
                    except: continue
        self.log(f"Timing manifest saved to: {save_path}")

if __name__ == "__main__":
    app = BZRadio()
    app.mainloop()

import os
import sys
import csv
import subprocess
import soundfile as sf
import customtkinter as ctk
from tkinter import filedialog, messagebox

def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

FFMPEG_EXE = get_resource_path("ffmpeg.exe")
COMM_BEEP = get_resource_path("commbeep.wav")
UNIT_BEEP = get_resource_path("unitbeep.wav")

class BZRadio(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("BZRadio - Battlezone 98 Redux Audio Tool")
        self.geometry("750x1050")
        self.custom_beep_path = None
        
        try:
            self.iconpath = get_resource_path("bzradio.ico")
            self.wm_iconbitmap(self.iconpath)
        except:
            pass 

        # --- HEADER ---
        self.header = ctk.CTkLabel(self, text="BZRadio", font=("Courier", 36, "bold"))
        self.header.pack(pady=(20, 5))
        self.sub = ctk.CTkLabel(self, text="Audio Architect for BZ98 Redux", font=("Arial", 12, "italic"))
        self.sub.pack(pady=(0, 15))

        # --- SELECTION MODE ---
        self.mode_frame = ctk.CTkFrame(self)
        self.mode_frame.pack(pady=5, padx=20, fill="x")
        self.process_mode = ctk.StringVar(value="batch")
        ctk.CTkRadioButton(self.mode_frame, text="Batch Folder Process", variable=self.process_mode, value="batch").grid(row=0, column=0, padx=40, pady=10)
        ctk.CTkRadioButton(self.mode_frame, text="Single File Process", variable=self.process_mode, value="single").grid(row=0, column=1, padx=40, pady=10)

        # --- GLOBAL SETTINGS ---
        self.global_frame = ctk.CTkFrame(self)
        self.global_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(self.global_frame, text="Global Processing Options", font=("Arial", 14, "bold")).pack(pady=5)
        
        self.strip_metadata_var = ctk.BooleanVar(value=True)
        self.strip_metadata_cb = ctk.CTkCheckBox(self.global_frame, text="Strip all metadata (Remove Author, Title, ID3 tags, etc.)", variable=self.strip_metadata_var)
        self.strip_metadata_cb.pack(pady=10)

        # --- RADIO SETTINGS (WAV ONLY) ---
        self.radio_frame = ctk.CTkFrame(self)
        self.radio_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(self.radio_frame, text="Radio Transmission (VO) Settings", font=("Arial", 16, "bold"), text_color="#d97706").pack(pady=5)
        ctk.CTkLabel(self.radio_frame, text="Note: Effects only apply to WAV output.", font=("Arial", 11, "italic"), text_color="#aaaaaa").pack(pady=(0, 10))
        
        ctk.CTkLabel(self.radio_frame, text="Intro/Outro Beep Tone:", font=("Arial", 12, "bold")).pack()
        self.beep_var = ctk.StringVar(value="commbeep.wav (Radio/Orders)")
        self.beep_dropdown = ctk.CTkComboBox(self.radio_frame, values=["commbeep.wav (Radio/Orders)", "unitbeep.wav (Unit Responses)", "Custom...", "None"], variable=self.beep_var, width=350, command=self.check_custom_beep)
        self.beep_dropdown.pack(pady=5)
        
        ctk.CTkLabel(self.radio_frame, text="Radio Effect Intensity:", font=("Arial", 12, "bold")).pack()
        self.intensity_var = ctk.StringVar(value="medium")
        # Added "none" to values
        self.intensity_dropdown = ctk.CTkComboBox(self.radio_frame, values=["none", "light", "medium", "heavy"], variable=self.intensity_var, width=200)
        self.intensity_dropdown.pack(pady=5)

        self.btn_radio = ctk.CTkButton(self, text="PROCESS WAV: Convert to 8-Bit (Game Audio)", command=self.handle_radio_request, fg_color="#d97706", hover_color="#b45309", height=50, font=("Arial", 14, "bold"))
        self.btn_radio.pack(pady=15)

        # --- SEPARATOR ---
        line = ctk.CTkFrame(self, height=2, fg_color="#444444")
        line.pack(fill="x", padx=40, pady=10)

        # --- MUSIC SETTINGS (OGG ONLY) ---
        ctk.CTkLabel(self, text="Music Soundtrack (OGG) Settings", font=("Arial", 16, "bold"), text_color="#1f538d").pack(pady=5)
        ctk.CTkLabel(self, text="Converts to high-fidelity stereo OGG. No radio effects applied.", font=("Arial", 11, "italic"), text_color="#aaaaaa").pack(pady=(0, 10))

        self.btn_ogg = ctk.CTkButton(self, text="PROCESS OGG: Clean Stereo (Music)", command=self.handle_ogg_request, fg_color="#1f538d", hover_color="#163a63", height=50, font=("Arial", 14, "bold"))
        self.btn_ogg.pack(pady=5)

        # --- UTILS ---
        self.csv_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.csv_frame.pack(pady=20)
        self.btn_csv = ctk.CTkButton(self.csv_frame, text="Export CSV Timing Manifest", command=self.export_csv, fg_color="#2b7a3e", hover_color="#1e562c")
        self.btn_csv.pack()
        ctk.CTkLabel(self.csv_frame, text="Useful for Lua scripting to ensure subtitles/events line up.", font=("Arial", 10, "italic"), text_color="gray").pack()

        # --- CONSOLE ---
        self.console = ctk.CTkTextbox(self, width=680, height=200, font=("Consolas", 11))
        self.console.pack(pady=10, padx=20)

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

    def handle_radio_request(self):
        files = self.get_input_list()
        if not files: return
        out_dir = os.path.join(os.path.dirname(files[0]), "bz98_radio_export")
        os.makedirs(out_dir, exist_ok=True)
        
        intensity = self.intensity_var.get()
        meta_args = ['-map_metadata', '-1'] if self.strip_metadata_var.get() else []
        choice = self.beep_var.get()
        beep = COMM_BEEP if "comm" in choice else UNIT_BEEP if "unit" in choice else self.custom_beep_path if choice == "Custom..." else None

        for f in files:
            out_f = os.path.join(out_dir, os.path.splitext(os.path.basename(f))[0] + ".wav")
            
            # Build Audio Filter Chain
            if intensity == 'none':
                # No radio FX, just ensure 22.05kHz resampling
                af_chain = "aresample=22050"
            else:
                if intensity == 'light': hp, lp, comp = 300, 4000, "compand=.3|.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2"
                elif intensity == 'heavy': hp, lp, comp = 700, 2500, "compand=.1|.1:1|1:-90/-60|-60/-30|-30/-20|-10/-10:12:0:-90:0.1"
                else: hp, lp, comp = 500, 3000, "compand=.2|.2:1|1:-90/-60|-60/-40|-40/-20|-10/-10:8:0:-90:0.15"
                af_chain = f"aresample=22050,highpass=f={hp},lowpass=f={lp},volume=2.0,{comp},tremolo=d=0.05:f=30"

            if beep:
                # Note: Concatenation requires all streams to have the same filters applied if handled via filter_complex
                # To keep "none" clean, we just resample the main audio and combine with resampled beeps
                cmd = [FFMPEG_EXE, '-y', '-i', beep, '-i', f, '-i', beep, '-filter_complex', 
                       f"[0:a]aresample=22050,volume=0.3[b1]; [1:a]{af_chain}[m]; [2:a]aresample=22050,volume=0.3[b2]; [b1][m][b2]concat=n=3:v=0:a=1[out]",
                       '-map', '[out]'] + meta_args + ['-c:a', 'pcm_u8', '-ar', '22050', '-ac', '1', out_f]
            else:
                cmd = [FFMPEG_EXE, '-y', '-i', f, '-af', af_chain] + \
                       meta_args + ['-c:a', 'pcm_u8', '-ar', '22050', '-ac', '1', out_f]
            
            subprocess.run(cmd, capture_output=True)
            self.log(f"Exported WAV: {os.path.basename(out_f)}")

    def handle_ogg_request(self):
        files = self.get_input_list()
        if not files: return
        out_dir = os.path.join(os.path.dirname(files[0]), "bz98_music_export")
        os.makedirs(out_dir, exist_ok=True)
        meta_args = ['-map_metadata', '-1'] if self.strip_metadata_var.get() else []

        for f in files:
            out_f = os.path.join(out_dir, os.path.splitext(os.path.basename(f))[0] + ".ogg")
            cmd = [FFMPEG_EXE, '-y', '-i', f] + meta_args + ['-c:a', 'libvorbis', '-q:a', '5', '-ar', '44100', out_f]
            subprocess.run(cmd, capture_output=True)
            self.log(f"Exported OGG: {os.path.basename(out_f)}")

    def export_csv(self):
        folder = filedialog.askdirectory()
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
        self.log(f"Manifest saved.")

if __name__ == "__main__":
    app = BZRadio()
    app.mainloop()

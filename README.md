# BZRadio: Battlezone 98 Redux Audio Tool

**BZRadio** is a specialized utility designed for the **Battlezone 98 Redux** modding community. It streamlines the process of mastering audio for the legacy engine, handling the strict formatting requirements for both unit voiceovers (VO) and mission soundtracks.



## Features

- **Radio VO Mastering:** Automatically applies high-pass/low-pass filtering, compression, and tremolo to simulate authentic analog radio transmissions. Can be disabled.
- **Intro/Outro Beeps:** Automatically appends "squelch" tones to the start and end of transmissions. Supports `commbeep.wav` (orders), `unitbeep.wav` (responses), or custom user files. Can be disabled.
- **WAV Profiles:** Supports both **Radio VO** export (`22050Hz` mono `PCM_U8`) and a dedicated **Thrust/Turbo Loop** export path (`11025Hz` mono `PCM_U8`, plain RIFF/WAVE).
- **Music Soundtrack Path:** Converts audio to high-fidelity **Stereo OGG** (44100Hz) without radio distortion, perfect for background music.
- **Metadata:** Can strip and remove all meta data and non-audio streams.
- **Lua Timing Manifest:** Exports a CSV of file durations—essential for scripters to perfectly time subtitles and mission events in Lua.
- **Batch & Single Mode:** Process an entire folder of source files or a single specific track with one click.

<img width="802" height="982" alt="image" src="https://github.com/user-attachments/assets/c1df73d5-a945-446c-8e8e-59c8cd4728f0" />




---

## Audio Specifications

| Target Type | Format | Sample Rate | Channels | Effects Applied |
| :--- | :--- | :--- | :--- | :--- |
| **Radio/Unit VO** | WAV (PCM_U8) | 22050 Hz | Mono | Bandpass, Tremolo, Beeps |
| **Thrust/Turbo Loops** | WAV (PCM_U8) | 11025 Hz | Mono | None, plain RIFF/WAVE rewrite |
| **Soundtrack** | OGG (Vorbis) | 44100 Hz | Stereo | None (Clean / Full Range) |

---

## Installation & Usage

### For Users (Standalone EXE)
1. Download the latest `BZRadio.exe` from the [Releases](../../releases) tab.
2. Launch the tool. 
3. **WAV Path:** Use for unit voices and radio chatter (Includes beeps and radio filters).
4. **OGG Path:** Use for mission music (Full quality, no filters).

### For Developers (Running from Source)
If you wish to run the script or build it yourself:
1. **Requirements:** Install dependencies:
   pip install -r requirements.txt
2. FFmpeg: Place a copy of ffmpeg.exe in the root directory.
3. Run: python audio.py
4. To generate the single-file executable with the custom icon and bundled assets, use the following command:
```Bash
python -m PyInstaller --noconsole --onefile \
--collect-all customtkinter \
--collect-all soundfile \
--icon="bzradio.ico" \
--add-data "bzradio.ico;." \
--add-data "commbeep.wav;." \
--add-data "unitbeep.wav;." \
--add-binary "ffmpeg.exe;." \
audio.py
```
## Credits & Licensing
Code: Licensed under the MIT License.

FFmpeg: This tool bundles FFmpeg binaries licensed under the LGPLv2.1.

Battlezone 98 Redux Assets: Default beep files (commbeep.wav, unitbeep.wav) are the property of Rebellion / Activision and are included for non-commercial fan-use specifically for the BZ98 modding community.

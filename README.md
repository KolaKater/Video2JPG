# Video2JPG

> **Free. No sign-up. No watermark.**
> Drag videos in, get JPG frames out.

Video2JPG is a small Windows desktop tool that extracts every frame from a video and saves the frames as JPG images. Drop one video, several videos, or a whole folder — pick a JPG quality from 60 to 95 — and hit **Start**.

[Version](https://img.shields.io/badge/version-V1.0%202026-blue)
[License](https://img.shields.io/badge/license-MIT-green)
[Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
[Python](https://img.shields.io/badge/python-3.x-yellow)

---

## ✨ Features

- **Drag & Drop** — drop video files or a video folder onto the file list (folders are scanned recursively)
- **Batch conversion** — convert many videos in one run
- **JPG quality 60–95** — slider, default `85`. Higher = better quality, bigger files. Mapped to FFmpeg `-q:v` (`95 → 2`, `60 → 12`)
- **Start / Suspend / Cancel** — Suspend really pauses the FFmpeg process (click again to Resume); Cancel stops the current job
- **30+ video formats** — `mp4, mkv, avi, mov, wmv, flv, webm, m4v, mpg, mpeg, ts, m2ts, mts, vob, 3gp, 3g2, rm, rmvb, asf, divx, f4v, m2v, ogv, ogm, mxf, dav, mod, tod, vro, dvr-ms, wtv, amv, mp2, mpe, mpv`
- **9 languages** — 中文 / English / Deutsch / 日本語 / Français / 한국어 / Español / Português / Italiano (switch in the top-right dropdown)
- **External language file** — all UI text lives in `bin/languages.json`, so you can fix a translation without touching code
- **Clickable result** — while converting, the left of the progress bar shows animated `Running....`; when finished it shows `Done: <folder path>`. Hover to see all output folders, click to open the latest one in Explorer
- **Relative paths** — the whole folder is portable. Move `Video2JPG\` anywhere and it still works
- **Free** — MIT licensed (see [License](#-license))

---

## 📦 Download & Run

### Option A: Download the release (recommended)

1. Download the latest release ZIP from the [Releases](../../releases) page
2. Unzip it anywhere, e.g. `D:\Video2JPG\`
3. Double-click **`Run_Video2JPG.BAT`**

No Python install needed if you use the release build. If you run from source, see below.

### Option B: Run from source

Requirements: **Windows + Python 3.x**

```bat
pip install tkinterdnd2
python Video2JPG_GUI.py
```

Or just double-click `Run_Video2JPG.BAT` — it tries to install `tkinterdnd2` automatically if it is missing. Without it, drag & drop is disabled, but **Add Files / Add Folder** still work.

---

## 🚀 How to use

1. Double-click `Run_Video2JPG.BAT`
2. **Drag** video files or a video folder onto the file list
   - Or use **Add Files / Add Folder** on the right of the list
   - **Empty** clears the list (disabled while converting)
   - **Remove Selected** removes only the highlighted rows
3. Drag the **Quality** slider: `60` = smaller files, `95` = highest quality
4. Click **Start**
5. Watch the progress bar. Use **Suspend** to pause, **Cancel** to stop
6. When it shows `Done: ..._Frames`, **click that path** to open the output folder

---

## 📂 Output

For each video, a folder is created **next to the video**:

```
D:\Videos\
  my-trip.mp4
  my-trip_Frames\
    frame_000001.jpg
    frame_000002.jpg
    frame_000003.jpg
    ...
```

- Folder name: `<video filename>_Frames`
- File names: `frame_%06d.jpg` (zero-padded, in video order)
- **All frames** are extracted (`-vsync 0`, no frames skipped)
- Existing files in the output folder are overwritten on re-run (`-y`)

> ⚠️ Extracting every frame of a long video produces a lot of files. A 10-minute video at 30 fps = ~18,000 JPGs. Make sure you have enough disk space.

---

## 🗂 Project structure

```
Video2JPG\
  README.md
  LICENSE
  Video2JPG_GUI.py        # the app (Tkinter, relative paths only)
  Run_Video2JPG.BAT       # launcher: cd to its own folder, start the GUI
  bin\
    ffmpeg.exe            # bundled FFmpeg (see FFmpeg note below)
    ffplay.exe
    ffprobe.exe
    languages.json        # UI dictionary: 9 languages × 39 strings
```

---

## 🌍 Languages

| Language | Code | | Language | Code |
|---|---|---|---|---|
| 中文 | `zh` | | 한국어 | `ko` |
| English | `en` | | Español | `es` |
| Deutsch | `de` | | Português | `pt` |
| 日本語 | `ja` | | Italiano | `it` |
| Français | `fr` | | | |

### Add / fix a translation

1. Open `bin/languages.json`
2. Find your language block, e.g. `"de": { ... }`
3. Edit the value, save, restart the app — no code change needed
4. To add a new language: copy the whole `"en"` block, change the key (e.g. `"nl"`), translate the values, and add `"Nederlands": "nl"` to `_langs` at the top of the file

Missing/broken `languages.json`? The app still starts with a built-in minimal English fallback.

---

## ❓ FAQ

**Q: I dragged a video in, but nothing happened.**
A: Drag & drop needs `tkinterdnd2`. Run `pip install tkinterdnd2`, then restart. Or use **Add Files / Add Folder**.

**Q: Where are my JPGs?**
A: Next to each video, in `<video name>_Frames\`. Click the blue `Done: ...` path at the left of the progress bar to open it.

**Q: Why is the output so big / so many files?**
A: Every frame is extracted. Lower the quality (e.g. `70`) for smaller files, or extract fewer frames with FFmpeg manually if you only need 1 fps (see below).

**Q: Can I extract 1 frame per second instead of every frame?**
A: Not in the V1.0 GUI — it extracts all frames by design. If you need it, this is a good first contribution (see Contributing).

**Q: Does it work on macOS / Linux?**
A: The Python code is mostly portable (it falls back to `ffmpeg` on PATH), but Suspend uses Windows APIs and the launcher is a `.BAT`. V1.0 targets Windows.

**Q: Is it really free?**
A: Yes. MIT license — free for personal and commercial use. FFmpeg in `bin\` is a separate project under its own license (see below).

---

## 🤝 Contributing

Issues and pull requests are welcome — especially:

- New translations in `bin/languages.json`
- An FPS / frame-interval option
- A macOS / Linux launcher
- A packaged release (PyInstaller) workflow

---

## 📄 License

**Video2JPG itself: MIT License** — free to use, copy, modify, and distribute, including commercially. See [`LICENSE`](LICENSE).

### FFmpeg note

`bin\ffmpeg.exe`, `bin\ffplay.exe`, and `bin\ffprobe.exe` are **not** written by this project. They are from the [FFmpeg](https://ffmpeg.org/) project and are distributed under the **LGPL/GPL** license. If you redistribute this project, keep the FFmpeg binaries and their license intact, or replace them with your own FFmpeg build. You can also delete `bin\ffmpeg.exe` and put FFmpeg on your system `PATH` — the app will find it there.

---

## 👤 Author

**Video2JPG — V1.0 2026**
Writen by Tony Lin

- Facebook: https://www.facebook.com/100000242772138
- Issues / feedback: please open an issue on GitHub

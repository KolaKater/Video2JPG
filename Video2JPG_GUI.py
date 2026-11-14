# -*- coding: utf-8 -*-
"""
Video2JPG - Writen by Tony Lin
相对路径: ffmpeg 在 ./bin/ffmpeg.exe
输出: 视频旁边 / <视频文件名>_Frames / frame_000001.jpg ...
启动: 双击 Run_Video2JPG.BAT
拖拽依赖: pip install tkinterdnd2  (BAT 会自动尝试安装, 没网也能用 Add Files/Add Folder)
"""
import os, sys, json, subprocess, threading, queue, webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FFMPEG = BASE_DIR / "bin" / "ffmpeg.exe"
def find_ffmpeg():
    return str(FFMPEG) if FFMPEG.exists() else "ffmpeg"

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ---------- 多种视频格式 ----------
VIDEO_EXTS = {".mp4",".mkv",".avi",".mov",".wmv",".flv",".webm",".m4v",".mpg",".mpeg",
".ts",".m2ts",".mts",".vob",".3gp",".3g2",".rm",".rmvb",".asf",".divx",".f4v",".m2v",
".ogv",".ogm",".mxf",".dav",".mod",".tod",".vro",".dvr-ms",".wtv",".amv",".mp2",".mpe",".mpv"}
FILETYPES = [("Video", " ".join(f"*{e}" for e in sorted(VIDEO_EXTS))), ("All files", "*.*")]
FACEBOOK_URL = "https://www.facebook.com/100000242772138"

# ---------- 五种语言 ----------
# ---------- 字典文件: bin/languages.json (相对路径) ----------
LANG_FILE = BASE_DIR / "bin" / "languages.json"
def _load_langs():
    try:
        with open(LANG_FILE, encoding="utf-8") as f:
            d = json.load(f)
        langs = d.pop("_langs", {"English": "en"})
        return langs, d
    except Exception:
        # 兜底: 字典文件缺失/损坏时仍能启动
        return {"English": "en"}, {"en": {"title": "Video2JPG", "subtitle": "Drop videos -> extract JPG frames",
            "list": " File List ", "empty": "Empty", "add_files": "Add Files", "add_folder": "Add Folder",
            "remove": "Remove Selected", "hint": "Drop files/folders", "quality": " JPG Quality ",
            "quality_label": "Quality:", "quality_hint": "60 - 95", "start": "Start", "suspend": "Suspend",
            "resume": "Resume", "cancel": "Cancel", "about": "About", "facebook": "Facebook",
            "ready": "Ready", "added": "Added {n}, total {t}", "not_added": "Nothing added",
            "cleared": "Cleared", "busy_clear": "Conversion running.", "need_files": "Drop videos first.",
            "converting": "Converting [{i}/{t}] {name}", "paused": "Paused", "resumed": "Resumed",
            "cancelling": "Cancelling...", "cancelled": "Cancelled", "done": "Done! {t} videos, quality {q}",
            "no_ffmpeg": "ffmpeg not found: {f}", "fail": "Failed {name}: {e}",
            "suspend_fail": "Suspend failed: {e}", "about_text": "Video2JPG\nV1.0 2026\nWriten by Tony Lin",
            "lang": "Language:", "progress": "Progress", "running": "Running", "done_prefix": "Done", "click_to_open": "Click to open folder", "done_tip": "{done}\nClick to open:\n{paths}"}}
LANGS, T = _load_langs()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Video2JPG")
        self.root.geometry("800x540"); self.root.minsize(660, 460)
        self.lang_code = tk.StringVar(value="zh")
        self.lang_name = tk.StringVar(value="中文")
        self.files = []
        self.quality = tk.IntVar(value=85)
        self.status_var = tk.StringVar(value="")
        self.progress_var = tk.DoubleVar(value=0)
        self.running=False; self.paused=False; self.cancelled=False
        self.done_dirs=[]; self.run_tick=0; self.tooltip=None
        self.current_proc=None; self.log_q=queue.Queue()
        self._build_ui()
        self._apply_lang()
        self._setup_dnd()  # 关键: 必须在 TkinterDnD.Tk() 上注册
        self.root.after(200, self._poll)

    def tr(self, k, **kw):
        s = T[self.lang_code.get()].get(k, k)
        try: return s.format(**kw)
        except Exception: return s

    # ---------- UI ----------
    def _build_ui(self):
        top = ttk.Frame(self.root, padding=10); top.pack(fill="x")
        self.lbl_title = ttk.Label(top, font=("Segoe UI", 16, "bold")); self.lbl_title.pack(side="left")
        self.lbl_sub = ttk.Label(top, font=("Segoe UI", 10)); self.lbl_sub.pack(side="left")
        # 语言切换
        ttk.Label(top, textvariable=self.lang_name).pack(side="right", padx=(4,0))  # 占位, 下面用 combobox
        self.lang_combo = ttk.Combobox(top, values=list(LANGS.keys()), state="readonly", width=12)
        self.lang_combo.set("中文"); self.lang_combo.pack(side="right")
        self.lang_combo.bind("<<ComboboxSelected>>", lambda e: self._set_lang(LANGS[self.lang_combo.get()]))
        self.lbl_lang = ttk.Label(top, text="语言:"); self.lbl_lang.pack(side="right", padx=(0,4))

        lf = ttk.LabelFrame(self.root, padding=8); self.list_frame = lf; lf.pack(fill="both", expand=True, padx=10, pady=(0,6))
        mid = ttk.Frame(lf); mid.pack(fill="both", expand=True)
        self.listbox = tk.Listbox(mid, selectmode="extended", font=("Segoe UI", 10))
        self.listbox.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(mid, orient="vertical", command=self.listbox.yview); sb.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=sb.set)
        side = ttk.Frame(mid); side.pack(side="right", fill="y", padx=(8,0))
        self.btn_empty = ttk.Button(side, command=self.empty_list, width=16); self.btn_empty.pack(pady=2)
        self.btn_addf = ttk.Button(side, command=self.add_files, width=16); self.btn_addf.pack(pady=2)
        self.btn_addd = ttk.Button(side, command=self.add_folder, width=16); self.btn_addd.pack(pady=2)
        self.btn_rem = ttk.Button(side, command=self.remove_selected, width=16); self.btn_rem.pack(pady=2)
        self.lbl_hint = ttk.Label(side, justify="left", font=("Segoe UI", 9)); self.lbl_hint.pack(pady=(10,0))

        qf = ttk.LabelFrame(self.root, padding=8); self.q_frame = qf; qf.pack(fill="x", padx=10, pady=(0,6))
        self.lbl_q = ttk.Label(qf); self.lbl_q.pack(side="left")
        self.q_val = ttk.Label(qf, font=("Segoe UI", 11, "bold"), width=4); self.q_val.config(text="85"); self.q_val.pack(side="left", padx=(4,2))
        ttk.Scale(qf, from_=60, to=95, orient="horizontal", variable=self.quality,
                  command=lambda v: self.q_val.config(text=str(int(float(v))))).pack(side="left", fill="x", expand=True, padx=6)
        self.lbl_qhint = ttk.Label(qf); self.lbl_qhint.pack(side="left")

        pf = ttk.Frame(self.root, padding=(10,0,10,6)); pf.pack(fill="x")
        # 进度条紧邻左侧: Running.... / Done + 保存地址 (可悬停提示, 单击打开文件夹)
        self.lbl_run = tk.Label(pf, text="", font=("Segoe UI", 10), anchor="w")
        self.lbl_run.pack(side="left", padx=(0,8))
        self.lbl_run.bind("<Enter>", self._run_enter); self.lbl_run.bind("<Leave>", self._run_leave)
        self.lbl_run.bind("<Button-1>", lambda e: self._open_done_folder())
        ttk.Progressbar(pf, variable=self.progress_var, maximum=100).pack(side="left", fill="x", expand=True)
        ttk.Label(self.root, textvariable=self.status_var).pack(fill="x", padx=10)

        bf = ttk.Frame(self.root, padding=(10,0,10,10)); bf.pack(fill="x")
        self.btn_about = ttk.Button(bf, command=self.show_about, width=12); self.btn_about.pack(side="left", padx=(0,6))
        self.btn_fb = ttk.Button(bf, command=lambda: webbrowser.open(FACEBOOK_URL), width=12); self.btn_fb.pack(side="left", padx=6)
        self.btn_cancel = ttk.Button(bf, command=self.cancel, width=14, state="disabled"); self.btn_cancel.pack(side="right", padx=6)
        self.btn_susp = ttk.Button(bf, command=self.toggle_suspend, width=14, state="disabled"); self.btn_susp.pack(side="right", padx=6)
        self.btn_start = ttk.Button(bf, command=self.start, width=14); self.btn_start.pack(side="right", padx=(6,0))

    def _set_lang(self, code):
        self.lang_code.set(code)
        # 反向找名字
        for k,v in LANGS.items():
            if v==code: self.lang_name.set(k); self.lang_combo.set(k)
        self._apply_lang()

    def _apply_lang(self):
        self.lbl_title.config(text=self.tr("title"))
        self.lbl_sub.config(text="  "+self.tr("subtitle"))
        self.list_frame.config(text=self.tr("list"))
        self.btn_empty.config(text=self.tr("empty"))
        self.btn_addf.config(text=self.tr("add_files"))
        self.btn_addd.config(text=self.tr("add_folder"))
        self.btn_rem.config(text=self.tr("remove"))
        self.lbl_hint.config(text=self.tr("hint"))
        self.q_frame.config(text=self.tr("quality"))
        self.lbl_q.config(text=self.tr("quality_label"))
        self.lbl_qhint.config(text=self.tr("quality_hint"))
        self.lbl_lang.config(text=self.tr("lang"))
        self.btn_start.config(text=self.tr("start"))
        self.btn_susp.config(text=self.tr("resume") if self.paused else self.tr("suspend"))
        self.btn_cancel.config(text=self.tr("cancel"))
        self.btn_about.config(text=self.tr("about"))
        self.btn_fb.config(text=self.tr("facebook"))
        if not self.running: self.status_var.set(self.tr("ready"))
        if not self.running and not self.done_dirs: self.lbl_run.config(text="")

    # ---------- 拖拽 (修复要点) ----------
    def _setup_dnd(self):
        # 必须用 TkinterDnD.Tk() 创建的 root 才有 drop_target_register
        # 旧版失败原因: 用了普通 tk.Tk() + 假的 DragAcceptFiles, 没有真正注册 Drop 目标
        try:
            from tkinterdnd2 import DND_FILES
            for w in (self.root, self.listbox):
                w.drop_target_register(DND_FILES)
                w.dnd_bind("<<Drop>>", self._on_drop)
                w.dnd_bind("<<DragEnter>>", lambda e: "break")
            self.status_var.set(self.tr("ready") + "  [Drag & Drop OK]")
        except Exception:
            self.status_var.set(self.tr("ready") + "  [Drag&Drop needs: pip install tkinterdnd2]")

    def _on_drop(self, event):
        # tkinterdnd2 的 event.data 是带 {} 的路径列表, 用 splitlist 解析, 支持中文/空格路径
        try: paths = self.root.tk.splitlist(event.data)
        except Exception: paths = [event.data]
        self.add_paths(paths)
        return "break"

    # ---------- 文件 ----------
    def add_paths(self, paths):
        added=0
        for p in paths:
            p = Path(str(p).strip().strip('"'))
            if p.is_dir():
                for f in sorted(p.rglob("*")):
                    if f.is_file() and f.suffix.lower() in VIDEO_EXTS and f not in self.files:
                        self.files.append(f); added+=1
            elif p.is_file() and p.suffix.lower() in VIDEO_EXTS and p not in self.files:
                self.files.append(p); added+=1
        self.listbox.delete(0,"end")
        for f in self.files: self.listbox.insert("end", str(f))
        self.status_var.set(self.tr("added", n=added, t=len(self.files)) if added else self.tr("not_added"))
    def empty_list(self):
        if self.running: messagebox.showwarning("Video2JPG", self.tr("busy_clear")); return
        self.files.clear(); self.listbox.delete(0,"end"); self.status_var.set(self.tr("cleared"))
    def add_files(self):
        ps=filedialog.askopenfilenames(title=self.tr("add_files"), filetypes=FILETYPES)
        if ps: self.add_paths(ps)
    def add_folder(self):
        d=filedialog.askdirectory(title=self.tr("add_folder"))
        if d: self.add_paths([d])
    def remove_selected(self):
        for i in sorted(self.listbox.curselection(), reverse=True): del self.files[i]
        self.listbox.delete(0,"end")
        for f in self.files: self.listbox.insert("end", str(f))

    # ---------- 转换 ----------
    def qv(self,q): return max(2, min(31, round(2+(95-q)*(10/35))))
    def start(self):
        if self.running: return
        if not self.files: messagebox.showinfo("Video2JPG", self.tr("need_files")); return
        self.running=True; self.paused=False; self.cancelled=False; self.done_dirs=[]; self.run_tick=0
        self.lbl_run.config(text=self.tr("running")+"....", fg="black", cursor="", font=("Segoe UI", 10))
        self.btn_start.config(state="disabled"); self.btn_susp.config(state="normal"); self.btn_cancel.config(state="normal")
        threading.Thread(target=self._run, daemon=True).start()
    def toggle_suspend(self):
        if not self.running or not self.current_proc: return
        try:
            import ctypes
            k=ctypes.windll.kernel32; h=k.OpenProcess(0x0800, False, self.current_proc.pid)
            if not h: return
            if not self.paused:
                ctypes.windll.ntdll.NtSuspendProcess(h); self.paused=True
                self.btn_susp.config(text=self.tr("resume")); self.status_var.set(self.tr("paused"))
            else:
                ctypes.windll.ntdll.NtResumeProcess(h); self.paused=False
                self.btn_susp.config(text=self.tr("suspend")); self.status_var.set(self.tr("resumed"))
            k.CloseHandle(h)
        except Exception as e: messagebox.showerror("Video2JPG", self.tr("suspend_fail", e=e))
    def cancel(self):
        self.cancelled=True
        if self.current_proc and self.current_proc.poll() is None:
            try:
                if self.paused:
                    import ctypes; k=ctypes.windll.kernel32; h=k.OpenProcess(0x0800, False, self.current_proc.pid)
                    if h: ctypes.windll.ntdll.NtResumeProcess(h); k.CloseHandle(h)
                    self.paused=False
                self.current_proc.terminate()
            except Exception: pass
        self.status_var.set(self.tr("cancelling"))
    def _run(self):
        ffmpeg=find_ffmpeg(); q=int(self.quality.get()); qv=self.qv(q); total=len(self.files)
        for idx, video in enumerate(list(self.files)):
            if self.cancelled: break
            out=video.parent/f"{video.stem}_Frames"; out.mkdir(parents=True, exist_ok=True)
            cmd=[ffmpeg,"-y","-i",str(video),"-vsync","0","-q:v",str(qv),str(out/"frame_%06d.jpg")]
            self.log_q.put(("status", self.tr("converting", i=idx+1, t=total, name=video.name, out=out.name, q=q, qv=qv)))
            self.log_q.put(("progress", idx/total*100))
            try:
                self.current_proc=subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
                self.current_proc.wait()
            except FileNotFoundError:
                self.log_q.put(("error", self.tr("no_ffmpeg", f=ffmpeg))); break
            except Exception as e:
                self.log_q.put(("error", self.tr("fail", name=video.name, e=e))); continue
            self.current_proc=None
            if not self.cancelled: self.log_q.put(("done_dir", str(out)))
            if self.cancelled: break
            self.log_q.put(("progress", (idx+1)/total*100))
        self.log_q.put(("done", self.tr("cancelled") if self.cancelled else self.tr("done", t=total, q=q)))
        self.log_q.put(("reset", None))
    def _poll(self):
        try:
            while True:
                k,v=self.log_q.get_nowait()
                if k=="status": self.status_var.set(v)
                elif k=="progress": self.progress_var.set(v)
                elif k=="error": messagebox.showerror("Video2JPG", v)
                elif k=="done_dir":
                    self.done_dirs.append(v)
                    self.lbl_run.config(text=f"{self.tr('done_prefix')}: {v}", fg="blue", cursor="hand2", font=("Segoe UI", 10, "underline"))
                elif k=="done":
                    self.status_var.set(v)
                    if not self.cancelled and self.done_dirs:
                        self.lbl_run.config(text=f"{self.tr('done_prefix')}: {self.done_dirs[-1]}", fg="blue", cursor="hand2", font=("Segoe UI", 10, "underline"))
                    elif self.cancelled:
                        self.lbl_run.config(text=self.tr("cancelled"), fg="black", cursor="", font=("Segoe UI", 10))
                elif k=="reset":
                    self.running=False; self.paused=False
                    self.btn_start.config(state="normal"); self.btn_susp.config(state="disabled", text=self.tr("suspend")); self.btn_cancel.config(state="disabled")
        except queue.Empty: pass
        if self.running and not self.paused:
            self.run_tick += 1
            self.lbl_run.config(text=self.tr("running") + "." * (1 + self.run_tick % 4))
        self.root.after(200, self._poll)

    # ---------- Running/Done 标签: 悬停提示 + 单击打开 ----------
    def _open_done_folder(self):
        if not self.done_dirs: return
        folder = self.done_dirs[-1]
        try:
            if sys.platform == "win32": os.startfile(folder)
            elif sys.platform == "darwin": subprocess.Popen(["open", folder])
            else: subprocess.Popen(["xdg-open", folder])
        except Exception as e: messagebox.showerror("Video2JPG", str(e))
    def _run_enter(self, e):
        if not self.done_dirs: return
        if self.tooltip: return
        tip = self.tr("done_tip", done=self.tr("done_prefix"), paths="\n".join(self.done_dirs))
        x, y = e.x_root + 12, e.y_root + 12
        self.tooltip = tk.Toplevel(self.root); self.tooltip.wm_overrideredirect(True); self.tooltip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tooltip, text=tip, justify="left", bg="#ffffe0", relief="solid", borderwidth=1, font=("Segoe UI", 9)).pack()
    def _run_leave(self, e):
        if self.tooltip: self.tooltip.destroy(); self.tooltip = None
    def show_about(self): messagebox.showinfo("About", self.tr("about_text"))

def main():
    # 关键修复: 拖拽必须用 TkinterDnD.Tk(), 普通 tk.Tk() 拖不进去
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except ImportError:
        # 自动尝试安装一次 (有网才行), 失败也不崩, 仍可用按钮添加
        try:
            subprocess.check_call([sys.executable,"-m","pip","install","tkinterdnd2","-q"])
            from tkinterdnd2 import TkinterDnD
            root = TkinterDnD.Tk()
        except Exception:
            root = tk.Tk()
            messagebox.showwarning("Video2JPG","Drag & Drop 需要 tkinterdnd2\n请运行: pip install tkinterdnd2\n(仍可用 Add Files / Add Folder 添加)")
    App(root); root.mainloop()
if __name__=="__main__": main()

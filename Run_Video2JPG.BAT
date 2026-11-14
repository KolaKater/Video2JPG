@echo off
REM Video2JPG 启动器 - 相对路径, 双击即可运行
REM 所在文件夹即 Video2JPG 根目录
cd /d "%~dp0"
REM 优先用 pythonw (无控制台窗口), 失败则用 python
where pythonw >nul 2>&1
if %errorlevel%==0 (
    start "" /min pythonw "%~dp0Video2JPG_GUI.py"
) else (
    python "%~dp0Video2JPG_GUI.py"
)

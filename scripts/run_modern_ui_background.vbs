Option Explicit

Dim shell, fso, scriptDir, projectDir, uiDir, logDir, ps, cmd
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
projectDir = fso.GetParentFolderName(scriptDir)
uiDir = projectDir & "\ui"
logDir = projectDir & "\logs"

If Not fso.FolderExists(logDir) Then fso.CreateFolder(logDir)

If shell.Run("cmd /c where npm >nul 2>nul", 0, True) <> 0 Then
  MsgBox "npm was not found on PATH. Install Node.js LTS, reopen Command Prompt, then try again.", vbCritical, "SonarDeck Studio"
  WScript.Quit 1
End If

If shell.Run("cmd /c where py >nul 2>nul || where python >nul 2>nul", 0, True) <> 0 Then
  MsgBox "Python was not found on PATH. Run scripts\setup_windows.bat first, or install Python with Add to PATH enabled.", vbCritical, "SonarDeck Studio"
  WScript.Quit 1
End If

If Not fso.FileExists(projectDir & "\bridge\config.json") Then
  fso.CopyFile projectDir & "\bridge\config.example.json", projectDir & "\bridge\config.json", True
End If

cmd = "cmd /c cd /d """ & uiDir & """ && npm install >> """ & logDir & "\sonardeck-ui.log"" 2>&1"
If shell.Run(cmd, 0, True) <> 0 Then
  MsgBox "UI dependency install/update failed. Try scripts
un_modern_ui.bat to see details.", vbCritical, "SonarDeck Studio"
  WScript.Quit 1
End If

' Stop older dev/API listeners first so a second click does not collide with the same ports.
ps = "Get-NetTCPConnection -LocalPort 8765,5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ } | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"
shell.Run "powershell -NoProfile -ExecutionPolicy Bypass -Command """ & ps & """", 0, True

cmd = "cmd /c cd /d """ & projectDir & """ && (py -3 -m bridge.web_api --host 0.0.0.0 --port 8765 || python -m bridge.web_api --host 0.0.0.0 --port 8765) >> """ & logDir & "\sonardeck-api.log"" 2>&1"
shell.Run cmd, 0, False

cmd = "cmd /c cd /d """ & uiDir & """ && npm run dev >> """ & logDir & "\sonardeck-ui.log"" 2>&1"
shell.Run cmd, 0, False

WScript.Sleep 2500
shell.Run "http://127.0.0.1:5173", 1, False
WScript.Quit 0

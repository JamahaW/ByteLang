@echo off
color 1F
python.exe F:\Projects\ScriptingLanguage\MobileRobotics\main.py example

F:\Projects\ScriptingLanguage\ByteLangVirtualMashine\bin\debug\ByteLangVirtualMashine.exe F:\Projects\ScriptingLanguage\ByteLangVirtualMashine\bin\debug\example.dat
pause
taskkill -im cmd.exe
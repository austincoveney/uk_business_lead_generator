# PowerShell script to build the executable for Windows
Write-Host "Building UK Business Lead Generator for Windows..."
python -m pip install -r requirements.txt
python build_scripts\build.py
Write-Host "Build completed. Executable is in the dist folder."

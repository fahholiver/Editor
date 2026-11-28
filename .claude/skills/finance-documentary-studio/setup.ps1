# One-step setup for Windows (PowerShell). Run: powershell -ExecutionPolicy Bypass -File setup.ps1
$ErrorActionPreference = "Continue"; Set-Location $PSScriptRoot
$py = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { Write-Host "Python 3.10+ is needed: https://www.python.org/downloads/ (tick 'Add to PATH'). Then run this again."; exit 1 }
Write-Host "Python packages (drawing, sound, word timing). The first time takes a few minutes."
foreach ($p in @("skia-python","numpy","scipy","soundfile","pillow","certifi","imageio-ffmpeg")) { & $py -m pip install --quiet $p }
& $py -m pip install --quiet "faster-whisper>=1.0"; if ($LASTEXITCODE -ne 0) { Write-Host "  installing faster-whisper without onnxruntime"; & $py -m pip install --quiet ctranslate2 tokenizers huggingface_hub av tqdm; & $py -m pip install --quiet --no-deps "faster-whisper>=1.0" }
Write-Host "  (the free voice is installed later, only if you choose it)"
Write-Host "Depth layers for paintings (optional)"; & $py -m pip install --quiet opencv-python-headless rembg onnxruntime; if ($LASTEXITCODE -ne 0) { Write-Host "  (depth layers not installed: paintings will use a flat push)" }
New-Item -ItemType Directory -Force bin | Out-Null
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { $ff = & $py -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"; Copy-Item $ff bin\ffmpeg.exe }
& $py engine/selftest.py; Write-Host "Setup complete"

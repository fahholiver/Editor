# One-step setup for Windows (PowerShell). Run: powershell -ExecutionPolicy Bypass -File setup.ps1
$ErrorActionPreference = "Continue"; Set-Location $PSScriptRoot
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { Write-Host "Node.js 18+ is needed: https://nodejs.org (LTS). Then run this again."; exit 1 }
$py = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { Write-Host "Python 3.10+ is needed: https://www.python.org/downloads/ (tick 'Add to PATH'). Then run this again."; exit 1 }
Write-Host "Node packages"; npm install --no-audit --no-fund --silent; try { npx --yes playwright install chromium | Out-Null } catch { Write-Host "(couldn't download Chromium; Orbit will use Chrome or Edge)" }
Write-Host "Python packages (word timing, sound). This can take a few minutes the first time."
foreach ($p in @("soundfile","numpy","scipy","imageio-ffmpeg","certifi")) { try { & $py -m pip install --quiet $p } catch { Write-Host "  (could not install $p)" } }
& $py -m pip install --quiet "faster-whisper>=1.0"; if ($LASTEXITCODE -ne 0) { Write-Host "  installing faster-whisper without onnxruntime"; & $py -m pip install --quiet ctranslate2 tokenizers huggingface_hub av tqdm; & $py -m pip install --quiet --no-deps "faster-whisper>=1.0" }
Write-Host "  (the free voice is installed later, only if you choose it)"
Write-Host "ffmpeg"; New-Item -ItemType Directory -Force bin | Out-Null
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { $ff = & $py -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"; Copy-Item $ff bin\ffmpeg.exe }
Write-Host "Test render"; node scripts/render.mjs examples/test.json examples/test.mp4 | Out-Null; Write-Host "Setup complete: examples\test.mp4"

<#
.SYNOPSIS
  Installs (or removes) the Arabic translation patch for RuneScape: Dragonwilds.

.DESCRIPTION
  Copies the patch .pak into <Game>\RSDragonwilds\Content\Paks\~mods\.
  The game loads any *_P.pak found there on top of its own files, so nothing
  original is modified. Verify game files in Steam or run with -Uninstall to
  go back to the stock game.

.PARAMETER GamePath
  Game install folder. Auto-detected from Steam when omitted.

.PARAMETER Mode
  English (default): Arabic replaces the English text. Game is Arabic right away.
  French:            Arabic replaces the French text. In the game go to
                     Settings > Language and pick "العربية (Arabic)" (formerly French)
                     to switch; pick English to go back.

.PARAMETER Uninstall
  Remove the patch.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\Install-Arabic.ps1
  powershell -ExecutionPolicy Bypass -File .\Install-Arabic.ps1 -Mode French
  powershell -ExecutionPolicy Bypass -File .\Install-Arabic.ps1 -Uninstall
#>
[CmdletBinding()]
param(
    [string]$GamePath,
    [ValidateSet('English', 'French')]
    [string]$Mode = 'English',
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
$AppId = '1374490'
$PakNames = @{
    English = 'RSDragonwilds-Arabic-over-English_P'
    French  = 'RSDragonwilds-Arabic-over-French_P'
}
# each patch is three files: .pak (the text) + .utoc/.ucas (an empty container UE 5.6 insists on)
$Exts = @('.pak', '.utoc', '.ucas')
# If the .pak is not next to this script (e.g. you only downloaded the script),
# it is fetched from here. Point this at your GitHub repo's raw dist folder.
$DownloadBase = 'https://raw.githubusercontent.com/ali-saleh6/kawn-translations/main/games/rs-dragonwilds/dist'

function Write-Info($msg) { Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Warn2($msg){ Write-Host "[!] $msg" -ForegroundColor Yellow }

function Find-GamePath {
    $candidates = @()
    try {
        $steam = (Get-ItemProperty -Path 'HKCU:\Software\Valve\Steam' -ErrorAction Stop).SteamPath
        if ($steam) {
            $steam = $steam -replace '/', '\'
            $candidates += (Join-Path $steam 'steamapps\common\RSDragonwilds')
            $vdf = Join-Path $steam 'steamapps\libraryfolders.vdf'
            if (Test-Path $vdf) {
                foreach ($m in [regex]::Matches((Get-Content $vdf -Raw), '"path"\s+"([^"]+)"')) {
                    $lib = $m.Groups[1].Value -replace '\\\\', '\'
                    $candidates += (Join-Path $lib 'steamapps\common\RSDragonwilds')
                }
            }
        }
    } catch { }
    $candidates += 'C:\Program Files (x86)\Steam\steamapps\common\RSDragonwilds'
    # prefer the library that Steam actually installed the game into (has the app manifest)
    foreach ($c in $candidates) {
        $manifest = Join-Path (Split-Path (Split-Path $c -Parent) -Parent) "appmanifest_$AppId.acf"
        if ((Test-Path $manifest) -and (Test-Path (Join-Path $c 'RSDragonwilds\Content\Paks'))) { return $c }
    }
    foreach ($c in $candidates) {
        if (Test-Path (Join-Path $c 'RSDragonwilds\Content\Paks')) { return $c }
    }
    return $null
}

# ---------------------------------------------------------------------------
Write-Host ''
Write-Host '  RuneScape: Dragonwilds - Arabic translation patch' -ForegroundColor White
Write-Host '  ترجمة رن سكيب دراقون وايلدز للعربية' -ForegroundColor White
Write-Host ''

if (-not $GamePath) { $GamePath = Find-GamePath }
if (-not $GamePath -or -not (Test-Path (Join-Path $GamePath 'RSDragonwilds\Content\Paks'))) {
    Write-Warn2 'Could not find the game. Pass the folder explicitly, e.g.:'
    Write-Host '    powershell -ExecutionPolicy Bypass -File .\Install-Arabic.ps1 -GamePath "D:\Steam\steamapps\common\RSDragonwilds"'
    exit 1
}
Write-Info "Game folder: $GamePath"

if (Get-Process -Name 'RSDragonwilds*' -ErrorAction SilentlyContinue) {
    Write-Warn2 'The game is running. Close it first, then run this script again.'
    exit 1
}

$modsDir = Join-Path $GamePath 'RSDragonwilds\Content\Paks\~mods'

if ($Uninstall) {
    $removed = 0
    foreach ($n in $PakNames.Values) { foreach ($e in $Exts) {
        $p = Join-Path $modsDir "$n$e"
        if (Test-Path $p) { Remove-Item $p -Force; $removed++ }
    } }
    if ($removed) { Write-Ok "Removed $removed patch file(s). The game is back to stock text." }
    else { Write-Info 'No patch was installed.' }
    exit 0
}

$pakName = $PakNames[$Mode]
$srcDir = Join-Path $PSScriptRoot 'dist'
if (-not (Test-Path (Join-Path $srcDir "$pakName.pak"))) {
    $srcDir = Join-Path $env:TEMP 'RSDragonwilds-Arabic'
    New-Item -ItemType Directory -Force -Path $srcDir | Out-Null
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    foreach ($e in $Exts) {
        $url = "$DownloadBase/$pakName$e"
        Write-Info "Patch not found next to the script; downloading $url"
        Invoke-WebRequest -Uri $url -OutFile (Join-Path $srcDir "$pakName$e") -UseBasicParsing
    }
}

New-Item -ItemType Directory -Force -Path $modsDir | Out-Null
# only one variant at a time
foreach ($n in $PakNames.Values) { foreach ($e in $Exts) {
    $p = Join-Path $modsDir "$n$e"
    if ($n -ne $pakName -and (Test-Path $p)) { Remove-Item $p -Force }
} }
foreach ($e in $Exts) { Copy-Item (Join-Path $srcDir "$pakName$e") (Join-Path $modsDir "$pakName$e") -Force }
Write-Ok "Installed $pakName (.pak/.utoc/.ucas)"
Write-Ok "-> $modsDir"
Write-Host ''
if ($Mode -eq 'English') {
    Write-Host '  Start the game: the text is now in Arabic.' -ForegroundColor White
    Write-Host '  شغّل اللعبة وبتلقاها بالعربي على طول.' -ForegroundColor White
} else {
    Write-Host '  Start the game, open Settings > Language and pick "العربية (Arabic)".' -ForegroundColor White
    Write-Host '  شغّل اللعبة، روح للإعدادات > اللغة واختر "العربية".' -ForegroundColor White
}
Write-Host '  To remove:  powershell -ExecutionPolicy Bypass -File .\Install-Arabic.ps1 -Uninstall' -ForegroundColor DarkGray
Write-Host ''

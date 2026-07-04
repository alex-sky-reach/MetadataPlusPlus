$ErrorActionPreference = "Stop"

$PluginFolder = "Metadata++"
$InitFile = Join-Path $PluginFolder "__init__.py"

if (-not (Test-Path $InitFile)) {
    throw "Could not find $InitFile"
}

$InitContent = Get-Content $InitFile -Raw
$VersionMatch = [regex]::Match($InitContent, "version\s*=\s*\((\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)")

if (-not $VersionMatch.Success) {
    throw "Could not find plugin version in $InitFile"
}

$Version = "$($VersionMatch.Groups[1].Value).$($VersionMatch.Groups[2].Value).$($VersionMatch.Groups[3].Value)"

$ReleaseFolder = Join-Path "Public Releases" $Version
$ZipName = "Metadata++_${Version}.zip"
$ZipPath = Join-Path $ReleaseFolder $ZipName
$StageFolder = Join-Path $ReleaseFolder "_stage"

$ExcludeDirectories = @(
    "__pycache__",
    ".git",
    ".github",
    ".vscode",
    ".idea"
)

$ExcludeFilePatterns = @(
    "*.pyc",
    "*.pyo",
    "*.log",
    "*.tmp",
    "*.bak",
    "*~",
    ".DS_Store",
    "Thumbs.db"
)

New-Item -ItemType Directory -Path $ReleaseFolder -Force | Out-Null

if (Test-Path $StageFolder) {
    Remove-Item $StageFolder -Recurse -Force
}

New-Item -ItemType Directory -Path $StageFolder -Force | Out-Null

$PluginRoot = (Resolve-Path $PluginFolder).Path

$FilesToPackage = Get-ChildItem -Path $PluginFolder -Recurse -File | Where-Object {
    $File = $_
    $RelativePath = $File.FullName.Substring($PluginRoot.Length).TrimStart('\', '/')
    $PathParts = $RelativePath -split '[\\/]'

    foreach ($Directory in $ExcludeDirectories) {
        if ($PathParts -contains $Directory) {
            return $false
        }
    }

    foreach ($Pattern in $ExcludeFilePatterns) {
        if ($File.Name -like $Pattern) {
            return $false
        }
    }

    return $true
}

if (-not $FilesToPackage) {
    throw "No plugin files found to package."
}

foreach ($File in $FilesToPackage) {
    $RelativePath = $File.FullName.Substring($PluginRoot.Length).TrimStart('\', '/')
    $DestinationPath = Join-Path $StageFolder $RelativePath
    $DestinationFolder = Split-Path $DestinationPath -Parent

    New-Item -ItemType Directory -Path $DestinationFolder -Force | Out-Null
    Copy-Item -Path $File.FullName -Destination $DestinationPath -Force
}

Compress-Archive -Path (Join-Path $StageFolder "*") -DestinationPath $ZipPath -Force
Remove-Item $StageFolder -Recurse -Force

Write-Host "Created public release package:"
Write-Host $ZipPath

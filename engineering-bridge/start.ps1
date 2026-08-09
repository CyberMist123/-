$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
node .\src\bridge.mjs

param(
  [int]$Port = 4173
)

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Url = "http://127.0.0.1:$Port/taihe-hall-3d-prototype.html"
$Prefix = "http://127.0.0.1:$Port/"

Add-Type -AssemblyName System.Web

$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add($Prefix)

try {
  $listener.Start()
} catch {
  Start-Process $Url
  Write-Host "Port $Port may already be in use. Opened $Url"
  Read-Host "Press Enter to close"
  exit
}

Start-Process $Url
Write-Host "Taihe Hall 3D viewer is running at $Url"
Write-Host "Keep this window open while viewing. Press Ctrl+C to stop."

function Get-ContentType($Path) {
  switch -Regex ($Path) {
    "\.html$" { return "text/html; charset=utf-8" }
    "\.js$" { return "text/javascript; charset=utf-8" }
    "\.css$" { return "text/css; charset=utf-8" }
    "\.json$" { return "application/json; charset=utf-8" }
    "\.glb$" { return "model/gltf-binary" }
    "\.png$" { return "image/png" }
    "\.jpg$|\.jpeg$" { return "image/jpeg" }
    "\.webp$" { return "image/webp" }
    "\.wasm$" { return "application/wasm" }
    default { return "application/octet-stream" }
  }
}

while ($listener.IsListening) {
  $context = $listener.GetContext()
  $requestPath = [System.Web.HttpUtility]::UrlDecode($context.Request.Url.AbsolutePath.TrimStart("/"))
  if ([string]::IsNullOrWhiteSpace($requestPath)) {
    $requestPath = "taihe-hall-3d-prototype.html"
  }

  $localPath = Join-Path $Root $requestPath
  $resolvedRoot = [System.IO.Path]::GetFullPath($Root)
  $resolvedPath = [System.IO.Path]::GetFullPath($localPath)

  if (-not $resolvedPath.StartsWith($resolvedRoot) -or -not (Test-Path -LiteralPath $resolvedPath -PathType Leaf)) {
    $context.Response.StatusCode = 404
    $bytes = [System.Text.Encoding]::UTF8.GetBytes("Not found")
  } else {
    $context.Response.StatusCode = 200
    $context.Response.ContentType = Get-ContentType $resolvedPath
    $bytes = [System.IO.File]::ReadAllBytes($resolvedPath)
  }

  $context.Response.ContentLength64 = $bytes.Length
  $context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
  $context.Response.OutputStream.Close()
}

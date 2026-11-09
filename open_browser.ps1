$url = "http://127.0.0.1:5000"
Write-Host "Opening $url in Google Chrome..."
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"

if (Test-Path $chromePath) {
    Start-Process $chromePath -ArgumentList "$url --new-window"
} else {
    Start-Process $url
}

Start-Sleep -Milliseconds 1200
try {
    $wshell = New-Object -ComObject WScript.Shell
    $wshell.AppActivate("Google Chrome")
    $wshell.AppActivate("Chrome")
} catch {
    # Ignore if not supported
}
Write-Host "Done! Browser window requested to foreground."

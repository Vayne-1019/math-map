# Windows built-in OCR (zh-Hant-TW) over every PNG in a folder -> one .txt per page.
# usage: powershell -File ocr_win.ps1 <imgdir> <outdir>
param([string]$ImgDir, [string]$OutDir)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) { $task = $asTask.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait(-1) | Out-Null; $task.Result }
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]
$lang = [Windows.Globalization.Language]::new('zh-Hant-TW')
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
New-Item -ItemType Directory -Force $OutDir | Out-Null
Get-ChildItem $ImgDir -Filter *.png | Sort-Object Name | ForEach-Object {
  $out = Join-Path $OutDir ($_.BaseName + '.txt')
  if (Test-Path $out) { return }
  $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($_.FullName)) ([Windows.Storage.StorageFile])
  $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $dec = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bmp = Await ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $res = Await ($engine.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
  ($res.Lines | ForEach-Object { $_.Text }) -join "`n" | Out-File -Encoding utf8 $out
  $stream.Dispose()
}
"done"

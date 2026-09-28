# 媒体ランキング週次取得 (タスクスケジューラ / デスクトップのショートカットから実行)
$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath $PSScriptRoot
$log = Join-Path $PSScriptRoot 'run_weekly.log'
Start-Transcript -Path $log -Force | Out-Null
try {
    git pull --rebase -q
    & 'C:\Users\jurassic\AppData\Local\Programs\Python\Python312\python.exe' fetch_rankings.py
    $fetchExit = $LASTEXITCODE
    git add ranking_data.json ranking_data.js
    git diff --cached --quiet
    if ($LASTEXITCODE -ne 0) {
        $today = Get-Date -Format 'yyyy-MM-dd'
        git commit -q -m "媒体ランキング自動取得 $today"
        git pull --rebase -q
        git push -q
        if ($LASTEXITCODE -eq 0) { Write-Host "GitHubに保存しました" } else { Write-Host "GitHubへの保存に失敗しました" ; $fetchExit = 1 }
    } else {
        Write-Host "新しく登録するデータはありませんでした(入力済み)"
    }
    if ($fetchExit -ne 0) {
        Add-Type -AssemblyName PresentationFramework
        [System.Windows.MessageBox]::Show("ランキング自動取得で一部取得できなかった媒体があります。`n$log を確認してください。", '媒体ランキング自動取得') | Out-Null
    }
} finally {
    Stop-Transcript | Out-Null
}

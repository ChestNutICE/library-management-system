$ErrorActionPreference = "Stop"
$projectDirectory = "C:\Users\YuboH\Documents\Codex\2026-07-18\c-python"

function Find-Git {
    $command = Get-Command git.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $candidates = @(
        "C:\Program Files\Git\cmd\git.exe",
        "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
    )
    return $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}

$git = Find-Git
if (-not $git) {
    Write-Host "没有检测到 Git，正在通过 winget 安装……"
    & winget install --id Git.Git -e --scope user --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) { throw "Git 安装失败，请检查网络后重试。" }
    $git = Find-Git
}
if (-not $git) { throw "Git 已安装但未找到 git.exe，请重新打开电脑后再运行本脚本。" }

Set-Location -LiteralPath $projectDirectory
& $git config user.name "ChestNutICE"
& $git config user.email "sudoavocado@gmail.com"
& $git add --all

$changes = & $git status --porcelain
if ($changes) {
    & $git commit -m "Complete library management system"
    if ($LASTEXITCODE -ne 0) { throw "创建 Git 提交失败。" }
} else {
    Write-Host "没有新的文件需要提交，将直接推送现有提交。"
}

& $git branch -M main
& $git push -u origin main
if ($LASTEXITCODE -ne 0) {
    throw "推送失败。如果弹出 GitHub 登录窗口，请登录后再次运行本脚本。"
}

Write-Host ""
Write-Host "提交成功：https://github.com/ChestNutICE/library-system"
Read-Host "按回车键关闭"

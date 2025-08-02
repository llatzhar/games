# PowerShell テスト実行スクリプト
#Requires -Version 5.1
[CmdletBinding()]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseApprovedVerbs', '', Justification='This is a build script with specific naming conventions')]
param(
    [string]$Command = "help"
)

# 実行ポリシーチェックと自動対応
function Test-ExecutionPolicy {
    $currentPolicy = Get-ExecutionPolicy
    if ($currentPolicy -eq "Restricted") {
        Write-Host "警告: PowerShellの実行ポリシーが制限されています。" -ForegroundColor Yellow
        Write-Host "現在のポリシー: $currentPolicy" -ForegroundColor Red
        Write-Host ""
        Write-Host "自動的に実行ポリシーを変更しますか？ (Y/N)" -ForegroundColor Yellow
        $response = Read-Host
        
        if ($response -eq "Y" -or $response -eq "y" -or $response -eq "yes") {
            try {
                Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
                Write-Host "実行ポリシーを RemoteSigned に変更しました。" -ForegroundColor Green
                return $true
            }
            catch {
                Write-Host "エラー: 実行ポリシーの変更に失敗しました。" -ForegroundColor Red
                Write-Host "管理者権限で以下のコマンドを実行してください:" -ForegroundColor Yellow
                Write-Host "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Cyan
                return $false
            }
        } else {
            Write-Host "実行ポリシーの変更をスキップしました。" -ForegroundColor Yellow
            Write-Host "手動で以下のコマンドを実行してください:" -ForegroundColor Yellow
            Write-Host "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Cyan
            return $false
        }
    } elseif ($currentPolicy -eq "AllSigned" -or $currentPolicy -eq "RemoteSigned" -or $currentPolicy -eq "Unrestricted") {
        Write-Host "実行ポリシー確認: $currentPolicy (OK)" -ForegroundColor Green
        return $true
    } else {
        Write-Host "警告: 予期しない実行ポリシー: $currentPolicy" -ForegroundColor Yellow
        return $true
    }
}

# 初期化時に実行ポリシーをチェック
if (-not (Test-ExecutionPolicy)) {
    Write-Host "実行ポリシーの問題により、スクリプトを正常に実行できない可能性があります。" -ForegroundColor Red
    Write-Host ""
}

function Show-Help {
    Write-Host "利用可能なコマンド:" -ForegroundColor Green
    Write-Host "  test          - テストを実行"
    Write-Host "  test-verbose  - 詳細出力でテストを実行"
    Write-Host "  test-coverage - カバレッジ付きでテストを実行"
    Write-Host "  lint          - コードのリンティング"
    Write-Host "  format        - コードフォーマット"
    Write-Host "  check         - フォーマットとリンティングのチェック"
    Write-Host "  install       - 依存関係のインストール"
    Write-Host "  clean         - 一時ファイルの削除"
    Write-Host ""
    Write-Host "使用例:" -ForegroundColor Yellow
    Write-Host "  .\test.ps1 test"
    Write-Host "  .\test.ps1 test-coverage"
}

function Test-Command {
    param([string]$CommandName)
    return $null -ne (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Install-Dependencies {
    Write-Host "依存関係をインストール中..." -ForegroundColor Blue
    
    if (-not (Test-Command "python")) {
        Write-Host "エラー: Pythonがインストールされていません。" -ForegroundColor Red
        return
    }
    
    try {
        python -m pip install --upgrade pip
        if (Test-Path "requirements.txt") {
            pip install -r requirements.txt
            Write-Host "依存関係のインストールが完了しました。" -ForegroundColor Green
        } else {
            Write-Host "警告: requirements.txt が見つかりません。" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "エラー: 依存関係のインストールに失敗しました。" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

function Invoke-Tests {
    Write-Host "テストを実行中..." -ForegroundColor Blue
    
    if (-not (Test-Command "python")) {
        Write-Host "エラー: Pythonがインストールされていません。" -ForegroundColor Red
        return
    }
    
    try {
        python -m unittest discover -s tests -p "test_*.py"
        Write-Host "テストが完了しました。" -ForegroundColor Green
    }
    catch {
        Write-Host "エラー: テストの実行に失敗しました。" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

function Invoke-TestsVerbose {
    Write-Host "詳細出力でテストを実行中..." -ForegroundColor Blue
    
    if (-not (Test-Command "python")) {
        Write-Host "エラー: Pythonがインストールされていません。" -ForegroundColor Red
        return
    }
    
    try {
        python -m unittest discover -s tests -p "test_*.py" -v
        Write-Host "詳細テストが完了しました。" -ForegroundColor Green
    }
    catch {
        Write-Host "エラー: テストの実行に失敗しました。" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

function Invoke-TestsCoverage {
    Write-Host "カバレッジ付きでテストを実行中..." -ForegroundColor Blue
    
    if (-not (Test-Command "coverage")) {
        Write-Host "警告: coverage がインストールされていません。pip install coverage でインストールしてください。" -ForegroundColor Yellow
        return
    }
    
    try {
        coverage run -m unittest discover -s tests -p "test_*.py"
        coverage report -m
        coverage html
        Write-Host "HTMLカバレッジレポートが htmlcov/ に生成されました" -ForegroundColor Green
    }
    catch {
        Write-Host "エラー: カバレッジテストの実行に失敗しました。" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

function Invoke-Lint {
    Write-Host "リンティングを実行中..." -ForegroundColor Blue
    
    if (-not (Test-Command "flake8")) {
        Write-Host "警告: flake8 がインストールされていません。pip install flake8 でインストールしてください。" -ForegroundColor Yellow
        return
    }
    
    try {
        flake8 . --count --ignore=E203,W503 --max-line-length=88 --statistics
        Write-Host "リンティングが完了しました。" -ForegroundColor Green
    }
    catch {
        Write-Host "エラー: リンティングの実行に失敗しました。" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

function Invoke-Format {
    Write-Host "コードをフォーマット中..." -ForegroundColor Blue
    
    $hasBlack = Test-Command "black"
    $hasIsort = Test-Command "isort"
    
    if (-not $hasBlack) {
        Write-Host "警告: black がインストールされていません。" -ForegroundColor Yellow
    }
    if (-not $hasIsort) {
        Write-Host "警告: isort がインストールされていません。" -ForegroundColor Yellow
    }
    
    try {
        if ($hasBlack) { black --line-length=88 . }
        if ($hasIsort) { isort --line-length=88 . }
        Write-Host "フォーマットが完了しました。" -ForegroundColor Green
    }
    catch {
        Write-Host "エラー: フォーマットの実行に失敗しました。" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

function Invoke-Check {
    Write-Host "フォーマットとリンティングをチェック中..." -ForegroundColor Blue
    
    try {
        if (Test-Command "black") {
            black --check --diff --line-length=88 .
        } else {
            Write-Host "警告: black がインストールされていません。" -ForegroundColor Yellow
        }
        
        if (Test-Command "isort") {
            isort --check-only --diff --line-length=88 .
        } else {
            Write-Host "警告: isort がインストールされていません。" -ForegroundColor Yellow
        }
        
        if (Test-Command "flake8") {
            flake8 . --count --ignore=E203,W503 --max-line-length=88 --statistics
        } else {
            Write-Host "警告: flake8 がインストールされていません。" -ForegroundColor Yellow
        }
        
        Write-Host "チェックが完了しました。" -ForegroundColor Green
    }
    catch {
        Write-Host "エラー: チェックの実行に失敗しました。" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}

function Clear-Files {
    Write-Host "一時ファイルを削除中..." -ForegroundColor Blue
    
    try {
        # .pyc ファイルを削除
        Get-ChildItem -Recurse -Name "*.pyc" -ErrorAction SilentlyContinue | ForEach-Object {
            Remove-Item $_ -Force -ErrorAction SilentlyContinue
        }
        
        # __pycache__ ディレクトリを削除
        Get-ChildItem -Recurse -Name "__pycache__" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            Remove-Item $_ -Recurse -Force -ErrorAction SilentlyContinue
        }
        
        # カバレッジファイルを削除
        @(".coverage", "htmlcov", "coverage.xml", ".pytest_cache") | ForEach-Object {
            if (Test-Path $_) { 
                Remove-Item $_ -Recurse -Force -ErrorAction SilentlyContinue 
            }
        }
        
        Write-Host "一時ファイルの削除が完了しました。" -ForegroundColor Green
    }
    catch {
        Write-Host "警告: 一部のファイル削除に失敗しました。" -ForegroundColor Yellow
        Write-Host $_.Exception.Message -ForegroundColor Yellow
    }
}

# コマンド実行
switch ($Command) {
    "help" { Show-Help }
    "install" { Install-Dependencies }
    "test" { Invoke-Tests }
    "test-verbose" { Invoke-TestsVerbose }
    "test-coverage" { Invoke-TestsCoverage }
    "lint" { Invoke-Lint }
    "format" { Invoke-Format }
    "check" { Invoke-Check }
    "clean" { Clear-Files }
    default { 
        Write-Host "不明なコマンド: $Command" -ForegroundColor Red
        Show-Help 
    }
}

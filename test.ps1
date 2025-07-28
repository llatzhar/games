# PowerShell テスト実行スクリプト
param(
    [string]$Command = "help"
)

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

function Install-Dependencies {
    Write-Host "依存関係をインストール中..." -ForegroundColor Blue
    python -m pip install --upgrade pip
    pip install -r requirements.txt
}

function Run-Tests {
    Write-Host "テストを実行中..." -ForegroundColor Blue
    python -m unittest discover -s . -p "test_*.py"
}

function Run-TestsVerbose {
    Write-Host "詳細出力でテストを実行中..." -ForegroundColor Blue
    python -m unittest discover -s . -p "test_*.py" -v
}

function Run-TestsCoverage {
    Write-Host "カバレッジ付きでテストを実行中..." -ForegroundColor Blue
    coverage run -m unittest discover -s . -p "test_*.py"
    coverage report -m
    coverage html
    Write-Host "HTMLカバレッジレポートが htmlcov/ に生成されました" -ForegroundColor Green
}

function Run-Lint {
    Write-Host "リンティングを実行中..." -ForegroundColor Blue
    flake8 . --count --statistics
}

function Run-Format {
    Write-Host "コードをフォーマット中..." -ForegroundColor Blue
    black .
    isort .
}

function Run-Check {
    Write-Host "フォーマットとリンティングをチェック中..." -ForegroundColor Blue
    black --check --diff .
    isort --check-only --diff .
    flake8 . --count --statistics
}

function Clean-Files {
    Write-Host "一時ファイルを削除中..." -ForegroundColor Blue
    Get-ChildItem -Recurse -Name "*.pyc" | Remove-Item -Force
    Get-ChildItem -Recurse -Name "__pycache__" -Directory | Remove-Item -Recurse -Force
    if (Test-Path ".coverage") { Remove-Item ".coverage" -Force }
    if (Test-Path "htmlcov") { Remove-Item "htmlcov" -Recurse -Force }
    if (Test-Path "coverage.xml") { Remove-Item "coverage.xml" -Force }
    if (Test-Path ".pytest_cache") { Remove-Item ".pytest_cache" -Recurse -Force }
}

# コマンド実行
switch ($Command) {
    "help" { Show-Help }
    "install" { Install-Dependencies }
    "test" { Run-Tests }
    "test-verbose" { Run-TestsVerbose }
    "test-coverage" { Run-TestsCoverage }
    "lint" { Run-Lint }
    "format" { Run-Format }
    "check" { Run-Check }
    "clean" { Clean-Files }
    default { 
        Write-Host "不明なコマンド: $Command" -ForegroundColor Red
        Show-Help 
    }
}

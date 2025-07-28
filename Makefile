.PHONY: test test-verbose test-coverage lint format check install clean help

# デフォルトターゲット
help:
	@echo "利用可能なコマンド:"
	@echo "  test          - テストを実行"
	@echo "  test-verbose  - 詳細出力でテストを実行"
	@echo "  test-coverage - カバレッジ付きでテストを実行"
	@echo "  lint          - コードのリンティング"
	@echo "  format        - コードフォーマット"
	@echo "  check         - フォーマットとリンティングのチェック"
	@echo "  install       - 依存関係のインストール"
	@echo "  clean         - 一時ファイルの削除"

# 依存関係のインストール
install:
	pip install --upgrade pip
	pip install -r requirements.txt

# テスト実行
test:
	python -m unittest discover -s tests -p "test_*.py"

test-verbose:
	python -m unittest discover -s tests -p "test_*.py" -v

test-coverage:
	coverage run -m unittest discover -s tests -p "test_*.py"
	coverage report -m
	coverage html

# リンティング
lint:
	flake8 . --count --statistics

# コードフォーマット
format:
	black .
	isort .

# フォーマットとリンティングのチェック（CIで使用）
check:
	black --check --diff .
	isort --check-only --diff .
	flake8 . --count --statistics

# 一時ファイルの削除
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf coverage.xml
	rm -rf .pytest_cache/

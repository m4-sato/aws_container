FROM python:3.11-slim

# 必要なシステムパッケージをインストール（curlやビルドツールなど）
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl build-essential && \
    rm -rf /var/lib/apt/lists/*

# Poetryのインストール（公式インストーラーを使用）
RUN curl -sSL https://install.python-poetry.org | python -

# PoetryをPATHに追加
ENV PATH="/root/.local/bin:$PATH"

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイル(pyproject.toml, poetry.lock)を先にコピーしてキャッシュを有効化
COPY pyproject.toml poetry.lock* ./

# 仮想環境を作成せず、グローバル環境に依存関係をインストールするよう設定
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# アプリケーションのソースコード全体をコンテナにコピー
COPY . .

# Streamlitのデフォルトポート8501を公開
EXPOSE 8501

# コンテナ起動時にStreamlitアプリを実行（エントリーポイントがapp.pyの場合）
CMD ["streamlit", "run", "take1.py", "--server.enableCORS", "false", "--server.address=0.0.0.0"]


<div align="center">

![Image](https://github.com/user-attachments/assets/fc6873fc-6017-424f-9004-93eca1dc53e3)

# openai-agents-sandbox

[![Python](https://img.shields.io/badge/Python-3.12.7-blue.svg)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-green.svg)](https://openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

## 🎯 概要
OpenAI Agents Sandbox - OpenAIのエージェント機能を実験するためのプロジェクト。

## 🚀 セットアップ手順

### ✅ 前提条件
- Python 3.12.7 以上
- uv パッケージマネージャー

### 💻 インストール

1. 仮想環境の作成と有効化:
```bash
# 仮想環境の作成
uv venv

# 仮想環境の有効化
source .venv/bin/activate
```

2. 必要なパッケージのインストール:
```bash
# openai-agentsのインストール
uv pip install openai-agents

# 環境変数用のpython-dotenvのインストール
uv pip install python-dotenv
```

3. 環境変数の設定:
```bash
# 環境変数の設定ファイルをコピー
cp example/.env.example example/.env

# .envファイルにOpenAI APIキーを設定
# OPENAI_API_KEY=あなたのAPIキーをここに設定
```

## 🔍 使用方法

exampleディレクトリに移動してサンプルコードを実行:

```bash
cd example
python async_hello_world.py
```

### 📝 実行例
このサンプルはプログラミングの再帰に関する詩的な応答を生成します:

```
Function calls itself,  
Base case stops the endless loop,  
Elegant solution.  

Problems split smaller,  
Each step a mirror of past,  
Stack builds, then unwinds.
```

## 🔧 トラブルシューティング

### ❓ よくある問題

1. モジュールが見つからないエラー:
```
ModuleNotFoundError: No module named 'dotenv'
```
解決策: python-dotenvパッケージをインストール
```bash
uv pip install python-dotenv
```

2. OpenAI APIエラー:
```
openai.BadRequestError: Error code: 400
```
解決策: .envファイルにOpenAI APIキーが正しく設定されていることを確認

3. APIキー未設定の警告:
```
OPENAI_API_KEY is not set, skipping trace export
```
解決策: .envファイルにOpenAI APIキーを設定してください

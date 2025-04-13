import os
import boto3
import streamlit as st

from dotenv import load_dotenv

load_dotenv()

# フロントエンドの記述
st.title("教えて! Bedrock")
question = st.text_input("質問を入力")
button = st.button("質問する")

# Bedrockクライアントを作成
kb = boto3.client("bedrock-agent-runtime")

# ボタンが押されたらナレッジベースを呼び出し
if button:

    # ナレッジベースを定義
    response = kb.retrieve_and_generate(
        input={"text": question},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId":os.getenv("KNOWLEDGE_ID"),
                "modelArn":os.getenv("MODEL_ARN")
                }
        }
    )
    # RAG結果を画面に表示
    st.write(response["output"]["text"])


import os
import streamlit as st
from langchain_aws import ChatBedrock
from langchain_aws.retrievers import AmazonKnowledgeBasesRetriever
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

load_dotenv()

# 検索手段を指定
retriever = AmazonKnowledgeBasesRetriever(
    knowledge_base_id=os.getenv("KNOWLEDGE_ID"),
    retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 10}},
)

# プロンプトのテンプレートを定義
prompt = ChatPromptTemplate.from_template(
    "以下のcontextに基づいて回答してください: {context} / 質問: {question}"
)

# LLMを指定
model = ChatBedrock(
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0",
    model_kwargs = {"max_tokens": 1000},
)

# チェーンを定義
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

# フロントエンドの記述
st.title("教えて! Bedrock")
question = st.text_input("質問を入力")
button = st.button("質問する")

# ボタンが押されたらチェーン実行結果を表示
if button:
    st.write(chain.invoke(question))
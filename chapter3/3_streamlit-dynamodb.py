import os
import streamlit as st
from langchain.globals import set_debug
from langchain_aws import ChatBedrock
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_community.chat_message_histories import DynamoDBChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langsmith import traceable
from dotenv import load_dotenv

# LangSmith の設定
load_dotenv()

# LangSmith環境変数を設定（getenvではなくenvironに設定する必要がある）
os.environ["LANGCHAIN_TRACING_V2"] = "true"  # getenvではなく、environに直接"true"を設定
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")  # APIキーが存在しない場合は空文字を設定
os.environ["LANGCHAIN_PROJECT"] = "bedrock-agent-monitoring"  # プロジェクト名を直接設定

# デバッグの有効化
set_debug(True)

# タイトル
st.title("Bedrock チャット")

# セッションIDを定義
if "session_id" not in st.session_state:
    st.session_state.session_id = "session_id"

# セッションに履歴を定義
if "history" not in st.session_state:
    st.session_state.history = DynamoDBChatMessageHistory(
        table_name="BedrockChatSessionTable", session_id=st.session_state.session_id
    )

# セッションにChainを定義
if "chain" not in st.session_state:
    # プロンプトを生成
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "あなたのタスクはユーザーの質問に明確に答えることです。"),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="human_message"),
        ]
    )

    # ChatBedrockを生成
    chat = ChatBedrock(
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0",
        model_kwargs = {"max_tokens": 1000},
        streaming = True,
    )

    # Chainを生成
    chain = prompt | chat
    st.session_state.chain = chain

# 履歴クリアボタンを画面表示
if st.button("履歴をクリア"):
    st.session_state.history.clear()

# メッセージを画面表示
for message in st.session_state.history.messages:
    with st.chat_message(message.type):
        st.markdown(message.content)

# チャット入力欄を定義
if prompt := st.chat_input("何でも聞いてください。"):
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # モデルの呼び出しと結果の画面表示
    with st.chat_message("assistant"):
        response = st.write_stream(
            st.session_state.chain.stream(
                {
                    "messages": st.session_state.history.messages,
                    "human_message": [HumanMessage(content=prompt)],
                },
                config={"configurable": {"session_id": st.session_state.session_id}},
            )
        )
    
    # 履歴に追加
    st.session_state.history.add_user_message(prompt)
    st.session_state.history.add_ai_message(response)

import nest_asyncio
import streamlit as st
from bs4 import BeautifulSoup
from langchain import hub
from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain_aws import ChatBedrock
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage, SystemMessage


nest_asyncio.apply()


# Webページを読み込む関数
def web_page_reader(url: str) -> str:
    loader = WebBaseLoader(url)
    content = loader.load()[0].page_content
    return content

# 検索ツールとWebページ読み込みツールの設定
search = DuckDuckGoSearchRun()
tools = [
    Tool(
        name="duckduckgo-search",
        func=search.run,
        description="このツールはユーザーから検索キーワードを受け取り、Web上の最新情報を検索します。"
    )
]

# チャットモデルの設定
chat = ChatBedrock(
    model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
    model_kwargs={"max_tokens": 1500},
    region_name="us-west-2"  # 必要なAWSリージョンを指定
)

prompt = hub.pull("hwchase17/react")

# エージェントの設定
agent = create_react_agent(chat, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

# Streamlitの設定
st.title("Bedrock React Agent チャット")
messages = [SystemMessage(content="あなたは質問に対して必ず日本語で回答します。")]

# ユーザー入力の処理
prompt = st.chat_input("何でも聞いてください")
if prompt:
    messages.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        result = agent_executor.invoke({"input": prompt})
        st.write(result["output"])
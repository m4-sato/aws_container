import os
from langchain.globals import set_debug
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

# LangSmith の設定
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["LANGCHAIN_PROJECT"] = "bedrock-agent-monitoring"
# デバッグの有効化
set_debug(True)

# ChatBedrockを生成
chat = ChatBedrock(
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0",
    model_kwargs = {"max_tokens": 1000},
    streaming = True,
)

# メッセージを定義
messages = [
    SystemMessage(content="あなたのタスクはユーザーの質問に明確に答えることです。"),
    HumanMessage(content="空が青いのはなぜですか？"),
]

for chunk in chat.stream(messages):
    print(chunk.content, end="", flush=True)

print("")


# # # モデル呼び出し
# response = chat.invoke(messages)

# print(response.content)
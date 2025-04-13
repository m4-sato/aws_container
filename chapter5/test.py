import os
import json
import uuid
import boto3
import streamlit as st
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from botocore.eventstream import EventStreamError

# LangChain imports
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_aws import BedrockChat
from langchain.chains import LLMChain
from langchain_community.callbacks import StreamlitCallbackHandler
from langsmith import traceable

load_dotenv()
# LangSmith の設定
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "bedrock-agent-monitoring"


def initialize_session():
    """セッションの初期設定を行う"""
    if "bedrock_client" not in st.session_state:
        st.session_state.bedrock_client = boto3.client("bedrock-runtime", region_name="us-west-2")
    
    if "agent_client" not in st.session_state:
        st.session_state.agent_client = boto3.client("bedrock-agent-runtime", region_name="us-west-2")
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "last_prompt" not in st.session_state:
        st.session_state.last_prompt = None
    
    if "llm" not in st.session_state:
        # Bedrock LLM設定
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"  # 使用するモデルのIDに変更
        st.session_state.llm = BedrockChat(
            model_id=model_id,
            client=st.session_state.bedrock_client,
            streaming=True,
            model_kwargs={"temperature": 0.7, "max_tokens": 2000}
        )
    
    return st.session_state.agent_client, st.session_state.session_id, st.session_state.messages, st.session_state.llm


def display_chat_history(messages):
    """チャット履歴を表示する"""
    st.title("わが家のAI技術顧問")
    st.text("画面下部のチャットボックスから何でも質問してね！")
    
    for message in messages:
        with st.chat_message(message['role']):
            st.markdown(message['text'])


def handle_trace_event(event):
    """トレースイベントの処理を行う"""
    if "orchestrationTrace" not in event["trace"]["trace"]:
        return
    
    trace = event["trace"]["trace"]["orchestrationTrace"]
    
    # 「モデル入力」トレースの表示
    if "modelInvocationInput" in trace:
        with st.expander("🤔 思考中…", expanded=False):
            input_trace = trace["modelInvocationInput"]["text"]
            try:
                st.json(json.loads(input_trace))
            except:
                st.write(input_trace)
    
    # 「モデル出力」トレースの表示
    if "modelInvocationOutput" in trace:
        output_trace = trace["modelInvocationOutput"]["rawResponse"]["content"]
        with st.expander("💡 思考がまとまりました", expanded=False):
            try:
                thinking = json.loads(output_trace)["content"][0]["text"]
                if thinking:
                    st.write(thinking)
                else:
                    st.write(json.loads(output_trace)["content"][0])
            except:
                st.write(output_trace)
    
    # 「根拠」トレースの表示
    if "rationale" in trace:
        with st.expander("✅ 次のアクションを決定しました", expanded=True):
            st.write(trace["rationale"]["text"])
    
    # 「ツール呼び出し」トレースの表示
    if "invocationInput" in trace:
        invocation_type = trace["invocationInput"]["invocationType"]
        
        if invocation_type == "AGENT_COLLABORATOR":
            # キー 'agentCollaboratorInvocationInput' が存在するか確認する
            if "agentCollaboratorInvocationInput" in trace["invocationInput"]:
                agent_input = trace["invocationInput"]["agentCollaboratorInvocationInput"]
                
                # .get() を使って安全にキーの値を取得する
                agent_name = agent_input.get("agentCollaboratorName", "不明なエージェント") 
                input_data = agent_input.get("input", {})
                input_text = input_data.get("text", "入力内容不明")

                with st.expander(f"🤖 サブエージェント「{agent_name}」を呼び出し中…", expanded=True):
                    st.write(input_text)
            else:
                st.warning(f"⚠️ AGENT_COLLABORATOR トレースで予期せぬ構造を検出しました。")
                try:
                    st.json(trace["invocationInput"])
                except:
                     st.write(trace["invocationInput"])

    # 「観察」トレースの表示
    if "observation" in trace:
        # .get() を使って安全に type を取得
        obs_type = trace["observation"].get("type")

        if obs_type == "KNOWLEDGE_BASE":
            # キー 'knowledgeBaseLookupOutput' が存在するか確認
            if "knowledgeBaseLookupOutput" in trace["observation"]:
                kb_output = trace["observation"]["knowledgeBaseLookupOutput"]
                # .get() を使って安全にアクセス
                retrieved_refs = kb_output.get("retrievedReferences", []) 
                with st.expander("🔍 ナレッジベースから検索結果を取得しました", expanded=False):
                    st.write(retrieved_refs)
            else:
                st.warning("⚠️ KNOWLEDGE_BASE 観察トレースで予期せぬ構造を検出しました。")
                try:
                    st.json(trace["observation"])
                except Exception as e:
                     st.write(f"観察トレース内容の表示中にエラー: {e}")
                     st.write(trace["observation"])

        elif obs_type == "AGENT_COLLABORATOR":
            # キー 'agentCollaboratorInvocationOutput' が存在するか確認
            if "agentCollaboratorInvocationOutput" in trace["observation"]:
                agent_output_data = trace["observation"]["agentCollaboratorInvocationOutput"]
                # .get() を使って安全にアクセス
                agent_name = agent_output_data.get("agentCollaboratorName", "不明なエージェント")
                output_content = agent_output_data.get("output", {})
                output_text = output_content.get("text", "出力内容不明")

                with st.expander(f"🤖 サブエージェント「{agent_name}」から回答を取得しました", expanded=True):
                    st.write(output_text)
            else:
                st.warning("⚠️ AGENT_COLLABORATOR 観察トレースで予期せぬ構造を検出しました。")
                try:
                    st.json(trace["observation"])
                except Exception as e:
                     st.write(f"観察トレース内容の表示中にエラー: {e}")
                     st.write(trace["observation"])
            
        else:
            if obs_type:
                st.warning(f"未対応の観察タイプ: {obs_type}")
            else:
                st.warning("観察トレースに 'type' キーが見つかりません。")
            try:
                st.json(trace["observation"])
            except Exception as e:
                st.write(f"観察トレース内容の表示中にエラー: {e}")
                st.write(trace["observation"])


@traceable
def process_with_langchain(llm, user_input, history):
    """LangChainを使用してプロンプトを処理する"""
    # システムプロンプト
    system_prompt = """
    あなたは「わが家のAI技術顧問」です。
    家庭内での技術的な質問に対して、親切で分かりやすい回答を提供してください。
    特にAI、プログラミング、IoT、家庭内ネットワークに関する質問に詳しく答えてください。
    難しい技術用語は避け、一般の方にも理解しやすい言葉で説明してください。
    """
    
    # チャット履歴をLangChain形式に変換
    chat_history = []
    for msg in history:
        if msg['role'] == 'human':
            chat_history.append(HumanMessage(content=msg['text']))
        elif msg['role'] == 'assistant':
            chat_history.append(AIMessage(content=msg['text']))
    
    # プロンプトテンプレートの作成
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        *[(msg.type, msg.content) for msg in chat_history],
        ("human", "{input}")
    ])
    
    # LLMチェーンの作成
    chain = prompt | llm
    
    # ストリーミング出力用のコールバックハンドラ
    st_callback = StreamlitCallbackHandler(st.empty())
    
    # チェーンを実行
    result = chain.invoke(
        {"input": user_input},
        config={"callbacks": [st_callback]}
    )
    
    return result.content


def invoke_bedrock_agent(client, session_id, prompt):
    """Bedrockエージェントを呼び出す"""
    load_dotenv()
    return client.invoke_agent(
        agentId=os.getenv("AGENT_ID"),
        agentAliasId=os.getenv("AGENT_ALIAS_ID"),
        sessionId=session_id,
        enableTrace=True,
        inputText=prompt,
    )


def handle_agent_response(response, messages):
    """エージェントのレスポンスを処理する"""
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        for event in response.get("completion"):
            if "trace" in event:
                handle_trace_event(event)
            
            if "chunk" in event:
                chunk = event["chunk"]["bytes"].decode()
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
        messages.append({"role": "assistant", "text": full_response})


def show_error_popup(exception_type):
    """エラーポップアップを表示する"""
    if exception_type == "dependencyFailedException":
        error_message = "【エラー】ナレッジベースのAurora DBがスリープしていたようです。数秒おいてから、ブラウザをリロードして再度お試しください🙏"
    elif exception_type == "throttlingException":
        error_message = "【エラー】Bedrockのモデル負荷が高いようです。1分待ってから、ブラウザをリロードして再度お試しください🙏（改善しない場合は、モデルを変更するか[サービスクォータの引き上げ申請](https://aws.amazon.com/jp/blogs/news/generative-ai-amazon-bedrock-handling-quota-problems/)を実施ください）"
    st.error(error_message)


def main():
    """メインのアプリケーション処理"""
    agent_client, session_id, messages, llm = initialize_session()
    display_chat_history(messages)
    
    if prompt := st.chat_input("例：画像入り資料を使ったRAGアプリを作るにはどうすればいい？"):
        messages.append({"role": "human", "text": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # モード選択: ここでBedrock AgentとLangChainベースのどちらかを選択可能
        use_agent = st.session_state.get("use_bedrock_agent", True)
        
        try:
            if use_agent:
                # Bedrock Agentを使用するモード
                response = invoke_bedrock_agent(agent_client, session_id, prompt)
                handle_agent_response(response, messages)
            else:
                # LangChainを使用するモード
                with st.chat_message("assistant"):
                    response = process_with_langchain(llm, prompt, messages[:-1])  # 最新のユーザー入力を除外
                    st.markdown(response)
                    messages.append({"role": "assistant", "text": response})
            
        except (EventStreamError, ClientError) as e:
            if "dependencyFailedException" in str(e):
                show_error_popup("dependencyFailedException")
            elif "throttlingException" in str(e):
                show_error_popup("throttlingException")
            else:
                raise e


# サイドバーでモード切替を追加
def sidebar():
    with st.sidebar:
        st.title("設定")
        st.session_state.use_bedrock_agent = st.checkbox(
            "Bedrock Agentを使用", 
            value=st.session_state.get("use_bedrock_agent", True),
            help="オフにするとLangChainベースのシンプルなチャットに切り替わります"
        )


if __name__ == "__main__":
    sidebar()
    main()
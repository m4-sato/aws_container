import os
import json
import uuid
import boto3
import streamlit as st
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from botocore.eventstream import EventStreamError

# Langfuse の設定
from langfuse import Langfuse
from langfuse.decorators import observe

# Langfuse 環境変数設定
os.environ["LANGFUSE_PUBLIC_KEY"] = ""
os.environ["LANGFUSE_SECRET_KEY"] = ""
os.environ["LANGFUSE_HOST"] = "https://your-self-hosted-instance.example.com"  # 自己ホストの URL を指定
os.environ["LANGFUSE_PROJECT"] = "bedrock-agent-monitoring"


def initialize_session():
    """セッションの初期設定を行う"""
    if "client" not in st.session_state:
        st.session_state.client = boto3.client("bedrock-agent-runtime", region_name="us-west-2")
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "last_prompt" not in st.session_state:
        st.session_state.last_prompt = None
    
    if "langfuse" not in st.session_state:
        # Langfuse クライアントの初期化
        st.session_state.langfuse = Langfuse(
            public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
            host=os.environ.get("LANGFUSE_HOST")
        )
    
    return st.session_state.client, st.session_state.session_id, st.session_state.messages, st.session_state.langfuse

def display_chat_history(messages):
    """チャット履歴を表示する"""
    st.title("わが家のAI技術顧問")
    st.text("画面下部のチャットボックスから何でも質問してね！")
    
    for message in messages:
        with st.chat_message(message['role']):
            st.markdown(message['text'])

def handle_trace_event(event, trace_id=None, langfuse=None):
    """トレースイベントの処理を行う"""
    if "orchestrationTrace" not in event["trace"]["trace"]:
        return
    
    trace = event["trace"]["trace"]["orchestrationTrace"]
    
    # 「モデル入力」トレースの表示と Langfuse への記録
    if "modelInvocationInput" in trace:
        with st.expander("🤔 思考中…", expanded=False):
            input_trace = trace["modelInvocationInput"]["text"]
            try:
                st.json(json.loads(input_trace))
                if langfuse and trace_id:
                    # Langfuse に入力をスパンとして記録
                    langfuse.span(
                        name="model_input",
                        start_time=None,
                        trace_id=trace_id,
                        input=input_trace
                    )
            except:
                st.write(input_trace)
    
    # 「モデル出力」トレースの表示と Langfuse への記録
    if "modelInvocationOutput" in trace:
        output_trace = trace["modelInvocationOutput"]["rawResponse"]["content"]
        with st.expander("💡 思考がまとまりました", expanded=False):
            try:
                thinking = json.loads(output_trace)["content"][0]["text"]
                if thinking:
                    st.write(thinking)
                else:
                    st.write(json.loads(output_trace)["content"][0])
                
                if langfuse and trace_id:
                    # Langfuse に出力をスパンとして記録
                    langfuse.span(
                        name="model_output",
                        start_time=None,
                        trace_id=trace_id,
                        output=output_trace
                    )
            except:
                st.write(output_trace)
    
    # 「根拠」トレースの表示と Langfuse への記録
    if "rationale" in trace:
        rationale_text = trace["rationale"]["text"]
        with st.expander("✅ 次のアクションを決定しました", expanded=True):
            st.write(rationale_text)
            
        if langfuse and trace_id:
            # Langfuse に根拠をスパンとして記録
            langfuse.span(
                name="rationale",
                start_time=None,
                trace_id=trace_id,
                input=rationale_text
            )
    
    # 「ツール呼び出し」トレースの表示と Langfuse への記録
    if "invocationInput" in trace:
        invocation_type = trace["invocationInput"]["invocationType"]
        
        if invocation_type == "AGENT_COLLABORATOR":
            # キー 'agentCollaboratorInvocationInput' が存在するか確認する
            if "agentCollaboratorInvocationInput" in trace["invocationInput"]:
                agent_input = trace["invocationInput"]["agentCollaboratorInvocationInput"]
                
                # .get() を使って安全にキーの値を取得する
                # キーが存在しない場合に備えてデフォルト値を設定
                agent_name = agent_input.get("agentCollaboratorName", "不明なエージェント") 
                input_data = agent_input.get("input", {}) # 'input' キーも存在しない可能性を考慮
                input_text = input_data.get("text", "入力内容不明") # 'text' キーも存在しない可能性を考慮

                with st.expander(f"🤖 サブエージェント「{agent_name}」を呼び出し中…", expanded=True):
                    st.write(input_text)
                
                if langfuse and trace_id:
                    # Langfuse にサブエージェント呼び出しをスパンとして記録
                    agent_span = langfuse.span(
                        name=f"agent_call_{agent_name}",
                        start_time=None,
                        trace_id=trace_id,
                        input=input_text
                    )
            else:
                # agentCollaboratorInvocationInput キーが存在しない場合の処理
                # (デバッグ用に警告と内容を表示するなど)
                st.warning(f"⚠️ AGENT_COLLABORATOR トレースで予期せぬ構造を検出しました。'agentCollaboratorInvocationInput' キーが見つかりません。")
                # 実際の invocationInput の内容を表示して確認
                try:
                    st.json(trace["invocationInput"])
                except:
                     st.write(trace["invocationInput"])

    # 「観察」トレースの表示と Langfuse への記録
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
                
                if langfuse and trace_id:
                    # Langfuse にナレッジベース検索をスパンとして記録
                    langfuse.span(
                        name="knowledge_base_lookup",
                        start_time=None,
                        trace_id=trace_id,
                        output=str(retrieved_refs)
                    )
            else:
                # キーが存在しない場合の処理
                st.warning("⚠️ KNOWLEDGE_BASE 観察トレースで予期せぬ構造を検出しました。")
                try:
                    st.json(trace["observation"]) # デバッグ用に内容表示
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
                
                if langfuse and trace_id:
                    # Langfuse にサブエージェント応答をスパンとして記録
                    langfuse.span(
                        name=f"agent_response_{agent_name}",
                        start_time=None,
                        trace_id=trace_id,
                        output=output_text
                    )
            else:
                # キーが存在しない場合の処理
                st.warning("⚠️ AGENT_COLLABORATOR 観察トレースで予期せぬ構造を検出しました。")
                try:
                    st.json(trace["observation"]) # デバッグ用に内容表示
                except Exception as e:
                     st.write(f"観察トレース内容の表示中にエラー: {e}")
                     st.write(trace["observation"])
        
        # obs_typeが KB でも AGENT でもない場合、または type キー自体がない場合
        else:
            if obs_type:  # obs_type に値があるか (None や "" でないか)
               st.warning(f"未対応の観察タイプ: {obs_type}")
            else: # obs_type が None や "" だった場合
               st.warning("観察トレースに 'type' キーが見つかりません、または値がありません。")
            # デバッグ用に内容表示
            try:
                st.json(trace["observation"])
            except Exception as e:
                st.write(f"観察トレース内容の表示中にエラー: {e}")
                st.write(trace["observation"])

@observe  # Langfuse トレースデコレータ
def invoke_bedrock_agent(client, session_id, prompt, langfuse=None):
    """Bedrockエージェントを呼び出す"""
    load_dotenv()
    
    # Langfuse でトレースを開始
    trace_id = None
    if langfuse:
        trace = langfuse.trace(
            name="bedrock_agent_invocation",
            user_id=session_id,
            input=prompt
        )
        trace_id = trace.id
    
    response = client.invoke_agent(
        agentId=os.getenv("AGENT_ID"),
        agentAliasId=os.getenv("AGENT_ALIAS_ID"),
        sessionId=session_id,
        enableTrace=True,
        inputText=prompt,
    )
    
    return response, trace_id

def handle_agent_response(response, messages, trace_id=None, langfuse=None):
    """エージェントのレスポンスを処理する"""
    with st.chat_message("assistant"):
        full_answer = ""
        for event in response.get("completion"):
            if "trace" in event:
                handle_trace_event(event, trace_id, langfuse)
            
            if "chunk" in event:
                answer = event["chunk"]["bytes"].decode()
                st.write(answer)
                full_answer += answer
        
        messages.append({"role": "assistant", "text": full_answer})
        
        # Langfuse でトレースを終了し、最終応答を記録
        if langfuse and trace_id:
            langfuse.update_trace(
                trace_id=trace_id,
                output=full_answer
            )

def show_error_popup(exception):
    """エラーポップアップを表示する"""
    if exception == "dependencyFailedException":
        error_message = "【エラー】ナレッジベースのAurora DBがスリープしていたようです。数秒おいてから、ブラウザをリロードして再度お試しください🙏"
    elif exception == "throttlingException":
        error_message = "【エラー】Bedrockのモデル負荷が高いようです。1分待ってから、ブラウザをリロードして再度お試しください🙏（改善しない場合は、モデルを変更するか[サービスクォータの引き上げ申請](https://aws.amazon.com/jp/blogs/news/generative-ai-amazon-bedrock-handling-quota-problems/)を実施ください）"
    st.error(error_message)

def main():
    """メインのアプリケーション処理"""
    client, session_id, messages, langfuse = initialize_session()
    display_chat_history(messages)
    
    if prompt := st.chat_input("例：画像入り資料を使ったRAGアプリを作るにはどうすればいい？"):
        messages.append({"role": "human", "text": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        try:
            response, trace_id = invoke_bedrock_agent(client, session_id, prompt, langfuse)
            handle_agent_response(response, messages, trace_id, langfuse)
            
        except (EventStreamError, ClientError) as e:
            if "dependencyFailedException" in str(e):
                show_error_popup("dependencyFailedException")
                # エラーも Langfuse に記録
                if langfuse:
                    langfuse.exception(
                        name="dependency_failed",
                        user_id=session_id,
                        message=str(e),
                        level="error"
                    )
            elif "throttlingException" in str(e):
                show_error_popup("throttlingException")
                # エラーも Langfuse に記録
                if langfuse:
                    langfuse.exception(
                        name="throttling",
                        user_id=session_id,
                        message=str(e),
                        level="error"
                    )
            else:
                # その他のエラーも Langfuse に記録
                if langfuse:
                    langfuse.exception(
                        name="unhandled_error",
                        user_id=session_id,
                        message=str(e),
                        level="error"
                    )
                raise e

if __name__ == "__main__":
    main()
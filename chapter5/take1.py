import os
import json
import uuid
import boto3
import streamlit as st
from dotenv import load_dotenv
from botocore.exceptions import ClientError
from botocore.eventstream import EventStreamError
import datetime # datetime をインポート

# Langfuse関連のインポート
from langfuse import Langfuse # Langfuse クラス本体のみインポート

# --- セッション初期化関数 ---
def initialize_session():
    """セッションの初期設定を行う"""
    # Bedrockクライアント初期化
    if "client" not in st.session_state:
        # リージョンは適切か確認してください
        st.session_state.client = boto3.client("bedrock-agent-runtime", region_name=os.getenv("AWS_REGION", "us-west-2"))

    # セッションID初期化
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    # メッセージリスト初期化
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Langfuseクライアントを初期化 (関数呼び出し)
    # initialize_langfuse関数はこの関数の前に定義されている必要がある
    langfuse = initialize_langfuse()

    print("Session initialized.") # セッション初期化完了ログ
    return st.session_state.client, st.session_state.session_id, st.session_state.messages, langfuse


# --- Langfuse クライアントの初期化 ---
def initialize_langfuse():
    """Langfuseクライアントを初期化する"""
    if "langfuse" not in st.session_state:
        load_dotenv() # 環境変数をロード
        try:
            langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
            langfuse_host = os.getenv("LANGFUSE_HOST")
            if not all([langfuse_public_key, langfuse_secret_key, langfuse_host]):
                 st.error("Langfuseの設定 (.envファイル: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST) が不足しています。")
                 st.stop()
            st.session_state.langfuse = Langfuse(
                public_key=langfuse_public_key,
                secret_key=langfuse_secret_key,
                host=langfuse_host,
            )
            st.session_state.langfuse.auth_check()
            print("Langfuse client initialized successfully.")
        except Exception as e:
            st.error(f"Langfuseクライアントの初期化に失敗しました: {e}")
            print(f"Langfuse initialization failed: {e}")
            st.stop()
    return st.session_state.langfuse

# --- Langfuse クライアントの初期化 (修正版) ---
def initialize_langfuse():
    """Langfuseクライアントを初期化する"""
    if "langfuse" not in st.session_state:
        load_dotenv() # 環境変数をロード
        try:
            langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
            langfuse_host = os.getenv("LANGFUSE_HOST")
            if not all([langfuse_public_key, langfuse_secret_key, langfuse_host]):
                 st.error("Langfuseの設定 (.envファイル: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST) が不足しています。")
                 st.stop()

            st.session_state.langfuse = Langfuse(
                public_key=langfuse_public_key,
                secret_key=langfuse_secret_key,
                host=langfuse_host,
            )
            st.session_state.langfuse.auth_check()
            print("Langfuse client initialized successfully.")

        except Exception as e:
            # --- エラーハンドリング修正 ---
            original_error_repr = repr(e) # エラーのrepr表現を取得 (より安全)
            print(f"Langfuse initialization failed! Original error repr: {original_error_repr}") # コンソールにreprを出力

            # Streamlitに表示するメッセージを作成 (文字化け対策)
            display_message = f"Langfuseクライアントの初期化に失敗しました。\n根本原因 (repr): {original_error_repr}"

            try:
                # Streamlitにエラー表示を試みる
                st.error(display_message)
            except Exception as display_err:
                # Streamlitへの表示自体でエラーが起きた場合
                print(f"Error displaying exception in Streamlit: {display_err}")
                # 代替メッセージを表示
                st.error("Langfuseクライアント初期化中にエラーが発生しました。詳細はコンソールログを確認してください。")

            # --- ここで st.stop() するのは変更なし ---
            st.stop()
            # --- ここまでエラーハンドリング修正 ---

    # 正常に初期化できた場合のみクライアントを返す
    # (st.stop()が呼ばれなかった場合)
    if "langfuse" in st.session_state:
        return st.session_state.langfuse
    else:
        # 通常ここには到達しないはずだが念のため
        print("Error: Langfuse client not found in session state after initialization attempt.")
        st.error("Langfuseクライアントの取得に失敗しました。")
        st.stop()

# --- チャット履歴表示関数 ---
def display_chat_history(messages):
    """チャット履歴を表示する"""
    # アプリケーションのタイトルなどをここで設定
    st.title("わが家のAI技術顧問")
    st.text("画面下部のチャットボックスから何でも質問してね！")
    print(f"Displaying {len(messages)} messages.") # 履歴表示ログ

    for message in messages:
        with st.chat_message(message['role']):
            st.markdown(message['text'])

# --- LangfuseにSpanを記録するトレースイベントハンドラ ---
# (定義はしておくが、まだ呼び出されない)
def handle_trace_event_with_langfuse(event, trace):
    """トレースイベントの処理を行い、LangfuseにSpanとして記録する"""
    if "orchestrationTrace" not in event.get("trace", {}).get("trace", {}):
        return
    bedrock_trace = event["trace"]["trace"]["orchestrationTrace"]
    span_name = "unknown_orchestration_step"
    span_input = None
    span_output = None
    span_metadata = {"bedrock_trace_event": bedrock_trace}
    start_time = datetime.datetime.now(datetime.timezone.utc)

    # (詳細な表示・解析ロジックは省略せずに入れておく)
    # ... (以前のコードの `handle_trace_event_with_langfuse` の中身をここに記述) ...
    # --- Streamlit 表示 & Span情報抽出ロジック ---
    if "modelInvocationInput" in bedrock_trace:
        span_name = "model_invocation"
        span_input = bedrock_trace["modelInvocationInput"]
        input_text_for_display = span_input.get("text", str(span_input)) if isinstance(span_input, dict) else str(span_input)
        if isinstance(span_input, dict):
            span_metadata["model_id"] = span_input.get("modelId", "N/A")
            span_metadata["traceId"] = span_input.get("traceId", "N/A")
        with st.expander("🤔 思考中…", expanded=False): # この段階では表示されないはず
            try:
                parsed_input = json.loads(input_text_for_display)
                st.json(parsed_input)
            except (json.JSONDecodeError, TypeError):
                st.write(input_text_for_display)
        if "modelInvocationOutput" in bedrock_trace:
            span_output = bedrock_trace["modelInvocationOutput"]
            output_trace_for_display = span_output.get("rawResponse", span_output) if isinstance(span_output, dict) else span_output
            if isinstance(span_output, dict):
                 span_metadata["output_traceId"] = span_output.get("traceId", "N/A")
            with st.expander("💡 思考がまとまりました", expanded=False): # この段階では表示されないはず
                output_text = "Output could not be parsed."
                try:
                    # ... (以前の出力解析ロジック) ...
                    if isinstance(output_trace_for_display, dict) and "content" in output_trace_for_display:
                        content_str = output_trace_for_display["content"]
                        content_data = json.loads(content_str)
                        if isinstance(content_data, dict) and "content" in content_data and isinstance(content_data["content"], list) and len(content_data["content"]) > 0 and "text" in content_data["content"][0]:
                            output_text = content_data["content"][0]["text"]
                        elif isinstance(content_data, dict) and "text" in content_data:
                             output_text = content_data["text"]
                        else:
                            output_text = json.dumps(content_data, indent=2, ensure_ascii=False)
                    elif isinstance(output_trace_for_display, str):
                        output_text = output_trace_for_display
                    else:
                         output_text = json.dumps(output_trace_for_display, indent=2, ensure_ascii=False)
                except Exception as e:
                    st.warning(f"モデル出力の解析中にエラー: {e}")
                    output_text = str(output_trace_for_display)
                st.write(output_text)
    elif "rationale" in bedrock_trace:
        span_name = "rationale"
        span_output = bedrock_trace["rationale"]
        rationale_text = span_output.get("text", "No rationale text found.") if isinstance(span_output, dict) else str(span_output)
        if isinstance(span_output, dict):
            span_metadata["traceId"] = span_output.get("traceId", "N/A")
        with st.expander("✅ 次のアクションを決定しました", expanded=True): # この段階では表示されないはず
            st.write(rationale_text)
    elif "invocationInput" in bedrock_trace:
        # ... (他のトレースタイプの処理も同様に記述) ...
        span_input = bedrock_trace["invocationInput"]
        invocation_type = span_input.get("invocationType") if isinstance(span_input, dict) else None
        span_metadata["invocation_type"] = invocation_type
        if isinstance(span_input, dict):
             span_metadata["traceId"] = span_input.get("traceId", "N/A")
        if invocation_type == "AGENT_COLLABORATOR":
             # ...
             pass # Placeholder, expand later
        elif invocation_type == "KNOWLEDGE_BASE":
             # ...
             pass # Placeholder, expand later
        elif invocation_type == "ACTION_GROUP":
             # ...
             pass # Placeholder, expand later
        else:
             # ...
             pass # Placeholder, expand later
    elif "observation" in bedrock_trace:
        # ... (observationの処理も同様に記述) ...
        span_name = "observation"
        span_output = bedrock_trace["observation"]
        obs_type = span_output.get("type") if isinstance(span_output, dict) else None
        span_metadata["observation_type"] = obs_type
        if isinstance(span_output, dict):
             span_metadata["traceId"] = span_output.get("traceId", "N/A")
        if obs_type == "KNOWLEDGE_BASE":
             # ...
             pass # Placeholder, expand later
        elif obs_type == "AGENT_COLLABORATOR":
             # ...
             pass # Placeholder, expand later
        else:
             # ...
             pass # Placeholder, expand later
    else:
        st.warning(f"未処理のOrchestration Traceキー: {list(bedrock_trace.keys())}")
        try: st.json(bedrock_trace)
        except: st.write(bedrock_trace)
        span_name = "unknown_orchestration_event"
        span_input = bedrock_trace

    # Langfuse Span を記録
    try:
        input_payload = json.dumps(span_input, ensure_ascii=False, default=str) if isinstance(span_input, (dict, list)) else str(span_input) if span_input is not None else None
        output_payload = json.dumps(span_output, ensure_ascii=False, default=str) if isinstance(span_output, (dict, list)) else str(span_output) if span_output is not None else None
        serializable_metadata = json.loads(json.dumps(span_metadata, ensure_ascii=False, default=str))
        trace.span(
            name=span_name,
            input=input_payload,
            output=output_payload,
            metadata=serializable_metadata,
            start_time=start_time,
            end_time=datetime.datetime.now(datetime.timezone.utc)
        )
    except Exception as e:
         st.error(f"LangfuseへのSpan記録中にエラー ({span_name}): {e}")
         print(f"Error logging span {span_name}: {e}")
         print(f"Span Input Data: {span_input}")
         print(f"Span Output Data: {span_output}")
         print(f"Span Metadata: {span_metadata}")

# --- Bedrockエージェント呼び出し関数 ---
# (定義はしておくが、まだ呼び出されない)
def invoke_bedrock_agent(client, session_id, prompt):
    """Bedrockエージェントを呼び出す"""
    load_dotenv()
    agent_id = os.getenv("AGENT_ID")
    agent_alias_id = os.getenv("AGENT_ALIAS_ID")
    if not agent_id or not agent_alias_id:
        st.error("AGENT_ID または AGENT_ALIAS_ID が環境変数に設定されていません。")
        st.stop()
    print(f"Invoking Bedrock Agent: {agent_id} ({agent_alias_id})") # 呼び出しログ
    return client.invoke_agent(
        agentId=agent_id,
        agentAliasId=agent_alias_id,
        sessionId=session_id,
        enableTrace=True,
        inputText=prompt,
    )

# --- エージェント応答処理 ---
# (定義はしておくが、まだ呼び出されない)
def handle_agent_response_for_langfuse(response, messages, generation, trace):
    """エージェントのレスポンスを処理し、Langfuseにイベントを記録する"""
    full_answer = ""
    agent_traces_collected = []
    print("Handling agent response...") # 処理開始ログ

    with st.chat_message("assistant"):
        full_response_container = st.empty()
        current_display_content = ""
        try:
            completion_events = response.get("completion", [])
            if completion_events is None:
                 completion_events = []
            for event in completion_events:
                if "trace" in event:
                    handle_trace_event_with_langfuse(event, trace)
                    agent_traces_collected.append(event["trace"])
                if "chunk" in event:
                    try:
                        answer_chunk = event["chunk"]["bytes"].decode("utf-8")
                        full_answer += answer_chunk
                        current_display_content += answer_chunk
                        full_response_container.markdown(current_display_content + "▌")
                    except Exception as decode_err:
                         st.warning(f"レスポンスチャンクのデコードエラー: {decode_err}")
                         print(f"Chunk decode error: {decode_err}, chunk data: {event['chunk']}")
            full_response_container.markdown(current_display_content)
            if full_answer:
                messages.append({"role": "assistant", "text": full_answer})
            print(f"Agent response processed. Answer length: {len(full_answer)}") # 処理完了ログ

            generation.end(
                output=full_answer,
                end_time=datetime.datetime.now(datetime.timezone.utc),
                metadata={
                    **(generation.metadata or {}),
                    "agent_traces_collected_count": len(agent_traces_collected),
                }
            )
        except Exception as e:
            error_msg = f"レスポンス処理中にエラーが発生しました: {e}"
            st.error(error_msg)
            print(f"Error during response processing: {e}")
            generation.end(
                output={"error": str(e), "partial_answer": full_answer},
                level="ERROR",
                status_message=str(e),
                end_time=datetime.datetime.now(datetime.timezone.utc),
                 metadata={
                    **(generation.metadata or {}),
                    "agent_traces_collected_count": len(agent_traces_collected),
                    "processing_error": error_msg
                }
            )
    return full_answer

# --- エラーポップアップ表示関数 ---
# (定義はしておくが、まだ呼び出されない)
def show_error_popup(exception_type):
    """エラーポップアップを表示する"""
    error_message = f"【エラー】予期せぬエラーが発生しました: {exception_type}"
    # ...(以前のエラーメッセージ分岐)...
    if exception_type == "dependencyFailedException": error_message = "【エラー】依存関係エラー（DB等）が発生。リロードしてください🙏"
    elif exception_type == "throttlingException": error_message = "【エラー】リクエストスロットリング。リロードしてください🙏（クォータ確認）"
    elif exception_type == "validationException": error_message = "【エラー】リクエスト無効。入力や設定を確認。"
    elif exception_type == "resourceNotFoundException": error_message = "【エラー】リソース（Agent ID等）が見つかりません。設定確認。"
    elif exception_type == "internalServerException": error_message = "【エラー】Bedrock内部エラー。再試行してください。"
    elif exception_type == "serviceQuotaExceededException": error_message = "【エラー】サービス上限超過。"
    st.error(error_message)

# --- メイン処理 ---
def main():
    """メインのアプリケーション処理"""
    print("Main function started.") # main開始ログ
    try:
        # セッション初期化を呼び出す
        client, session_id, messages, langfuse = initialize_session()
    except Exception as init_err:
        print(f"Initialization failed in main: {init_err}")
        st.error(f"初期化中にエラーが発生しました: {init_err}") # エラーを画面にも表示
        return # アプリケーション実行を中断

    # チャット履歴表示を呼び出す
    display_chat_history(messages)

    # --- チャット入力とBedrock/Langfuse連携部分はまだコメントアウト ---
    if prompt := st.chat_input("例：画像入り資料を使ったRAGアプリを作るにはどうすればいい？"):
        messages.append({"role": "human", "text": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
    
        trace = langfuse.trace(
            name="bedrock-agent-chat-v3",
            user_id="streamlit-user-01",
            session_id=session_id,
            metadata={
                "environment": os.getenv("APP_ENV", "development"),
                "agent_id": os.getenv("AGENT_ID"),
                "agent_alias_id": os.getenv("AGENT_ALIAS_ID"),
            },
            tags=["streamlit", "bedrock-agent"]
        )
        print(f"Langfuse Trace created: {trace.id}")
    
        generation_metadata = {
            "bedrock_session_id": session_id,
            "streamlit_session_id": st.session_state.session_id
        }
        generation = trace.generation(
            name="agent-invocation",
            input=prompt,
            model=f"bedrock-agent:{os.getenv('AGENT_ID')}",
            model_parameters={
                "agentAliasId": os.getenv("AGENT_ALIAS_ID"),
                "enableTrace": True,
            },
            metadata=generation_metadata,
            start_time=datetime.datetime.now(datetime.timezone.utc)
        )
        print(f"Langfuse Generation created: {generation.id}")
    
        try:
            response = invoke_bedrock_agent(client, session_id, prompt)
            handle_agent_response_for_langfuse(response, messages, generation, trace)
    
        except (EventStreamError, ClientError) as e:
            # ... (エラーハンドリング) ...
            pass
        except Exception as e:
             # ... (エラーハンドリング) ...
             pass
        finally:
            try:
                langfuse.flush()
                print("Langfuse data flushed.")
            except Exception as e:
                st.warning(f"Langfuseへのデータ送信中にエラー: {e}")
                print(f"Error flushing Langfuse data: {e}")
    print("Main function finished.") # main終了ログ (この段階ではすぐ終わる)

if __name__ == "__main__":
    # 最小テストページのコードは削除
    # st.set_page_config(layout="wide")
    # st.title("最小テストページ")
    # st.write("このメッセージが見えれば、Streamlit自体は動作しています。")
    # print("最小テストページのコードが実行されました。")

    # main関数を呼び出す
    main()
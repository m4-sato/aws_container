import json
import boto3

# Bedrockクライアントの作成
bedrock_runtime = boto3.client("bedrock-runtime")

# リクエストボディを定義
body = json.dumps(
    {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": "Bedrockってどういう意味？",
            }
        ],
    }
)

#モデルの定義
modelId = "anthropic.claude-3-sonnet-20240229-v1:0"

# HTTPヘッダーを定義
accept = "application/json"
contentType = "application/json"

# レスポンスを取得
response = bedrock_runtime.invoke_model(body=body, modelId=modelId, accept = accept, contentType=contentType)
response_body = json.loads(response.get("body").read())
answer = response_body["content"][0]["text"]

print(answer)
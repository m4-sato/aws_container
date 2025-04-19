# aws_container

## 事前準備

### GitHubからSSH経由でクローン
- SSHキーの作成

```bash
ssh-keygen -t ed25519 -C "youremail@test.com"
```

- 公開鍵の登録

```bash
cat ~/.ssh/id_ed25519.pub
```

- GitHubのSSHキーへ登録

- GitHubへの接続確認

```bash
ssh -T git@github.com
```

- Gitディレクトリへ移動、その後GitHubからクローン

```bash
git clone git@github.com:m4-sato/aws_container.git
```

## Docker コマンド
- イメージの作成
```bash
docker image build -t myapp:v1 .
```

- イメージ情報の表示
```bash
docker image ls
```

- イメージ情報の削除
```bash
docker image rm <image ID> 
```

- イメージタグの追加
```bash
docker image tag myapp:v1 myapp:20210701
```

- レジストリへのイメージ保存
```bash
docker image push myapp:v1
```

- レジストリからのイメージの取得(docker image pull)

```bash
docker image pull myapp:v1
```

- コンテナの実行
```bash
docker container run -d -p 80:80 myapp:v1
```

- コンテナの起動状態の確認
```bash
docker container ls
```

- ログの確認
```bash
docker container logs 101b5647431d
```

- 実行中のコンテナに関するコマンド実行
```bash
docker container exec -it 101b5647431d /bin/sh
```

- コンテナの停止
```bash
docker container stop 101b5647431d
```

- ローカル環境での検証
```bash
docker build -t my-app .
```

```bash
docker run -p 8501:8501 \
  -v $(pwd):/app \
  -e AWS_ACCESS_KEY_ID=<IAM Your ACCESS KEY> \
  -e AWS_SECRET_ACCESS_KEY=<IAM Your SECRET KEY> \
  -e AWS_DEFAULT_REGION=us-west-2 \
  my-app
```

## 参考記事
- [Bedrock FastAPI& AWS Lambda Web Adapter](https://github.com/awslabs/aws-lambda-web-adapter/tree/main/examples/bedrock-agent-fastapi-zip)
- [Bedrock Agent 設定Tips](https://aws.amazon.com/jp/blogs/news/agents-for-amazon-bedrock-is-now-available-with-improved-control-of-orchestration-and-visibility-into-reasoning/)
- [チャンク検証](https://techcommunity.microsoft.com/t5/ai-azure-ai-services-blog/azure-ai-search-outperforming-vector-search-with-hybrid/ba-p/3929167)
- [Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html)

## 参考論文
- [ReAct](https://arxiv.org/abs/2210.03629)
- [Zero Plus FewShot CoT](https://arxiv.org/abs/2205.11916)
- [Multi Agent Debate](https://arxiv.org/abs/2305.19118)

## 参考書
- [Bedrockサンプルコード](https://github.com/minorun365/bedrock-book)

## プロンプトエンジニアリング
- Claude 版
  - [公式サイト](https://docs.anthropic.com/claude/docs/prompt-engineering)

## Bedrock Function Calling (Tool use)
- [Bedrock サイト](https://docs.aws.amazon.com/bedrock/latest/userguide/tool-use.html)


## AI エージェント
- Agents for Amazon Bedrockの仕組み
  - ベースプロンプト
    - ユーザーからの入力や基盤モデルの出力処理
    - 基盤モデルやアクショングループ、ナレッジベース間の調整
    - レスポンスをユーザーに返却する方法
  - ベースプロンプトテンプレート
    - 前処理
      ユーザーの入力をカテゴリーA~Eに分類するエージェントの設定を定義する
    - オーケストレーション
    　ユーザーの入力に応えるためにアクショングループなどのツールを呼び出すエージェントの設定と、回答にあたってのガイドラインを定義する。
    - ナレッジベースの応答生成
    　ナレッジベースの検索結果を用いてユーザーの入力に応えるエージェントの設定を定義する。
    - 後処理
    　エージェントが最終応答をどのようにフォーマットしてエンドユーザーに提示するかを定義する。
  - アクショングループ利用時のガイドライン
    - APIの数
    　少数の入力パラメータを備えた、3~5つのAPI数に留める
    - API設計
    　冪等性の確保など、APIを設計する際の一般的なベストプラクティスに従う
    - API呼び出しの検証
    　LLMはハルシネーションを起こす可能性があるため、全てのAPI呼び出しに対して徹底的意見称する。
  - 対応モデルとリージョン
    [AWS Rejions](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-regions.html)
  - 料金
    - InvokeAgentsメソッド:無料 
    - InvokeModelメソッド:有料 

- [各プロバイダーが提供するAgent List](https://github.com/e2b-dev/awesome-ai-agents)

### データソース
- [ファイル1](https://www.jpx.co.jp/corporate/investor-relations/ir-library/financial-info/J_ER_JPX_Q3FY2023.pdf)
- [ファイル2](https://www.jpx.co.jp/corporate/investor-relations/ir-library/financial-info/J_ER_JPX_Q2FY2023.pdf)

## トークン目安
- 8Kトークン:ブログ記事1本程度
- 16Kトークン:論文1本程度
- 100Kトークン:文庫本1本程度

## Bedrockの特徴
- 対応リージョン
  - Bedrockのすべての機能が使えるのは以下2つのリージョンのみ
    - 「バージニア北部」
    - 「オレゴン」
- 料金
  - オンデマンド
  - プロビジョンドスループット
  →検証用や小規模開発の場合にはまずはオンデマンド（従量課金）から試す！
  →オンデマンドで利用している時、モデルへのリクエストが多くエラーが発生するケースがあり。その場合はアプリ側でリトライ等のエラーハンドリングを実装したり、複数のリージョンのモデルを併用して負荷分散したり、非同期処理などのアーキテクチャ的な工夫が必要。
- Bedrock モデルID, モデルリソース名, モデル名
```bash
aws bedrock list-foundation-models --query "modelSummaries[*].[modelId, modelArn, modelName]" --output table --region us-east-2
```

### Lambdaレイヤーの作成方法
```bash
docker run \
--rm --platform linux/amd64 \
-v $PWD/python:/python \
--user $(id -u):$(id -g) \
python:3.9 pip install -t python langchain==0.2.0 langchain-aws==0.1.4 langchain-community==0.2.0 python-dateutil==2.8.2 pydantic pydantic-core
```

```bash
zip -r langchain-layer-take2.zip python > /dev/null
```

```bash
aws lambda publish-layer-version \
  --layer-name "lambda-layer-amd64" \
  --compatible-runtimes python3.9 \
  --compatible-architectures x86_64 \
  --zip-file fileb://langchain-layer-take1.zip --no-cli-pager
```

```bash
aws s3 cp langchain-layer-take2.zip s3://bedrock-docs-agent-20250407/
```

```bash
aws lambda publish-layer-version \
  --layer-name lambda-layer-take2 \
  --description "My python libs" \
  --content S3Bucket=bedrock-docs-agent-20250407,S3Key=langchain-layer-take2.zip \
  --compatible-runtimes python3.9
```

```bash
aws lambda publish-layer-version --layer-name langchain-layer --description "My python libs" --zip-file fileb://langchain-layer.zip --compatible-runtimes "python3.9"
```

### RAGアーキテクチャ&コスト管理
- アプリケーション
  - Pythonプログラムのホスト
    - AWS Lambda
    - Amazon ECS 
- 埋め込みモデル
  - Cohere Embed
  - Amazon Titan Text Embeddings V2
  - Amazon Titan Embeddings G1 -Text
- 検索対象
  - ベクトルDB
    - Amazon OpenSearch Serverless
      - Agentビルダーでナレッジベースを追加するとこのサービスが勝手に立ち上がる
        →Pineconeを使用してコストの節用
      - 閉域接続　　　
        https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-create.html
    - Amazon OpenSearch Service
      - セマンティック検索に活用
      - オープンソースの検索スイート「OpenSearch」をAWS上でマネージドに提供するサービス。
      - 検索エンジンとインデックスを内包した検索サービスという位置付けのAWSサービスですが、ベクトルデータの保存・検索にも利用可能
      - 「ドメイン」と呼ばれる抽象リソースを作成することで、その中にAWSが管理するOpenSearchクラスターが自動セットアップされます。
      - openSearch2.9では「ニューラル検索」という機能がサポート（「クエリのベクトル変換」と「LLMによる回答生成」を完結させることができる）
      - このニューラル検索で利用する埋め込みモデルやLLMとして、BedrockやAmazon SageMakerのモデルをMLコネクタで統合する「リモート推論」も利用可能
      - [LangChain | OpenSearch](https://python.langchain.com/docs/integrations/vectorstores/opensearch/)
    - **Amazon Aurora** & Amazon RDS
      - 両サービスが互換性の持つPostgreSQLでは、「pgvector」というベクトルデータを取り扱うための拡張機能あり
        →Auroraの方はServerlessオプションが存在するため、DBアクセスが少ない時は自動的にスケールダウンして利用コストの節約を図ることが可能
      - **Aurora**
        互換性のあるDBエンジンはMySQL及びPostgreSQL
      - [langChain | PGVector](https://python.langchain.com/docs/integrations/vectorstores/pgvector/)
    - Amazon DocumentDB
      - ドキュメントDB指向型　MongoDBと互換性あり
      - JSONのような形式のデータをいくつもの格納し、スキーマを固定せずに柔軟に扱える点。
      - [Amazon Document DB | LangChain](https://python.langchain.com/docs/integrations/vectorstores/documentdb/)
    - Amazon MemoryDB for Redis
      - インメモリDBサービスの一つ
      - プレビュー版であるため高精度なベクトルDBを利用したい場合はRedis Enterprise Cloudの使用を検討
      - Redisソフトウェアと互換性あり「NoSQL」
      - [Redis | LangChain](https://python.langchain.com/docs/integrations/vectorstores/redis/)
    - Pinecone(ベクトルDB/AWS Marketplace製品)
      - Knowledge basesのベクトルDBとしてサポートされている。(RAGパイプラインの実装を速やかに行える)
      - マネージドなベクトルDBサービス。
      - API経由で簡単に使える。
      - 無料版はindexが5件に制限
      - キャパシティ
        - ポッド
        - サーバーレス
      - AWS PrivateLinkによる閉域接続もプレビュー可能（ENterpriseプランで利用可能）
      - [Pinecone | LangChain](https://python.langchain.com/docs/integrations/vectorstores/pinecone/)
    - Redis Enterprise Cloud
      - インメモリDBサービスの一つ
      - Redisソフトウェアと互換性あり「NoSQL」
      - Knowledge basesに対応していることもRedis Enterprise Cloudのメリットの一つ
      - [Redis Cloud Integration With Amazon Bedrock Now Available | Redis](https://redis.io/blog/amazon-bedrock-integrration-with-redis-enterprise/)
    - MongoDB Atlas(AWS Marketplace製品)
      - ドキュメントDB指向型　MongoDBと互換性あり
      - AWS PrivateLinkによる閉域接続もプレビュー可能（ENterpriseプランで利用可能）
      - Knowledge basesに対応
      - [Build RAG applications with MongoDB Atlas, now available in Knowledge Bases for Amazon Bedrock | AWS News Blog](https://aws.amazon.com/jp/blogs/aws/build-rag-applications-with-mongodb-atlas-now-available-in-knoledge-bases-for-amazon-bedrock/)
  - その他
    - Amazon Kendra
      - エンタープライズ検索
      - 社内にあるさまざまな種類のデータリソースを横断して検索可能
      - 機械学習を活用したインテリジェントな検索を提供
      - 「Retrieve」APIが登場、最大200トークンの抜粋文書を100件まで取得可能
      - [Kendra | LangChain](https://python.langchain.com/docs/retrievers/amazon_kendra_retriever/)
      - Kendraの特徴として、AWSサービス及びサードパーティーを含めた多数のデータソースを検索対象にできること、及び多数のコネクタ（AWS社製のものだけで33種類）が用意されていることが挙げられる。
        - ウェブクローラー（Webサイト内を検索）
        - AWSサービス：S3,　RDS, FSx
        - 他社サービス：Confluence, OneDrive, Teams, GitHub, Gmail, Slack
      - **利用料金が比較的高め**
      - [Amazon kendraの利用料金](https://aws.amazon.com/jp/kendra/pricing/)
    - Amazon DynamoDB
      - サーバレスDB
      - NoSQL
      - キーバリュー型
      - **「ゼロETL統合」機能**
      - [AWSブログ](https://aws.amazon.com/jp/blogs/amazon-dynamodb-zero-etl-integration-with-amazon-opensearch-service-is-now-generally-available/)
    - Amazon S3
      - ベクトルDBではない
      - アーキテクチャを工夫すればRAGのベクトルデータを保管する用途にも利用
      - [Building aserverless document chat with AWS lambda and Amazon Bedrock | AWS Compute Blog](https://aws.amazon.com/jp/blogs/compute/building-a-serverless-document-chat-with-aws-lambda-and-amazon-bedrock/)
- LLM
  - Anthropic Claudeシリーズ
  - Amazon Titan Text G1 -Premier

### knowledge basesのクエリ設定
- 詳細クエリ設定
  - 検索タイプ
    - セマンティック検索と全文検索の結果を良いとこどりした「ハイブリッド検索」が可能
    - 「overrideSearchType」パラメーターで指定
    - [参考資料](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent-runtime_Retrieve.html)
  - 推論パラメーター
    - RetrieveAndGenerateメソッド　「inferenceConfig」フィールド内に各パラメーターの値を指定
  - ソースチャンクの最大数
    - ドキュメントの検索結果として最大100件のチャンクを取得
    - Retrieveメソッド　及び　retrieveAndGenerateメソッド　で　「numberOfResults」パラメーターの値を指定することで、取得件数を調整
    - 最適な取得件数に関する一般的な値は存在しないので、実際に回答品質やレスポンス時間を検証しながら、システムに合わせてチューニングすることが必要
  - メタデータによるフィルター
    あらかじめドキュメントにメタデータを付与して検索対象を絞り込むことが可能
  - プロンプトテンプレート
  - ガードレール
  - [参考資料](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-test-config.html)

- 利用料金
  - knowledge bases自体は無料で利用できますが、ナレッジベースから利用したモデルとベクトルDBの利用料金は発生。
  - [Bedrock料金表](https://aws.amazon.com/jp/bedrock/pricing)

### RAGアーキテクチャ例
1. とりあえずお試し
  - ECS
  - Bedrock(Knowledge bases)
  - S3
  - Pinecone Serverless
  - セキュリティ対策
    - Aurora Serverlessのクラスターを構築してknowledge basesのベクトルストアに指定することも可能
2. 品質重視
  - OpenSearch Serverlessの「ハイブリッド検索」機能を用いるパターン
  - その他、上記に同じ
  - overrideSearchTypeパラメーターの値にHYBRIDを指定
  - 日本語に適したアナライザーを適用
  - [日本語性能を向上させる技術検証](https://www.fsi.co.jp/blog/10661/)
  - Tips
    - 図入りドキュメントをRAGに活用するコツ
3. **データソースとの接続性を重視**
  - knowledge basesを利用する場合、データソースはS3バケットに配置する必要があるため、検索対象にしたいプラットフォームによっては
    、S3バケットへのデータ配置がしづらい場合がある。
    →その場合、Kendraの利用を検討
  - WebクローラーやAWS内外の多数のデータソースに対応したコネクタがあること。
  - ex) Microsoft SharePoint Online Connector
  - 弱点取得可能なデータが検索1件あたり最大200トークンと情報量がやや少なめ。

### RAGの品質向上の工夫
- チャンクサイズの調整
- メタデータの追加
- リランク
- RAGフュージョン
 - [rag-fusion | LangChain](https://python.langchain.com/v0.1/docs/templates/rag-fusion/) 
- Rewrite-Retrieve-Read
 - [rewrite_retrieve_read | LangChain](https://python.langchain.com/v0.1/docs/templates/rewrite-retrieve-read/) 
- HyDE
 - [hyde | LangChain](https://python.langchain.com/v0.1/docs/templates/hyde/) 
 - [Amazon Kendra Amazon Bedrock で構築したRAGシステムに対するAdvanced RAG手法の精度寄与検証](https://aws.amazon.com/jp/blogs/news/verifying-the-accuracy-contribution-of-advanced-rag-methods-on-rag-systems-built-with-amazon-kendra-and-amazon-bedrock/)

- RAGの評価ツール
  - Ragas
    [Customise models - Ragas](https://docs.ragas.io/en/stable/howtos/customizations/customize_models/#aws-bedrock)
  - LangSmith
    - SLAの提供
    - トレーシング（コスト管理）、評価、モニタリング、プロンプト管理
  - Lansfuse
    クラウド版とself host版がある[Langfuse GitHub](https://langfuse.com/docs/integrations/langchain/tracing)
    - [AWS Bedrock & Langfuse記事](https://www.docswell.com/s/kawara-y/Z4VRPG-2025-03-24-212139#p1)
  - [LangSmith VS Langfuse](https://langfuse.com/faq/all/langsmith-alternative)


### カスタムモデル（ファインチューニングと継続的な事前トレーニング）
1. ファインチューニング
2. 継続的な事前トレーニング

1. ファインチューニング
- Inputデータ
  - ラベル付きのデータセット
    - `prompt`:Bedrockって何？
       →`completion`:AWSの生成AIサービスです。
       →特定タスクの精度を高められる。
  - jsonl形式
  - データ量は数百件以上が目安
- 実行可能なリージョンと対象のモデル
  - リージョン
    - バージニア北部
    - オレゴン
  - モデル
    - Claude
    - Amazon Titan
    - Cohere Command
    - Meta Llama2
- コスト
  プロビジョンドスループットが必須条件


2. 継続的な事前トレーニング
  - ラベルなしのデータセット
    - `input`:BedrockはAWSの生成AIサービスです。
       →ドメイン知識を獲得できる。

### CloudWatchとの連携
- CloudWatchの主な機能
  - メトリックス
  - ログ
  - ダッシュボード
  - アラーム
- CloudWatch Dashboardを作成する方法
  - [BedrockとCloudWatchの統合](https://aws.amazon.com/jp/blogs/news/amazon-bedrock_and_amazon-cloudwatch_integration_for_genai/)

### 生成AIアプリのネットワーク設計
- 複数サービスのプライベート接続例
- NATゲートウェイを使用したプライベート接続例
- オンプレミス環境とのプライベート接続例
- AWS上のアプリケーションからAzureOpenAIを呼び出す方法
  - [Azureネットワーク設定](https://learn.microsoft.com/ja-jp/azure/ai-services/cognitive-services-virtual-networks) 
  - [AWSとMicrosoftAzure間のサイト間VPN接続](https://repost.aws/ja/knowledge-center/vpn-azure-aws-bgp)


### Amazon Sagemaker
- Sagemakerは機械学習に必要な開発環境を素早く構築できるフルマネージド型の機械学習サービス

### Bedrock Claude Chat
- [チャットボットのサンプル](https://github.com/aws-samplpassword
es/bedrock-claude-chat/blob/main/docs/README_ja.md)
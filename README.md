# jma-api-forecast

気象庁 (JMA) の JSON API を使用して、日本国内主要 10 地点の週間予報データを自動取得し、CSV および JSON 形式で保存するツールです。Cloud Run 等のクラウド環境での定期実行を想定した設計になっています。

## プロジェクト構成

```text
.
├── data/                    # 取得した予報データ (CSV, JSON)
├── src/
│   ├── main.py              # エントリポイント
│   ├── config.py            # ロギング設定・地点設定の読み込み
│   ├── fetcher.py           # API 取得・パース処理
│   ├── saver.py             # CSV/JSON 保存処理
│   ├── bigquery_client.py   # BigQuery 書き込み処理
│   ├── models.py            # データモデル (AreaSetting, Forecast)
│   └── locations.toml       # 取得対象エリアの設定ファイル
├── tests/
│   ├── test_config.py
│   ├── test_fetcher.py
│   ├── test_saver.py
│   └── test_bigquery_client.py
├── Dockerfile
├── .dockerignore
├── pyproject.toml
└── README.md
```

## セットアップ

Python 3.13 以上が必要です。依存ライブラリの管理には [uv](https://docs.astral.sh/uv/) を使用しています。

```bash
uv sync
```

開発用ツール（mypy・pytest）もインストールする場合:

```bash
uv sync --group dev
```

## 実行方法

```bash
uv run python src/main.py
```

実行後、`data/` ディレクトリ内に以下のファイルが生成されます。

| ファイル | 内容 |
| --- | --- |
| `data/all_forecasts.json` | 全レコードの JSON |
| `data/all_forecasts.csv` | 全レコードの CSV（BOM 付き UTF-8） |

## Cloud Run デプロイ

### 前提条件

- Google Cloud プロジェクトが作成済みであること
- `gcloud` CLI がインストール済みで、対象プロジェクトに認証済みであること
- 以下の API が有効化されていること
  - Artifact Registry API
  - Cloud Run API
  - Cloud Scheduler API
  - IAM API

### 1. 環境変数の設定

```bash
export PROJECT_ID=your-project-id
export REGION=asia-northeast1
export REPO=jma-api-forecast
export JOB_NAME=jma-api-forecast
export SA_NAME=jma-api-forecast-sa
```

### 2. サービスアカウントの作成と権限付与

```bash
# サービスアカウントの作成
gcloud iam service-accounts create $SA_NAME \
  --display-name "jma-api-forecast runner"

# Cloud Run ジョブ実行権限（Cloud Scheduler が Job を起動するために必要）
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member "serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/run.invoker"
```

### 3. Artifact Registry リポジトリの作成（初回のみ）

```bash
gcloud artifacts repositories create $REPO \
  --repository-format=docker \
  --location=$REGION \
  --description "jma-api-forecast Docker images"
```

### 4. Docker イメージのビルドと push

```bash
gcloud builds submit \
  --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${JOB_NAME}:latest
```

### 5. Cloud Run ジョブのデプロイ

```bash
gcloud run jobs create $JOB_NAME \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${JOB_NAME}:latest \
  --region $REGION \
  --service-account ${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com \
  --max-retries 1 \
  --task-timeout 300
```

更新時は `create` を `update` に変更して同じコマンドを実行します。

手動実行で動作確認する場合:

```bash
gcloud run jobs execute $JOB_NAME --region $REGION
```

### 6. Cloud Scheduler でのスケジュール実行設定

毎日 06:00 JST に実行する例（スケジュールは用途に応じて変更してください）:

```bash
gcloud scheduler jobs create http ${JOB_NAME}-daily \
  --location $REGION \
  --schedule "0 6 * * *" \
  --time-zone "Asia/Tokyo" \
  --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run" \
  --http-method POST \
  --oauth-service-account-email ${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
```

### 7. 実行失敗の監視

Cloud Run ジョブは全エリアの取得が失敗した場合に exit code 1 で終了します。Cloud Monitoring でアラートを設定することで失敗を検知できます。

```bash
# ジョブ実行履歴の確認
gcloud run jobs executions list --job $JOB_NAME --region $REGION

# 直近の実行ログの確認
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=${JOB_NAME}" \
  --limit 50 \
  --format "value(timestamp, severity, textPayload)"
```

## BigQuery へのデータ書き込み

### 事前準備

```bash
export PROJECT_ID=your-project-id
export DATASET_ID=weather_data
export TABLE_ID=jma_weekly_forecast

# データセットの作成（初回のみ）
bq mk --dataset --location=asia-northeast1 ${PROJECT_ID}:${DATASET_ID}

# テーブルの作成（初回のみ）
bq mk --table \
  ${PROJECT_ID}:${DATASET_ID}.${TABLE_ID} \
  date:STRING,area_group:STRING,prefecture:STRING,location:STRING,weather_code:STRING,pop:STRING,temp_min:STRING,temp_max:STRING,reliability:STRING
```

### 環境変数

Cloud Run ジョブに以下の環境変数を設定することで BigQuery への書き込みが有効になります。

| 環境変数 | 必須 | デフォルト | 説明 |
| --- | --- | --- | --- |
| `GCP_PROJECT_ID` | 必須 | なし | Google Cloud プロジェクト ID。未設定の場合は BigQuery 書き込みをスキップ |
| `BQ_DATASET_ID` | 任意 | `weather_data` | BigQuery データセット ID |
| `BQ_TABLE_ID` | 任意 | `jma_weekly_forecast` | BigQuery テーブル ID |

Cloud Run ジョブへの環境変数設定:

```bash
gcloud run jobs update $JOB_NAME \
  --region $REGION \
  --set-env-vars GCP_PROJECT_ID=${PROJECT_ID},BQ_DATASET_ID=${DATASET_ID},BQ_TABLE_ID=${TABLE_ID}
```

### 書き込み方式

毎実行で `WRITE_TRUNCATE`（全件上書き）を使用します。週間予報は日々更新されるため、常に最新の予報データで上書きします。

## 取得地点の変更

取得対象エリアは `src/locations.toml` を編集するだけで変更できます。Python コードの修正は不要です。

```toml
[[locations]]
area_name   = "首都圏"
prefecture  = "東京"
location    = "東京"
area_code   = "130000"
office_code = "130000"
```

| フィールド | 内容 |
| --- | --- |
| `area_name` | 広域エリア名（出力データの `area_group` に使用） |
| `prefecture` | 都道府県名 |
| `location` | 地点名 |
| `area_code` | 気象庁の地域コード |
| `office_code` | 気象庁の府県予報区コード（API リクエストに使用） |

## データ項目 (CSV/JSON)

BigQuery への格納を想定し、列名は英語（スネークケース）で定義されています。

| 列名 | 内容 | 型/例 |
| --- | --- | --- |
| `date` | 予報日 | YYYY-MM-DD |
| `area_group` | 広域エリア名 | 首都圏, 近畿 など |
| `prefecture` | 都道府県名 | 東京, 大阪 など |
| `location` | 地点名 | 東京, 大阪 など |
| `weather_code` | 天気コード | 100, 200, 300 など (※1) |
| `pop` | 降水確率 | 0 〜 100 (%) |
| `temp_min` | 最低気温 | 摂氏 (℃) |
| `temp_max` | 最高気温 | 摂氏 (℃) |
| `reliability` | 予報の信頼度 | A, B, C |

> (※1) `weather_code` は気象庁定義のコードです。詳細な天気名が必要な場合は BigQuery 側でマスタテーブルと結合して利用してください。

## 開発

### テストの実行

```bash
uv run pytest tests/ -v
```

### 型チェック

```bash
uv run mypy src/ tests/
```

### Lint

```bash
uv run ruff check .
```

## 特徴

- **設定とコードの分離**: 取得エリアは `src/locations.toml` で管理し、コードを変更せずに地点の追加・変更が可能です。
- **API 到達性**: クラウド環境からのアクセス拒否を避けるため、`User-Agent` ヘッダーを適切に設定しています。
- **堅牢なエラーハンドリング**: ネットワークエラーとパースエラーを分けて記録し、一部エリアで失敗しても残りのデータを取得し続けます。全件失敗時は exit code 1 で終了するため、Cloud Run のジョブ失敗検知に対応しています。
- **型安全**: pydantic による地点設定のバリデーション、全関数への型アノテーション、mypy による静的型チェックを実施しています。

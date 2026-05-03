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
│   ├── models.py            # データモデル (AreaSetting, Forecast)
│   └── locations.toml       # 取得対象エリアの設定ファイル
├── tests/
│   ├── test_config.py
│   ├── test_fetcher.py
│   └── test_saver.py
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

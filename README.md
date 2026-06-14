# Day 7 まとめ：外部API連携（天気・植物識別）

---

## 1. 今日やったこと

```
新プロジェクト zukan-app を作成
  ↓
Open-Meteo API（天気・気温・湿度の取得）を試す
  ↓
Pl@ntNet API（写真から植物を識別）を試す
```

---

## 2. 新プロジェクトのセットアップ

```powershell
cd ~
mkdir zukan-app
cd zukan-app
python -m venv venv
venv\Scripts\activate
pip install requests
```

- 既存の`myapp`（タスク管理アプリ）とは別のフォルダで管理
- `database.py`や`auth.py`の書き方は再利用可能

---

## 3. VS Code拡張機能

| 拡張機能 | 役割 |
|---|---|
| Python(Microsoft) | 実行・デバッグ・補完（必須） |
| Pylance | コード補完・型チェック強化 |
| REST Client | APIリクエストをVS Code内でテスト |
| SQLite Viewer | DBの中身をGUIで確認 |
| GitLens | Gitの履歴・diffを見やすくする |
| Error Lens | エラーを行内に表示 |

---

## 4. Open-Meteo APIで天気取得

```python
import requests

url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 35.68,
    "longitude": 139.69,
    "current": "temperature_2m,relative_humidity_2m,weather_code"
}

response = requests.get(url, params=params)
data = response.json()

print(data["current"]["temperature_2m"])      # 気温
print(data["current"]["relative_humidity_2m"]) # 湿度
print(data["current"]["weather_code"])         # 天気コード
```

### response.json()とは

| | 内容 |
|---|---|
| `response` | HTTPレスポンス全体（status_code, headers, body など） |
| `response.text` | 本文（JSON形式の**文字列**） |
| `response.json()` | 本文の文字列をPythonの**辞書(dict)**に変換したもの |

`.json()`を使うことで`data["current"]["temperature_2m"]`のようにキーでアクセスできるようになる。

### weather_codeを文字に変換（コンパクトな書き方）

```python
def get_weather_description(code: int) -> str:
    table = [
        (0, "快晴"),
        (3, "晴れ〜曇り"),
        (48, "霧"),
        (67, "雨"),
        (77, "雪"),
        (99, "雷雨・にわか雨"),
    ]
    return next(desc for limit, desc in table if code <= limit)
```

- `table`: 「この値以下ならこの説明」というペアのリスト
- `next(... for ... if ...)`: 最初に条件が成立した`desc`を返す
- if/elifを並べるより、表に1行追加するだけで済む

---

## 5. 環境変数とAPIキーの管理

### .envファイルの作成

```
PLANTNET_API_KEY=（取得したAPIキー）
```

### python-dotenvのインストール

```powershell
pip install python-dotenv
```

### コードでの読み込み

```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.environ["PLANTNET_API_KEY"]
```

### venvと.envの違い（混同しやすい）

| 名前 | 何か | 役割 |
|---|---|---|
| venv | 仮想環境（フォルダ） | プロジェクトごとに独立したPython環境を作る |
| .env | 環境変数を書くファイル | APIキーなどの秘密情報をコードと分離して管理する |

- `.env`に書いた変数名と、`os.environ["..."]`の中の文字列は完全に一致させる必要がある
- `.env`はGitHubにpushしないように設定する（次回以降対応）

---

## 6. Pl@ntNet APIで植物識別

### アカウント登録・APIキー取得

`https://my.plantnet.org/` でサインアップし、APIキーを取得。

### 識別コード

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ["PLANTNET_API_KEY"]

url = f"https://my-api.plantnet.org/v2/identify/all?api-key={api_key}"

files = [
    ("images", ("tanpopo.jpg", open("tanpopo.jpg", "rb")))
]
data = {"organs": ["flower"]}

response = requests.post(
    url,
    files=files,
    data=data,
    params={"lang": "ja"}  # 日本語の名前を取得
)
result = response.json()
```

### コードのポイント

- `requests.post`: 画像とデータを送信するので**POST**を使う（GETはデータ取得のみ）
- `files`: 画像ファイルを送るための指定。`open("tanpopo.jpg", "rb")`で画像をバイナリ（`rb`=読み込み専用・バイナリモード）で開く
- `data`: リクエストの**本文(body)**に入る情報（`organs`など）
- `params`: URLの**クエリパラメータ**（`?lang=ja`など）に入る情報
- `lang`は`data`ではなく`params`で渡す必要がある（`data`に入れると「許可されていない」エラーになる）

### レスポンスから情報を取り出す

```python
best_match = result["bestMatch"]
common_names = result["results"][0]["species"]["commonNames"]
score = result["results"][0]["score"]

# 日本語(ひらがな・カタカナ・漢字)を含む名前を探す
common_name = next(
    (name for name in common_names if any(
        '぀' <= c <= 'ヿ' or '一' <= c <= '鿿' for c in name
    )),
    common_names[0]
)

print(f"学名: {best_match}")
print(f"一般名: {common_name}")
print(f"確信度: {score}")
```

### 結果（タンポポの写真）

```
学名: Taraxacum officinale F.H.Wigg.
一般名: アイノコセイヨウタンポポ
確信度: 0.31559
```

- `remainingIdentificationRequests`から、無料枠は1日500回までと確認できた

---

## 7. よくやったミス

### .envの変数名とコードの不一致

```python
# .env: PLANTNET_API_KEY=xxxx
api_key = os.environ["PLANT_API_KEY"]   # ❌ 名前が違う
api_key = os.environ["PLANTNET_API_KEY"]  # ✅ 一致させる
```

### URLのスペルミス

```
v2/indentfy/all   ❌
v2/identify/all   ✅
```

### langパラメータをdataに入れてしまった

```python
# ❌ "lang" is not allowed エラー
data = {"organs": ["flower"], "lang": "ja"}

# ✅ paramsに入れる
data = {"organs": ["flower"]}
params = {"lang": "ja"}
```

### リストに余計な[0]を付けた

```python
# ❌ 文字列（最初の名前）になってしまう
common_names = result["results"][0]["species"]["commonNames"][0]

# ✅ リスト全体を取得する
common_names = result["results"][0]["species"]["commonNames"]
```

`for name in common_names`を文字列に対して行うと、1文字ずつ取り出されてしまい、`commonNames[0]`が「名前の最初の1文字」になってしまう。

---

## 次回 Day 8 の予告

- Anthropic API(Claude)を使い、生物名から飼育方法を生成する
- `.env`をGitHubにpushしないための設定（`.gitignore`）

# Day1〜7 総復習 練習問題（全50問）

各問題に「コードを書く」「コードを読む（説明する）」を混ぜています。
答えは`practice_50_answers.md`を見てください。まずは自分で考えてみましょう。

---

## Part A: FastAPI基礎・環境（Day1）【1〜5】

**Q1.** 次のコードは何をするものか説明してください。

```python
@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"こんにちは、{name}さん！"}
```

**Q2.** `uvicorn main:app --reload`の各部分（`main`, `app`, `--reload`）が何を意味するか説明してください。

**Q3.** ASGIとは何か、WSGI（同期）との違いを簡単に説明してください。

**Q4.** 以下のコードを書いてください: `/square/{number}`にアクセスすると、`number`の2乗を`{"result": ...}`の形で返すエンドポイント。

**Q5.** `venv\Scripts\activate`を実行する目的を説明してください。

---

## Part B: CRUD・リスト操作（Day2）【6〜20】

**Q6.** 次のコードのバグを指摘してください。

```python
@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
            raise HTTPException(status_code=404, detail="見つかりません")
```

**Q7.** リスト内包表記を使って、`tasks`の中から`done`が`True`のものだけを抜き出すコードを書いてください。

**Q8.** 次の2つのコードの違いを説明してください。

```python
task["title"] == new_title
task["title"] = new_title
```

**Q9.** 以下のエンドポイントを書いてください: `POST /tasks/bulk`で、複数のタスク（`title`のリスト）を受け取り、それぞれに`id`を割り振って`tasks`に追加し、追加したタスク一覧を返す。

**Q10.** 次のコードはなぜ動かないか説明してください。

```python
@app.get("/tasks/{task_id}")
@app.get("/tasks/search")
def search_tasks(keyword: str):
    ...
```

**Q11.** `@app.delete("/tasks/{task_id}")`と`@app.delete("/tasks/done")`はどちらを先に書くべきか、理由とともに答えてください。

**Q12.** `global`が必要な場合と不要な場合を、それぞれ例で説明してください。

**Q13.** 次のコードを書いてください: `GET /tasks/stats`で、タスクの総数・完了数・未完了数を辞書で返す。

**Q14.** 次のコードのエラーを直してください。

```python
if not target:
    raise HTTPException(status_code==404, detail="見つかりません")
```

**Q15.** PUTとPATCHの違いを説明してください。

**Q16.** 次のコードを書いてください: `PATCH /tasks/{task_id}/done`で、指定したタスクの`done`を反転（True⇔False）させる。

**Q17.** 次のコードのバグを指摘してください。

```python
def title_put(task_id: int, task: Task):
    for task in tasks:
        if task["id"] == task_id:
            task["title"] = task.title
            return task
```

**Q18.** クエリパラメータとパスパラメータの違いを、URLの例を使って説明してください。

**Q19.** 次のコードを書いてください: `DELETE /tasks/done`で、`done`が`True`のタスクを全て削除し、削除件数を返す。

**Q20.** 422エラーが返ってくる典型的な原因を1つ挙げてください。

---

## Part C: データベース・SQLAlchemy（Day3）【21〜33】

**Q21.** 次のコードの`Base`の役割を説明してください。

```python
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
```

**Q22.** `Base.metadata.create_all(bind=engine)`は何をするか説明してください。

**Q23.** 次のコードの`yield`と`finally`の役割を説明してください。

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Q24.** 次のコードを書いてください: `Task`モデルに`priority`（整数、デフォルト1）という列を追加する。

**Q25.** 次の操作をSQLAlchemyで書いてください: `tasks`テーブルから`done`が`False`のものを全件取得する。

**Q26.** 次のコードのバグを指摘してください。

```python
@app.put("/tasks/{task_id}")
def put_title(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    task.title = task.title
    db.commit()
    return task
```

**Q27.** `db.add()`, `db.commit()`, `db.refresh()`の役割をそれぞれ説明してください。

**Q28.** `index=True`を付ける理由を説明してください。

**Q29.** 次のコードを書いてください: `GET /tasks/search?keyword=xxx`で、`title`に`keyword`を含むタスクを検索する（SQLAlchemy版）。

**Q30.** `nullable=False`と`default=False`の違いを説明してください。

**Q31.** ルーティングの順番について、次の2つを正しい順番に並べてください。

```python
@app.get("/tasks/{task_id}")
@app.get("/tasks/search")
```

**Q32.** `db.delete(obj)`の後に何を呼ぶ必要があるか答えてください。

**Q33.** Day2（メモリ）とDay3（DB）で、データの永続性にどのような違いがあるか説明してください。

---

## Part D: 認証・JWT（Day4）【34〜43】

**Q34.** `hash_password`と`verify_password`の違いを説明してください。

**Q35.** 「ソルト」とは何か、なぜ必要か説明してください。

**Q36.** 次のコードを書いてください: `User`モデルに`username`（一意、必須）と`hashed_password`（必須）の列を持つテーブルを定義する。

**Q37.** JWTの`exp`クレームは何のためにあるか説明してください。

**Q38.** 次のコードのバグを指摘してください。

```python
def get_tasks(db: Session = Depends(get_db), get_current_user: str = Depends(get_current_user)):
    return db.query(Task).all()
```

**Q39.** `OAuth2PasswordBearer`と`OAuth2PasswordRequestForm`の役割の違いを説明してください。

**Q40.** 次のコードを書いてください: `/register`エンドポイントで、ユーザー名の重複チェックを行い、重複していれば400エラーを返す。

**Q41.** `Authorization: Bearer <token>`の`Bearer`とは何を意味するか説明してください。

**Q42.** `jwt.encode`と`jwt.decode`の入出力の関係を説明してください。

**Q43.** JWTはどこに保存されるか、また有効期限が切れたらどうなるか説明してください。

---

## Part E: タスクとユーザーの紐付け（Day5）【44〜46】

**Q44.** 次のコードを書いてください: `Task`モデルに`owner_id`（`User.id`への外部キー）を追加する。

**Q45.** 次のコードを書いてください: `POST /tasks`で、ログイン中のユーザーのidを`owner_id`として保存する（`current_user`はユーザー名）。

**Q46.** SQLite + SQLAlchemyで「投稿直後にGETしても表示されない」という不具合が起きる原因と、解決のために追加する2つの関数の役割を説明してください。

---

## Part F: 外部API連携（Day7）【47〜50】

**Q47.** 次のコードを書いてください: Open-Meteo APIにリクエストを送り、`temperature_2m`を取り出して表示する（緯度35.68、経度139.69）。

**Q48.** `response.json()`が何をしているか、`response.text`との違いとともに説明してください。

**Q49.** `.env`ファイルと`venv`フォルダの違いを説明してください。

**Q50.** 次のコードのバグを指摘してください。

```python
data = {"organs": ["flower"], "lang": "ja"}
response = requests.post(url, files=files, data=data)
```

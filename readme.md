# arxiv_interpreter

arxivの論文を読み取り、[落合陽一形式のフォーマット](https://www.slideshare.net/Ochyai/1-ftma15#65)で要約を返してくれるSlackボット

## 実行方法
- Slack APIの設定を行う
- `.env`に以下の環境変数を格納する
  - MODELは`GPT3`か`GPT4`を選択
```.env
OPEN_AI_API_KEY=
MODEL=GPT3
SLACK_BOT_TOKEN=
SLACK_APP_TOKEN=
```
- `python main.py`で実行する

## 注意事項
論文全文を読み取り、トークン数の多いChatGPTモデルに入力しています.

利用料金には十分気を付けてください.
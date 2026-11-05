# 無価値価値 Webカメラ専用配布版 0.1.2

前のVプロジェクトのcodex/webcam-distribution（6a5e70a5f69bfcb85706e82e5ffa9149319b78d9）を確認し、同ブランチのviewer/index.htmlに基づく単一HTML方式で作成。
モデルは無価値価値自身の生成rigを使用。元キャラの画像や既存配布HTMLを差し替え改変していない。

dist/mukachi_kachi_webcam_0.1.2.zip：単一HTML、はじめに.txt、VERSION.txtを同梱。
iPhone、VTube Studio、Node.js、npm、UDP中継は不要。Webカメラの開始ボタンで追跡する。顔認識にはネット接続が必要。

ブラウザのモデル表示、ネイティブ疑似カメラ取得と停止、拒否時の案内、iPhoneコード非混入、ZIP内HTML一致を検証。顔検出器を模擬した試験であり、実MediaPipeの読込みやMacの実カメラを検証したものではない。

GitHubの通常のコード表示・チャット内プレビューは起動用の画面ではない。配布ZIPのダウンロードが必要。GitHubアカウントにログインし、対象リポジトリのアクセス権が必要な場合がある。
MacのFinderで展開して、HTMLをChromeで開く。「開始」→カメラを許可→正面・閉じ口で「正面を較正」。1=笑顔、2=驚き、0=通常。

HTML内のカメラ映像は顔追跡に使い、カメラ映像を送信する処理は実装していない。顔追跡コードとモデルはcdn.jsdelivr.netとstorage.googleapis.comから取得する。

最新版は0.2.0。docs/webcam-repairs-0.2.0.mdを参照。0.1.2は戻す版として保存。

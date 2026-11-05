# 無価値価値：HTML Webカメラモデル

最新版はWebカメラ専用0.3.0です。iPhone・Node.js・中継サーバー不要。インターネット接続が必要です。

[配布ZIPをダウンロード](https://github.com/98nryk89/-Live2D/raw/refs/heads/codex/webcam-distribution/dist/mukachi_kachi_webcam_0.3.0.zip)

FinderでZIPを展開し、中のmukachi_kachi_webcam_0.3.0.htmlをChromeで開きます。「開始」→カメラを許可→「正面を較正」。チャット内プレビューでは起動しません。

今回の修正：閉じ目の瞼・陰影を保持、口差分を通常口の傾きに補正。かしげは左5度・右12度。V完成版に倣って頭・首・胴を分け、顔の片側が残る伸びを除去。装飾9箇所の揺れは維持。
[修正・検査・追加素材・再生成](docs/webcam-repairs-0.3.0.md)を参照してください。Mac実カメラ・OBSは未確認です。
旧配布版0.1.2のZIPも保持しています。

制作ソース：character_materialsに原本、projects/mukachi_kachiに変換・リグ情報、toolsに生成処理、viewerに描画とWebカメラ入力。requirements-validated.txtは検証環境のPython依存バージョンです。

# 無価値価値：HTML Webカメラモデル

最新版はWebカメラ専用0.4.0です。iPhone・Node.js・中継サーバー不要。インターネット接続が必要です。

[配布ZIPをダウンロード](https://github.com/98nryk89/-Live2D/raw/refs/heads/codex/webcam-distribution/dist/mukachi_kachi_webcam_0.4.0.zip)

FinderでZIPを展開し、中のmukachi_kachi_webcam_0.4.0.htmlをChromeで開きます。「開始」→カメラを許可→「正面を較正」。チャット内プレビューでは起動しません。

今回の修正：新たに提供された開・半開・閉の3画像を直接使用し、目の変形補間を廃止。かしげは左右とも5度。肩の熊と髪の所属を切り直し、熊の裏の髪には提供された下絵を使用。口と装飾9箇所の揺れは維持。
[修正・検査・追加素材・再生成](docs/webcam-repairs-0.4.0.md)を参照してください。Mac実カメラ・OBSは未確認です。
旧配布版0.1.2のZIPも保持しています。

制作ソース：character_materialsに原本、projects/mukachi_kachiに変換・リグ情報、toolsに生成処理、viewerに描画とWebカメラ入力。requirements-validated.txtは検証環境のPython依存バージョンです。

再生成：Python仮想環境でrequirements-validated.txtを導入し、tools/prepare_character.py → tools/prepare_revision4.py → tools/build_character.py → tools/export_webcam.pyを順に実行します。

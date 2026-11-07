# 無価値価値：HTML Webカメラモデル

最新版はWebカメラ専用0.10.0です。iPhone・Node.js・中継サーバー不要。インターネット接続が必要です。

[配布ZIPをダウンロード](https://github.com/98nryk89/-Live2D/raw/refs/heads/codex/webcam-distribution/dist/mukachi_kachi_webcam_0.10.0.zip)

FinderでZIPを展開し、中のmukachi_kachi_webcam_0.10.0.htmlをChromeで開きます。「開始」→カメラを許可→「正面を較正」。チャット内プレビューでは起動しません。

今回の修正：提供された首肌を別の曲面に配置し、頭を顎までで分離。顎下の影を首の内側へクリップし、襟の前後で重なりを管理する構成にしました。装飾の重力と小さめの揺れは維持。追加の画像生成は行っていません。見た目の自然さは比較画像・GIFと実際の動作で確認する検証版です。
[修正・検査・追加素材・再生成](docs/webcam-repairs-0.10.0.md)を参照してください。Mac実カメラ・OBSは未確認です。
旧配布版0.1.2のZIPも保持しています。

制作ソース：character_materialsに原本、projects/mukachi_kachiに変換・リグ情報、toolsに生成処理、viewerに描画とWebカメラ入力。requirements-validated.txtは検証環境のPython依存バージョンです。

再生成：Python仮想環境でrequirements-validated.txtを導入し、tools/prepare_character.py → tools/prepare_revision4.py → tools/build_character.py → tools/export_webcam.pyを順に実行します。

[首の作画依頼書](docs/neck-material-request.md) ／ [絵師へ渡す資料ZIP](https://github.com/98nryk89/-Live2D/raw/refs/heads/codex/webcam-distribution/dist/mukachi_kachi_neck_materials.zip)

[新しく受領した首かしげ素材の評価と次の生成プロンプト](docs/neck-pose-assessment.md)

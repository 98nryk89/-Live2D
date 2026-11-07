"""Standalone webcam export following V/codex/webcam-distribution, without iPhone input/relay."""
from pathlib import Path
import json,base64,hashlib,zipfile
R=Path(__file__).resolve().parents[1];O=R/'projects/mukachi_kachi/out';D=R/'dist'
rig=json.loads((O/'rig.json').read_text())
for part in rig['parts']:part['tex']='data:image/png;base64,'+base64.b64encode((O/part['tex']).read_bytes()).decode()
s=(R/'viewer/webcam.html').read_text()
for name in ['pendulum.js','runtime.js','tracking.js']:
 code=(R/'viewer'/name).read_text().replace('</script','<\\/script')
 s=s.replace(f'<script src="{name}"></script>','<script>'+code+'</script>')
s=s.replace('<script>\nconst q=','<script>window.__RIG__='+json.dumps(rig,ensure_ascii=False,separators=(',',':'))+';</script>\n<script>\nconst q=',1)
assert 'window.__RIG__=' in s
assert 'WebSocket(' not in s and 'iOSTrackingDataRequest' not in s
html=D/'mukachi_kachi_webcam.html';html.write_text(s)
readme='''無価値価値 Webカメラ専用版 0.12.0

GitHubからこのZIPを保存し、MacのFinderの「ダウンロード」で展開してください。
中の mukachi_kachi_webcam_0.12.0.html をGoogle Chromeで開き、「開始」を押します。
チャット内のプレビューはカメラを使えません。

元のVプロジェクトと同じ、単一HTML＋Webカメラ追跡方式です。
iPhone、VTube Studio、Node.js、npm、中継サーバーは不要です。
顔認識用ライブラリとモデルは初回開始時にインターネットから取得します。
正面・閉じ口で「正面を較正」。1=笑顔、2=驚き、0=通常です。
頭の元絵の傾きを補正し、真っ直ぐな状態を基準に、顔は画面左（熊側）8度・右5度まで傾きます。首自体は左右5度のままです。V完成版を基準に頭・首・胴を分け、首は元絵の輪郭と陰影を使う構成へ戻しました。
通常の瞬きは開・半開・閉の3枚を使用し、笑顔では最初に提供された笑顔の目を表示します。口は0.3.0の状態を維持しています。
イヤリング2点とタッセル7点の重力と、小さめの揺れ量は0.9.0の設定を維持しています。熊の笑顔と約4秒ごとの瞬きも維持しています。
首元の支点と動きはV完成版の値をこのキャラの顎・襟の位置に対応させています。生成した首肌は使用しません。比較画像と動作GIFを同梱しています。
この版のMac実カメラとOBSは未確認です。
'''
archive=D/'mukachi_kachi_webcam_0.12.0.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 z.write(html,'Mukachi_Webcam_0.12.0/mukachi_kachi_webcam_0.12.0.html')
 z.writestr('Mukachi_Webcam_0.12.0/はじめに.txt',readme)
 for name in ['neck_before_after.jpg','neck_review.jpg','neck_motion.gif']:
  proof=R/'docs/verification/repair_0.12.0'/name
  if proof.exists():z.write(proof,'Mukachi_Webcam_0.12.0/確認画像/'+name)
 z.writestr('Mukachi_Webcam_0.12.0/VERSION.txt','Model SHA256 '+hashlib.sha256(html.read_bytes()).hexdigest()+'\nViewer source: 98nryk89/V @6a5e70a5f69bfcb85706e82e5ffa9149319b78d9 (webcam distribution)\n')
with zipfile.ZipFile(archive) as z:assert z.testzip() is None and z.read('Mukachi_Webcam_0.12.0/mukachi_kachi_webcam_0.12.0.html')==html.read_bytes()
print(archive)

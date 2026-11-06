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
readme='''無価値価値 Webカメラ専用版 0.9.0

GitHubからこのZIPを保存し、MacのFinderの「ダウンロード」で展開してください。
中の mukachi_kachi_webcam_0.9.0.html をGoogle Chromeで開き、「開始」を押します。
チャット内のプレビューはカメラを使えません。

元のVプロジェクトと同じ、単一HTML＋Webカメラ追跡方式です。
iPhone、VTube Studio、Node.js、npm、中継サーバーは不要です。
顔認識用ライブラリとモデルは初回開始時にインターネットから取得します。
正面・閉じ口で「正面を較正」。1=笑顔、2=驚き、0=通常です。
頭の元絵の傾きを補正し、真っ直ぐな状態を基準に左右5度ずつ傾きます。頭と首を連続メッシュに統合し、襟は固定しています。
通常の瞬きは開・半開・閉の3枚を使用し、笑顔では最初に提供された笑顔の目を表示します。口は0.3.0の状態を維持しています。
イヤリング2点とタッセル7点は重力・慣性・減衰を持つ2D振り子です。停止すると画面の下へ垂れます。熊は笑顔で両目を閉じ、通常時は約4秒ごとに瞬きします。揺れは初期ONです。揺れへの反応量は前版の半分に設定しています。首の素材依頼書と参考画像を同梱しています。首の違和感は未解決で、この版では首を変更していません。
この版のMac実カメラとOBSは未確認です。
'''
archive=D/'mukachi_kachi_webcam_0.9.0.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 z.write(html,'Mukachi_Webcam_0.9.0/mukachi_kachi_webcam_0.9.0.html')
 z.writestr('Mukachi_Webcam_0.9.0/はじめに.txt',readme)
 for name in ['upright_placement_reference.png']:
  proof=R/'docs/verification/repair_0.9.0'/name
  if proof.exists():z.write(proof,'Mukachi_Webcam_0.9.0/首の素材依頼/'+name)
 z.write(R/'docs/neck-material-request.md','Mukachi_Webcam_0.9.0/首の素材依頼/作画依頼書.txt')
 z.write(R/'character_materials/mukachi_kachi/base.png','Mukachi_Webcam_0.9.0/首の素材依頼/original_base.png')
 z.writestr('Mukachi_Webcam_0.9.0/VERSION.txt','Model SHA256 '+hashlib.sha256(html.read_bytes()).hexdigest()+'\nViewer source: 98nryk89/V @6a5e70a5f69bfcb85706e82e5ffa9149319b78d9 (webcam distribution)\n')
with zipfile.ZipFile(archive) as z:assert z.testzip() is None and z.read('Mukachi_Webcam_0.9.0/mukachi_kachi_webcam_0.9.0.html')==html.read_bytes()
print(archive)

materials=D/'mukachi_kachi_neck_materials.zip'
with zipfile.ZipFile(materials,'w',zipfile.ZIP_DEFLATED) as z:
 z.write(R/'docs/neck-material-request.md','Mukachi_Neck_Materials/作画依頼書.txt')
 z.write(R/'character_materials/mukachi_kachi/base.png','Mukachi_Neck_Materials/original_base.png')
 z.write(R/'docs/verification/repair_0.9.0/upright_placement_reference.png','Mukachi_Neck_Materials/upright_placement_reference.png')
with zipfile.ZipFile(materials) as z:assert z.testzip() is None
print(materials)

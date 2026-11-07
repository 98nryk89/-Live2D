"""Audit source-line restoration and white-background render, including tilted poses."""
from pathlib import Path
import json,io,base64,zipfile
import numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'docs/verification/repair_0.12.1';D.mkdir(exist_ok=True);checks=[]
def check(n,v):
 assert v,n
 checks.append(n);print('PASS',n,flush=True)
def rig(s):return json.JSONDecoder().raw_decode(s.split('window.__RIG__=',1)[1])[0]
with zipfile.ZipFile(R/'dist/mukachi_kachi_webcam_0.12.0.zip') as z:oldhtml=z.read('Mukachi_Webcam_0.12.0/mukachi_kachi_webcam_0.12.0.html').decode()
new=rig((R/'dist/mukachi_kachi_webcam.html').read_text());old=rig(oldhtml);oparts={p['id']:p for p in old['parts']}
check('all motion ranges and physics unchanged',new['params']==old['params'] and new['physics']==old['physics'])
source=np.array(Image.open(R/'character_materials/mukachi_kachi/base.png').convert('RGBA'));changed=[]
for p in new['parts']:
 o=oparts[p['id']];check('effects unchanged '+p['id'],p['effects']==o['effects'])
 a=np.array(Image.open(io.BytesIO(base64.b64decode(p['tex'].split(',',1)[1]))));b=np.array(Image.open(io.BytesIO(base64.b64decode(o['tex'].split(',',1)[1]))));diff=np.any(a!=b,axis=2)
 if diff.any():
  changed.append(p['id']);yy,xx=np.where(diff);check('change restricted to ear junction '+p['id'],xx.min()>=465 and xx.max()<535 and yy.min()>=335 and yy.max()<390)
 if p['id']=='companion':
  check('restored ear has exact source RGB and alpha',np.array_equal(a[diff],source[diff]));check('missing source outline restored',a[346,502,3]>200 and b[346,502,3]==0 and a[358,479,3]>200)
check('only companion and neighboring hair ownership changed',set(changed)=={'companion','head','hair_behind_companion'})
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);errors=[]
 def setup(url):
  p=b.new_page(viewport={'width':1350,'height':1165});p.on('pageerror',lambda e:errors.append(str(e)));p.goto(url);p.wait_for_function('window.READY===true');p.evaluate('M.stop();M.reset();M.auto={blink:false,idle:false,breath:false,physics:false,companionBlink:false};M.opts.view=[0,0,1350,1165]');p.add_style_tag(content='html,body,#stage{background:white!important}#app{display:block}#panel,#msg{display:none}#stage{width:1350px;height:1165px}');return p
 tmp=R/'dist/_before_ear13.html';tmp.write_text(oldhtml);p=setup('http://127.0.0.1:8089/mukachi_kachi_webcam.html');op=setup('http://127.0.0.1:8089/_before_ear13.html')
 sheet=Image.new('RGB',(1400,600),'white');draw=ImageDraw.Draw(sheet)
 for i,(pg,label,z) in enumerate([(op,'Before / white',0),(p,'Restored / white',0),(p,'Bear-side tilt 8',-8),(p,'Other-side tilt 5',5)]):
  pg.evaluate('z=>{M.reset();M.setParam("AngleZ",z);M.renderStill()}',z);im=Image.open(io.BytesIO(pg.locator('#c').screenshot())).convert('RGB');sheet.paste(im.crop((350,320,610,565)).resize((350,330)),(i*350,35));sheet.paste(im.crop((465,332,530,387)).resize((350,230)),(i*350,370));draw.text((i*350+8,10),label,fill='black')
 sheet.save(D/'bear_ear_white.jpg');check('no rendering script errors',not errors);op.close();p.close();tmp.unlink();b.close()
(D/'bear_ear13_results.json').write_text(json.dumps({'passed':checks,'scope':'source preservation and Chromium render on white; physical Mac camera and OBS unverified'},indent=2))

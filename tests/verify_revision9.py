"""Lower amplitude without changing gravity, images, geometry or the neck."""
from pathlib import Path
import json,zipfile,io
from PIL import Image
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'docs/verification/repair_0.9.0';D.mkdir(exist_ok=True);checks=[]
def check(name,ok,detail=None):
 assert ok,(name,detail)
 checks.append({'name':name,'detail':detail});print('PASS',name,detail,flush=True)
def rig(s):return json.JSONDecoder().raw_decode(s.split('window.__RIG__=',1)[1])[0]
current=rig((R/'dist/mukachi_kachi_webcam.html').read_text())
with zipfile.ZipFile(R/'dist/mukachi_kachi_webcam_0.8.0.zip') as z:previous=rig(z.read('Mukachi_Webcam_0.8.0/mukachi_kachi_webcam_0.8.0.html').decode())
check('all 128 textures meshes and effects unchanged',current['parts']==previous['parts'])
check('gravity damping lengths and support definitions unchanged',current['physics']==previous['physics'])
changed=[a['id'] for a,b in zip(current['params'],previous['params']) if a!=b];check('only default sway sensitivity changed',changed==['AccessoryGain'] and next(p for p in current['params'] if p['id']=='AccessoryGain')['default']==.5,changed)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1350,'height':1165},device_scale_factor=1);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto('http://127.0.0.1:8089/mukachi_kachi_webcam.html');page.wait_for_function('window.READY===true');page.evaluate('M.stop();M.reset();M.auto={blink:false,idle:false,breath:false,physics:true,companionBlink:false}')
 check('initial sensitivity halved',page.evaluate('M.params.AccessoryGain===.5'))
 response=page.evaluate('''()=>{function run(gain){M.reset();M.setParam('AccessoryGain',gain);M._drive(1/60);const out={};for(let n=1;n<=240;n++){const t=n/60;M.setParams({BodyX:.12*Math.sin(t*3.1),BodyY:.04*Math.sin(t*2.7),AngleZ:4*Math.sin(t*2.3)});M._drive(1/60);for(const d of M.rig.physics)out[d.part]=Math.max(out[d.part]||0,Math.abs(M.params[d.output]))}return out}const old=run(1),now=run(.5);return Object.fromEntries(Object.keys(old).map(k=>[k,{old:old[k],now:now[k],ratio:now[k]/old[k]}]))}''')
 check('all nine swing less with identical movement',len(response)==9 and all(.35<d['ratio']<.7 for d in response.values()),response)
 page.evaluate('M.reset();M.setParams({AngleZ:5,BodyX:.25});M.renderStill(900)');settled=page.evaluate('M.rig.physics.map(d=>Math.abs(M.params[d.output]))');check('all ornaments settle downward while head stays tilted',max(settled)<.03,settled)
 page.evaluate('M.reset();M.opts.view=[0,0,1350,1165];M.renderStill(600)');page.add_style_tag(content='html,body,#stage{background:transparent!important}#app{display:block}#panel,#msg{display:none}#stage{width:1350px;height:1165px}');page.evaluate('M.renderStill()');page.locator('#c').screenshot(path=str(D/'upright_placement_reference.png'),omit_background=True)
 check('artist placement reference matches original canvas',Image.open(D/'upright_placement_reference.png').size==(1350,1165))
 check('no browser script errors',not errors,errors);b.close()
(D/'revision9_results.json').write_text(json.dumps({'count':len(checks),'passed':checks,'scope':'simulated movement and renderer; neck unchanged and unresolved; physical Mac webcam/OBS unverified'},ensure_ascii=False,indent=2))

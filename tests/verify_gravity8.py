"""Verify gravity equilibrium, support inertia, damping and unchanged character geometry."""
from pathlib import Path
import json,zipfile,io
import numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'docs/verification/repair_0.8.0';D.mkdir(exist_ok=True);results=[]
def check(name,ok,detail=None):
 assert ok,(name,detail)
 results.append({'name':name,'detail':detail});print('PASS',name,detail,flush=True)
def rig(s):return json.JSONDecoder().raw_decode(s.split('window.__RIG__=',1)[1])[0]
current=rig((R/'dist/mukachi_kachi_webcam.html').read_text());parts={p['id']:p for p in current['parts']}
with zipfile.ZipFile(R/'dist/mukachi_kachi_webcam_0.7.0.zip') as z:old=rig(z.read('Mukachi_Webcam_0.7.0/mukachi_kachi_webcam_0.7.0.html').decode())
ornaments={p['part'] for p in current['physics']}
# Full-canvas textures can differ in invisible RGB beneath the repaired earring.
import base64
def visible_equal(a,b):
 def decode(p):return np.array(Image.open(io.BytesIO(base64.b64decode(p['tex'].split(',',1)[1]))).convert('RGBA'))
 x,y=decode(a),decode(b);v=(x[:,:,3]>0)|(y[:,:,3]>0)
 return np.array_equal(x[:,:,3],y[:,:,3]) and np.array_equal(x[v],y[v])
check('other visible character parts and expressions unchanged',all(visible_equal(parts[p['id']],p) and parts[p['id']]['mesh']==p['mesh'] and parts[p['id']]['effects']==p['effects'] for p in old['parts'] if p['id'] not in ornaments and p['id'] not in ['head','body']))
check('eight other ornament cutouts unchanged',len(ornaments)==9 and all(parts[p['id']]['tex']==p['tex'] and parts[p['id']]['mesh']==p['mesh'] for p in old['parts'] if p['id'] in ornaments and p['id']!='earring_name'))

# The name earring's previously stranded gold rim is removed; the throat image/effects stay exact.
import base64
oldparts={p['id']:p for p in old['parts']}
def image_of(p):return np.array(Image.open(io.BytesIO(base64.b64decode(p['tex'].split(',',1)[1]))).convert('RGBA'))
check('neck image and deformation unchanged',all(np.array_equal(image_of(parts[k])[385:505,610:765],image_of(oldparts[k])[385:505,610:765]) and parts[k]['effects']==oldparts[k]['effects'] for k in ['head','body']))
for k in ['head','body']:
 diff=np.any(image_of(parts[k])!=image_of(oldparts[k]),axis=2);diff[357:471,774:821]=False
 check(k+' changes confined to earring outer border',not diff.any())
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1350,'height':1165},device_scale_factor=1);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8089/mukachi_kachi_webcam.html');page.wait_for_function('window.READY===true');page.evaluate('M.stop();M.reset();M.auto={blink:false,idle:false,breath:false,physics:true,companionBlink:false};M.opts.view=[0,0,1350,1165]')
 page.add_style_tag(content='html,body,#stage{background:transparent!important}#app{display:block}#panel,#msg{display:none}#stage{width:1350px;height:1165px}')
 # Render two actual mesh points at the attachment and mass centre; use the exact renderer, not only solver state.
 geometry='''()=>M.rig.physics.map(d=>{const original=M.byId[d.part],rest=new Float32Array([...d.pivot,...d.com]),part={_rest:rest,_pos:new Float32Array(4),effects:original.effects};M._deform(part);const px=part._pos[0],py=part._pos[1],x=part._pos[2],y=part._pos[3],f=L2DGravity.frame(d,M.params);return {id:d.part,angle:Math.atan2(-(x-px),y-py)*180/Math.PI,dy:y-py,anchorError:Math.hypot(px-f.pivot[0],py-f.pivot[1])}})'''
 for pose in [{},{'AngleZ':-5},{'AngleZ':5},{'AngleX':5,'AngleY':-10,'AngleZ':5},{'AngleX':-5,'AngleY':5,'AngleZ':-5}]:
  page.evaluate('pose=>{M.reset();M.setParams(pose);M.renderStill(720)}',pose);data=page.evaluate(geometry)
  check('all accessories hang down at rest '+str(pose),all(abs(d['angle'])<.03 and d['dy']>0 and d['anchorError']<.0003 for d in data),data)
 # Sustained acceleration to the right makes the masses lag to the left.
 inertia=page.evaluate('''()=>{M.reset();M.renderStill(1);for(let n=1;n<=60;n++){const t=n/240;M.setParam('BodyX',(.5*900*t*t)/135);M._drive(1/240)}return M.rig.physics.map(d=>({id:d.part,angle:M.params[d.output]}))}''')
 check('masses lag left under rightward support acceleration',all(d['angle']>1 for d in inertia),inertia)
 page.evaluate('M.setParams({BodyX:.5,BodyY:.15,AngleZ:5});M.renderStill(1200)');settled=page.evaluate(geometry)
 check('after motion stop all masses settle down even with head tilted',all(abs(d['angle'])<.03 for d in settled),settled)
 # Released from rest at 25 degrees: gravity returns it and damping removes energy.
 energy=page.evaluate('''()=>{M.reset();M.renderStill(1);const d=M.rig.physics[0],s=M.phys[0].pendulum;s.theta=25*Math.PI/180;s.omega=0;const energy=()=>.5*d.length*d.length*s.omega*s.omega+d.gravity*d.length*(1-Math.cos(s.theta));const initial=energy();for(let i=0;i<60;i++)M._drive(1/240);const first=s.theta;for(let i=0;i<1860;i++)M._drive(1/240);return {initial,final:energy(),firstAngle:first*180/Math.PI,finalAngle:s.theta*180/Math.PI}}''')
 check('gravity restores and damping dissipates pendulum energy',energy['firstAngle']<25 and energy['final']/energy['initial']<.0001 and abs(energy['finalAngle'])<.03,energy)
 # Gravity must remain when sway sensitivity is zero.
 page.evaluate('M.reset();M.setParams({AngleZ:5,AccessoryGain:0});M.renderStill(300)');zero=page.evaluate(geometry);check('zero sway gain still hangs down',all(abs(d['angle'])<.03 for d in zero),zero)
 # Fixed tilt snapshots and a move-then-stop sequence: last frames show gravity, not source-pose recovery.
 sheet=Image.new('RGB',(1500,600),(40,42,50));draw=ImageDraw.Draw(sheet)
 for i,z in enumerate([-5,0,5]):
  page.evaluate('z=>{M.reset();M.setParam("AngleZ",z);M.renderStill(600)}',z);im=Image.open(io.BytesIO(page.locator('#c').screenshot(omit_background=True))).convert('RGBA');bg=Image.new('RGBA',im.size,(40,42,50));bg.alpha_composite(im);sheet.paste(bg.crop((545,345,830,480)).resize((1000//2,237)).convert('RGB'),(i*500,30));sheet.paste(bg.crop((875,665,1020,965)).resize((160,330)).convert('RGB'),(i*500+170,270));draw.text((i*500+5,8),'Head tilt '+str(z)+' / settled',fill='white')
 sheet.save(D/'gravity_at_rest.jpg')
 frames=[];page.evaluate('M.reset()')
 for n in range(60):
  page.evaluate('''n=>{const t=n*.1;M.setParams({BodyX:t<2?.24*Math.sin(t*3):.24*Math.sin(6),AngleZ:t<2?5*Math.sin(t*2):5*Math.sin(4)});M.renderStill(6)}''',n)
  im=Image.open(io.BytesIO(page.locator('#c').screenshot(omit_background=True))).convert('RGBA');bg=Image.new('RGBA',im.size,(40,42,50));bg.alpha_composite(im);frame=Image.new('RGB',(1000,620),(40,42,50));frame.paste(bg.crop((540,340,840,480)).resize((760,355)).convert('RGB'),(0,30));frame.paste(bg.crop((875,660,1020,965)).resize((225,475)).convert('RGB'),(775,60));ImageDraw.Draw(frame).text((10,8),'MOVING' if n<20 else 'STOPPED / gravity settles down',fill='white');frames.append(frame)
 frames[0].save(D/'gravity_move_stop.gif',save_all=True,append_images=frames[1:],duration=100,loop=0)
 check('no browser script errors',not errors,errors);b.close()
(D/'gravity8_results.json').write_text(json.dumps({'count':len(results),'passed':results,'scope':'2D pendulum and renderer, simulated movement; physical Mac camera/OBS unverified'},ensure_ascii=False,indent=2))

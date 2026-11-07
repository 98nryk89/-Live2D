"""Supplied neck surface: provenance, fixed base, curved sections, clipping and expression fidelity."""
from pathlib import Path
import json,zipfile,hashlib,io
import numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'docs/verification/repair_0.10.0';D.mkdir(exist_ok=True);checks=[]
def check(name,ok,detail=None):
 assert ok,(name,detail)
 checks.append({'name':name,'detail':detail});print('PASS',name,detail,flush=True)
def rig(s):return json.JSONDecoder().raw_decode(s.split('window.__RIG__=',1)[1])[0]
now=rig((R/'dist/mukachi_kachi_webcam.html').read_text());parts={p['id']:p for p in now['parts']}
with zipfile.ZipFile(R/'dist/mukachi_kachi_webcam_0.9.0.zip') as z:old=rig(z.read('Mukachi_Webcam_0.9.0/mukachi_kachi_webcam_0.9.0.html').decode())
oldparts={p['id']:p for p in old['parts']};unchanged=[k for k in oldparts if k.startswith(('eye_','mouth_','earring_','tassel_','companion','head_ear_','hair_behind_'))]
check('approved features textures meshes and effects unchanged',all(parts[k]['tex']==oldparts[k]['tex'] and parts[k]['mesh']==oldparts[k]['mesh'] and parts[k]['effects']==oldparts[k]['effects'] for k in unchanged),{'parts':len(unchanged)})
check('gravity and restrained amplitude unchanged',now['physics']==old['physics'] and now['params']==old['params'])
check('rigid head no longer stretches throat',not any(e.get('weight') for e in parts['head']['effects']) and 'neck_backing' not in parts)
check('shadow independent and clipped to supplied skin',parts['jaw_shadow']['clip']=='neck_skin' and parts['neck_skin']['z']<parts['body']['z']<parts['head']['z'])
record=json.loads((R/'projects/mukachi_kachi/neck_materials.json').read_text());check('original supplied skin preserved',hashlib.sha256((R/record['source']).read_bytes()).hexdigest()==record['sha256'])
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1350,'height':1165},device_scale_factor=1);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8089/mukachi_kachi_webcam.html');page.wait_for_function('window.READY===true');page.evaluate('M.stop();M.reset();M.auto={blink:false,idle:false,breath:false,physics:false,companionBlink:false};M.opts.view=[0,0,1350,1165]')
 page.add_style_tag(content='html,body,#stage{background:transparent!important}#app{display:block}#panel,#msg{display:none}#stage{width:1350px;height:1165px}')
 def shot():return Image.open(io.BytesIO(page.locator('#c').screenshot(omit_background=True))).convert('RGBA')
 for pose in [{'AngleZ':-5},{'AngleZ':-2.5},{'AngleZ':0},{'AngleZ':2.5},{'AngleZ':5},{'AngleX':5,'AngleY':-10,'AngleZ':5},{'AngleX':-5,'AngleY':5,'AngleZ':-5}]:
  geometry=page.evaluate('''pose=>{M.reset();M.setParams(pose);M.renderStill();const n=M.byId.neck_skin,d=n.effects[0].definition,f=L2DNeck.frame(d,M.params),a=L2DNeck.point(d,M.params,d.sourceCenterX,d.restTop),z=L2DNeck.point(d,M.params,d.sourceCenterX,d.restBottom);let folds={};for(const id of ['head','neck_skin']){const p=M.byId[id],ix=p.mesh.tris;const area=(v,i,j,k)=>(v[j*2]-v[i*2])*(v[k*2+1]-v[i*2+1])-(v[j*2+1]-v[i*2+1])*(v[k*2]-v[i*2]);let count=0;for(let i=0;i<ix.length;i+=3)if(area(p._rest,...ix.slice(i,i+3))*area(p._pos,...ix.slice(i,i+3))<=0)count++;folds[id]=count}return {topError:Math.hypot(a[0]-f.points[0][0],a[1]-f.points[0][1]),baseError:Math.hypot(z[0]-d.base[0],z[1]-d.base[1]),folds,collar:Math.max(...M.byId.collar._pos.map((v,i)=>Math.abs(v-M.byId.collar._rest[i])))}}''',pose)
  check('jaw attachment fixed base and unfolded surface '+str(pose),geometry['topError']<1e-6 and geometry['baseError']<1e-6 and geometry['collar']==0 and all(v==0 for v in geometry['folds'].values()),geometry)
  im=np.array(shot());check('no interior neck transparency '+str(pose),bool(np.all(im[438:475,642:737,3]>245)))
 # Compare the actual rendered face against the accepted frame, not only texture metadata.
 page.evaluate('M.reset();M.renderStill()');neutral=shot();reference=Image.open(R/'docs/verification/repair_0.9.0/upright_placement_reference.png').convert('RGBA');box=(555,250,815,390);diff=np.abs(np.array(neutral.crop(box)).astype(float)-np.array(reference.crop(box)).astype(float));check('rendered face unchanged',float(diff.mean())<.2,{'mean_rgba_error':float(diff.mean())})
 # A clipped shadow may not extend beyond the opaque skin when every other layer is hidden.
 page.evaluate("for(const p of M.parts)p.opacity=p.id==='neck_skin'?1:0;M.renderStill()");skin=np.array(shot())[:,:,3]
 page.evaluate("M.byId.neck_skin.maskOnly=true;M.byId.jaw_shadow.opacity=1;M.renderStill()");shadow=np.array(shot())[:,:,3]
 import cv2
 allowed=cv2.dilate((skin>16).astype(np.uint8),np.ones((5,5),np.uint8));check('jaw shadow never floats outside skin',not np.any((shadow>16)&(allowed==0)))
 page.evaluate('for(const p of M.parts){delete p.opacity;delete p.maskOnly}M.reset();M.renderStill()')
 # Pose proof and a continuous, small head roll, with lower collar stationary.
 sheet=Image.new('RGB',(1650,850),(40,42,50));draw=ImageDraw.Draw(sheet)
 for i,z in enumerate([-5,0,5]):
  page.evaluate('z=>{M.reset();M.setParam("AngleZ",z);M.renderStill()}',z);im=shot();bg=Image.new('RGBA',im.size,(40,42,50));bg.alpha_composite(im);sheet.paste(bg.crop((340,0,1020,680)).resize((550,550)).convert('RGB'),(i*550,30));sheet.paste(bg.crop((570,380,790,500)).resize((550,300)).convert('RGB'),(i*550,550));draw.text((i*550+8,8),str(z),fill='white')
 sheet.save(D/'neck_review.jpg')
 beforeafter=Image.new('RGB',(1200,380),(40,42,50));draw=ImageDraw.Draw(beforeafter)
 for i,(label,im) in enumerate([('0.9.0',reference),('0.10.0',neutral)]):
  bg=Image.new('RGBA',im.size,(40,42,50));bg.alpha_composite(im);beforeafter.paste(bg.crop((570,375,810,515)).resize((600,350)).convert('RGB'),(600*i,30));draw.text((600*i+8,8),label,fill='white')
 beforeafter.save(D/'neck_before_after.jpg')
 frames=[];page.evaluate('M.reset();M.auto.physics=true;M.auto.companionBlink=true')
 for n in range(40):
  page.evaluate('n=>{M.setParam("AngleZ",5*Math.sin(n*.1*Math.PI/2));M.renderStill(6)}',n);im=shot();bg=Image.new('RGBA',im.size,(40,42,50));bg.alpha_composite(im);frame=Image.new('RGB',(1100,600),(40,42,50));frame.paste(bg.crop((340,0,1020,680)).resize((600,600)).convert('RGB'),(0,0));frame.paste(bg.crop((585,370,805,510)).resize((500,318)).convert('RGB'),(600,120));frames.append(frame)
 frames[0].save(D/'neck_motion.gif',save_all=True,append_images=frames[1:],duration=100,loop=0)
 check('no browser script errors',not errors,errors);b.close()
(D/'neck10_results.json').write_text(json.dumps({'count':len(checks),'passed':checks,'scope':'geometry, image fidelity and actual renderer; appearance still requires user review; physical Mac camera/OBS unverified'},ensure_ascii=False,indent=2))

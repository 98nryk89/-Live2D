"""Regression for upright neutral, collar stability and movement-driven ornaments."""
from pathlib import Path
import io,json,zipfile,base64
import cv2,numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'docs/verification/repair_0.6.0';D.mkdir(exist_ok=True);checks=[]
def check(name,ok,detail=None):
 assert ok,(name,detail)
 checks.append({'name':name,'detail':detail});print('PASS',name,flush=True)
def rig_html(s):return json.JSONDecoder().raw_decode(s.split('window.__RIG__=',1)[1])[0]
html=(R/'dist/mukachi_kachi_webcam.html').read_text();rig=rig_html(html);parts={p['id']:p for p in rig['parts']}
with zipfile.ZipFile(R/'dist/mukachi_kachi_webcam_0.5.0.zip') as z:old=rig_html(z.read('Mukachi_Webcam_0.5.0/mukachi_kachi_webcam_0.5.0.html').decode())
oldparts={p['id']:p for p in old['parts']}
kept=[k for k in oldparts if k.startswith(('eye_','mouth_','earring_','tassel_','head_ear_','companion','hair_behind_'))]
check('accepted cutouts, eye and mouth images/meshes unchanged',all(parts[k]['tex']==oldparts[k]['tex'] and parts[k]['mesh']==oldparts[k]['mesh'] for k in kept),{'layers':len(kept)})
check('all nine ornaments have zero autonomous sway',len(rig['physics'])==9 and all(p.get('sway',0)==0 for p in rig['physics']))
def png(pid):return cv2.imdecode(np.frombuffer(base64.b64decode(parts[pid]['tex'].split(',',1)[1]),np.uint8),-1)
neck=png('neck');check('old collar line excluded from moving neck',all(neck[y,x,3]==0 for x,y in [(630,457),(649,466),(731,461),(750,442)]))
collar=png('collar');src=cv2.imread(str(R/'character_materials/mukachi_kachi/base.png'),-1);mask=collar[:,:,3]>0
check('fixed collar uses original pixels',np.array_equal(collar[mask],src[mask]))
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1350,'height':1165},device_scale_factor=1);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8089/mukachi_kachi_webcam.html');page.wait_for_function('window.READY===true');page.evaluate('M.stop();M.reset();M.auto={blink:false,breath:false,idle:false,physics:false};M.opts.view=[0,0,1350,1165]')
 page.add_style_tag(content='html,body,#stage{background:transparent!important}#app{display:block}#panel,#msg{display:none}#stage{width:1350px;height:1165px}')
 page.evaluate('M.renderStill()');shot=Image.open(io.BytesIO(page.locator('#c').screenshot(omit_background=True))).convert('RGBA');im=np.array(shot)
 centers=[]
 for x0,y0,x1,y1 in [(620,290,674,329),(731,290,773,329)]:
  r=im[y0:y1,x0:x1,:3].astype(float);rr,g,bb=r[:,:,0],r[:,:,1],r[:,:,2];w=np.clip(g-np.maximum(bb,rr),0,None);y,x=np.mgrid[y0:y1,x0:x1];centers.append([float((w*x).sum()/w.sum()),float((w*y).sum()/w.sum())])
 check('actual neutral iris heights level within one pixel',abs(centers[1][1]-centers[0][1])<1,centers)
 limits=page.evaluate('()=>{M.setParam("AngleZ",-20);const l=M.params.AngleZ;M.setParam("AngleZ",20);return [l,M.params.AngleZ]}');check('both roll limits five degrees',limits==[-5,5],limits)
 for pose in [{'AngleZ':-5},{'AngleZ':0},{'AngleZ':5},{'AngleX':-5,'AngleY':-10,'AngleZ':-5},{'AngleX':5,'AngleY':5,'AngleZ':5}]:
  d=page.evaluate('''pose=>{M.reset();M.setParams(pose);M.renderStill();const fixed={};for(const id of ['collar','body','companion']){const p=M.byId[id];fixed[id]=Math.max(...p._pos.map((v,i)=>Math.abs(v-p._rest[i])))}let folds={};for(const id of ['head','neck']){const p=M.byId[id],ix=p.mesh.tris;const area=(v,i,j,k)=>(v[j*2]-v[i*2])*(v[k*2+1]-v[i*2+1])-(v[j*2+1]-v[i*2+1])*(v[k*2]-v[i*2]);let n=0;for(let i=0;i<ix.length;i+=3)if(area(p._rest,...ix.slice(i,i+3))*area(p._pos,...ix.slice(i,i+3))<=0)n++;folds[id]=n}return {fixed,folds}}''',pose)
  check('collar/body/bear fixed and neck/head not folded '+str(pose),all(v==0 for v in d['fixed'].values()) and all(v==0 for v in d['folds'].values()),d)
 page.evaluate('M.reset();M.auto.physics=true;M.renderStill(180)')
 still=page.evaluate('M.rig.physics.map(p=>M.params[p.output])');check('stationary character produces no ornament motion',all(abs(x)<1e-10 for x in still),still)
 frames=[];rows=[]
 for n in range(40):
  data=page.evaluate('''n=>{const t=n*.1;M.setParams({BodyX:.30*Math.sin(t*3.2),BodyY:.12*Math.sin(t*2.7),AngleZ:5*Math.sin(t*2.4),AngleX:2*Math.sin(t*2.2)});M.renderStill(6);return M.rig.physics.map(p=>({id:p.output,value:M.params[p.output]}))}''',n);rows.append(data)
  if n%2==0:
   raw=Image.open(io.BytesIO(page.locator('#c').screenshot(omit_background=True))).convert('RGBA');bg=Image.new('RGBA',raw.size,(40,42,50));bg.alpha_composite(raw)
   frame=Image.new('RGB',(980,650),(25,27,32));frame.paste(bg.resize((753,650)).convert('RGB'),(0,0));frame.paste(bg.crop((885,670,1015,965)).resize((220,500)).convert('RGB'),(755,45));ImageDraw.Draw(frame).text((755,15),'Motion-driven',fill='white');frames.append(frame)
 amplitudes={r['id']:float(np.ptp([row[i]['value'] for row in rows])) for i,r in enumerate(rows[0])}
 check('all nine ornaments respond to character movement',all(v>.04 for v in amplitudes.values()),amplitudes)
 page.evaluate('M.setParams({BodyX:0,BodyY:0,AngleZ:0,AngleX:0});M.renderStill(300)')
 residual=page.evaluate('Math.max(...M.rig.physics.map(p=>Math.abs(M.params[p.output])))');check('ornaments settle after movement stops',residual<.001,residual)
 frames[0].save(D/'movement_driven.gif',save_all=True,append_images=frames[1:],duration=200,loop=0)
 # Authored face expressions still select exactly one eye/mouth texture per side.
 for smile,ids in [(1,['eye_left_smile','eye_right_smile']),(0,['eye_left_0','eye_right_0'])]:
  selected=page.evaluate('''smile=>{M.setParams({Smile:smile,EyeLOpen:0,EyeROpen:0});M.renderStill();return M.parts.filter(p=>p.id.startsWith('eye_')&&p._opacity>.5).map(p=>p.id)}''',smile);check('smile/closed eye selection '+str(smile),selected==ids,selected)
 check('no browser script errors',not errors,errors);b.close()
(D/'revision6_results.json').write_text(json.dumps({'count':len(checks),'passed':checks,'scope':'renderer and simulated movement; physical Mac camera and OBS unverified'},ensure_ascii=False,indent=2))
print('TOTAL',len(checks))

"""Left-only face extension: preserve old neck and accepted range, verify real renderer."""
from pathlib import Path
import io,json,zipfile,copy,math
import numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'docs/verification/repair_0.12.0';D.mkdir(exist_ok=True);checks=[]
def check(name,ok,detail=None):
 assert ok,(name,detail)
 checks.append({'name':name,'detail':detail});print('PASS',name,detail,flush=True)
def rig(s):return json.JSONDecoder().raw_decode(s.split('window.__RIG__=',1)[1])[0]
html=(R/'dist/mukachi_kachi_webcam.html').read_text();now=rig(html)
with zipfile.ZipFile(R/'dist/mukachi_kachi_webcam_0.11.0.zip') as z:oldhtml=z.read('Mukachi_Webcam_0.11.0/mukachi_kachi_webcam_0.11.0.html').decode()
old=rig(oldhtml);prev={p['id']:p for p in old['parts']}
check('all original textures and meshes unchanged',all(p['tex']==prev[p['id']]['tex'] and p['mesh']==prev[p['id']]['mesh'] for p in now['parts']))
ne=copy.deepcopy(next(p for p in now['parts'] if p['id']=='neck'));ne['effects'][0].pop('rollBounds');check('neck definition otherwise identical to 0.11',ne==prev['neck'])
check('only AngleZ parameter changed', [p for p in now['params'] if p['id']!='AngleZ']==[p for p in old['params'] if p['id']!='AngleZ'])
z=next(p for p in now['params'] if p['id']=='AngleZ');check('face left8 right5',z['min']==-8 and z['max']==5)
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 errors=[]
 def setup(url):
  p=b.new_page(viewport={'width':1350,'height':1165},device_scale_factor=1);p.on('pageerror',lambda e:errors.append(str(e)));p.goto(url);p.wait_for_function('window.READY===true');p.evaluate('M.stop();M.reset();M.auto={blink:false,idle:false,breath:false,physics:false,companionBlink:false};M.opts.view=[0,0,1350,1165]');p.add_style_tag(content='html,body,#stage{background:transparent!important}#app{display:block}#panel,#msg{display:none}#stage{width:1350px;height:1165px}');return p
 p=setup('http://127.0.0.1:8089/mukachi_kachi_webcam.html');temp=R/'dist/_previous12.html';temp.write_text(oldhtml);op=setup('http://127.0.0.1:8089/_previous12.html')
 def pose(pg,z,x=0,y=0):pg.evaluate('v=>{M.reset();M.setParams(v);M.renderStill()}',{'AngleZ':z,'AngleX':x,'AngleY':y})
 def shot(pg):return Image.open(io.BytesIO(pg.locator('#c').screenshot(omit_background=True))).convert('RGBA')
 for z in [-5,0,5]:
  pose(p,z);pose(op,z);check('accepted pose pixels identical '+str(z),np.array_equal(np.array(shot(p)),np.array(shot(op))))
 pose(p,-5);n5=p.evaluate('Array.from(M.byId.neck._pos)');pose(p,-8);check('neck at left8 exactly equals neck at left5',n5==p.evaluate('Array.from(M.byId.neck._pos)'))
 vals=[]
 for z in [0,-5,-8,5]:
  pose(p,z)
  vals.append(p.evaluate('''()=>{const r=new Float32Array([620,300,740,300,687,435]),q={_rest:r,_pos:new Float32Array(6),effects:M.byId.head.effects};M._deform(q);return {angle:Math.atan2(q._pos[3]-q._pos[1],q._pos[2]-q._pos[0])*180/Math.PI,jaw:Array.from(q._pos.slice(4))}}'''))
 check('left face adds exactly3 degrees, right stays5',abs(vals[2]['angle']-vals[0]['angle']+8)<.001 and abs(vals[3]['angle']-vals[0]['angle']-5)<.001,vals)
 check('extra face rotation keeps transformed jaw pivot fixed',max(abs(a-b) for a,b in zip(vals[1]['jaw'],vals[2]['jaw']))<.0001)
 for x,y,z in [(0,0,-8),(5,-10,-8),(-5,5,-8),(0,0,5)]:
  pose(p,z,x,y)
  folds=p.evaluate('''()=>{let a={};for(const id of ['head','neck']){let p=M.byId[id],ix=p.mesh.tris,n=0;const area=(v,i,j,k)=>(v[j*2]-v[i*2])*(v[k*2+1]-v[i*2+1])-(v[j*2+1]-v[i*2+1])*(v[k*2]-v[i*2]);for(let i=0;i<ix.length;i+=3)if(area(p._rest,...ix.slice(i,i+3))*area(p._pos,...ix.slice(i,i+3))<=0)n++;a[id]=n}return a}''')
  check('no head/neck folds '+str((x,y,z)),all(n==0 for n in folds.values()),folds)
  im=np.array(shot(p));check('interior neck remains opaque '+str((x,y,z)),bool(np.all(im[438:475,642:737,3]>200)))
 pose(p,-8,5,-10)
 a=p.evaluate('''()=>{M.auto.physics=true;M.renderStill(600);return M.rig.physics.map(d=>{const r=new Float32Array([...d.pivot,...d.com]),q={_rest:r,_pos:new Float32Array(4),effects:M.byId[d.part].effects};M._deform(q);const f=L2DGravity.frame(d,M.params);return {id:d.part,error:Math.hypot(q._pos[0]-f.pivot[0],q._pos[1]-f.pivot[1]),angle:Math.atan2(-(q._pos[2]-q._pos[0]),q._pos[3]-q._pos[1])*180/Math.PI}})}''')
 check('accessories attach and settle downward at new limit',all(v['error']<.0003 and abs(v['angle'])<.03 for v in a),a);p.evaluate('M.auto.physics=false')
 sheet=Image.new('RGB',(1650,850),(40,42,50));draw=ImageDraw.Draw(sheet)
 for i,(label,z) in enumerate([('Before / screen left 5',-5),('Now / screen left 8',-8),('Unchanged / screen right 5',5)]):
  pose(p,z);im=shot(p);bg=Image.new('RGBA',im.size,(40,42,50));bg.alpha_composite(im);sheet.paste(bg.crop((340,0,1020,680)).resize((550,550)).convert('RGB'),(i*550,30));sheet.paste(bg.crop((570,375,810,515)).resize((550,320)).convert('RGB'),(i*550,530));draw.text((i*550+8,8),label,fill='white')
 sheet.save(D/'neck_review.jpg');sheet.save(D/'neck_before_after.jpg')
 check('no browser script errors',not errors,errors);op.close();temp.unlink();b.close()
(D/'face_left12_results.json').write_text(json.dumps({'count':len(checks),'passed':checks,'scope':'rendered model and geometry; physical Mac camera and OBS unverified'},ensure_ascii=False,indent=2))

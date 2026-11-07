"""Completed V neck behavior, original painted contour/shadow, and current expression/physics regressions."""
from pathlib import Path
import io,json,zipfile,base64,hashlib
import numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'docs/verification/repair_0.11.0';D.mkdir(exist_ok=True);checks=[]
def check(name,ok,detail=None):
 assert ok,(name,detail)
 checks.append({'name':name,'detail':detail});print('PASS',name,detail,flush=True)
def rig(s):return json.JSONDecoder().raw_decode(s.split('window.__RIG__=',1)[1])[0]
html=(R/'dist/mukachi_kachi_webcam.html').read_text();now=rig(html);parts={p['id']:p for p in now['parts']}
with zipfile.ZipFile(R/'dist/mukachi_kachi_webcam_0.10.0.zip') as z:previous_html=z.read('Mukachi_Webcam_0.10.0/mukachi_kachi_webcam_0.10.0.html').decode();previous=rig(previous_html)
old={p['id']:p for p in previous['parts']};reference=json.loads((R/'reference_sources/v_completed_neck.json').read_text())
for p in reference['params']:
 current=next(x for x in now['params'] if x['id']==p['id']);check('V completed '+p['id']+' range',current['min']==p['min'] and current['max']==p['max'],[current['min'],current['max']])
weight=parts['neck']['effects'][0]['weight'];scale=55/(640-568);expected={'mode':'y','from':490.0,'to':435+(540-568)*scale}
check('V linear neck weighting mapped by jaw/collar landmarks',weight==expected,weight)
check('V pivot mapped above collar rather than previous low pivot',abs(parts['head']['effects'][0]['pivot'][1]-(435+(610-568)*scale))<1e-8,parts['head']['effects'][0]['pivot'])
check('V cylindrical neck depth is active',parts['neck']['effects'][0]['vz'] and parts['neck']['effects'][0]['k']==1 and len(parts['neck']['mesh']['z'])==len(parts['neck']['mesh']['verts'])//2)
check('generated neck and separate invented shadow removed',not any(k in parts for k in ['neck_skin','jaw_shadow','neck_backing']) and 'L2DNeck' not in html and 'neck-tube' not in html)
source=np.array(Image.open(R/'character_materials/mukachi_kachi/base.png').convert('RGBA'));neck=np.array(Image.open(io.BytesIO(base64.b64decode(parts['neck']['tex'].split(',',1)[1]))).convert('RGBA'))
for x,y in [(631,435),(748,440),(650,435),(675,450),(700,460)]:
 check('original contour/shading RGB preserved '+str((x,y)),neck[y,x,3]>200 and np.array_equal(neck[y,x,:3],source[y,x,:3]),neck[y,x].tolist())
for x,y in [(631,435),(748,440)]:check('dark neck outline retained '+str((x,y)),int(neck[y,x,:3].mean())<110)
kept=[k for k in old if k.startswith(('eye_','mouth_','earring_','tassel_','head_ear_','hair_behind_','companion'))]
check('accepted expressions/cutouts retained',all(parts[k]['tex']==old[k]['tex'] and parts[k]['mesh']==old[k]['mesh'] for k in kept),{'parts':len(kept)})
check('input ranges and small accessory gain unchanged',now['params']==previous['params'])
for a,b in zip(now['physics'],previous['physics']):
 a=dict(a);b=dict(b);a.pop('parentHead',None);b.pop('parentHead',None);check('pendulum settings retained '+a['part'],a==b)
metadata=json.loads((R/'projects/mukachi_kachi/v_neck_materials.json').read_text());check('neck source is original base only',metadata['generated_neck_layers_used']==[] and hashlib.sha256((R/metadata['source']).read_bytes()).hexdigest()==metadata['source_sha256'])
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1350,'height':1165},device_scale_factor=1);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8089/mukachi_kachi_webcam.html');page.wait_for_function('window.READY===true');page.evaluate('M.stop();M.reset();M.auto={blink:false,idle:false,breath:false,physics:false,companionBlink:false};M.opts.view=[0,0,1350,1165]');page.add_style_tag(content='html,body,#stage{background:transparent!important}#app{display:block}#panel,#msg{display:none}#stage{width:1350px;height:1165px}')
 def shot():return Image.open(io.BytesIO(page.locator('#c').screenshot(omit_background=True))).convert('RGBA')
 for pose in [{'AngleZ':-5},{'AngleZ':-2.5},{'AngleZ':0},{'AngleZ':2.5},{'AngleZ':5},{'AngleX':5,'AngleY':-10,'AngleZ':5},{'AngleX':-5,'AngleY':5,'AngleZ':-5}]:
  g=page.evaluate('''pose=>{M.reset();M.setParams(pose);M.renderStill();let folds={};for(const id of ['head','neck']){const p=M.byId[id],ix=p.mesh.tris;let count=0;const area=(v,i,j,k)=>(v[j*2]-v[i*2])*(v[k*2+1]-v[i*2+1])-(v[j*2+1]-v[i*2+1])*(v[k*2]-v[i*2]);for(let i=0;i<ix.length;i+=3)if(area(p._rest,...ix.slice(i,i+3))*area(p._pos,...ix.slice(i,i+3))<=0)count++;folds[id]=count}const n=M.byId.neck;let base=0;for(let i=0;i<n._pos.length;i+=2)if(n._rest[i+1]>=490)base=Math.max(base,Math.abs(n._pos[i]-n._rest[i]),Math.abs(n._pos[i+1]-n._rest[i+1]));return {folds,base}}''',pose)
  check('V neck base fixed and no folded meshes '+str(pose),all(v==0 for v in g['folds'].values()) and g['base']==0,g)
  a=np.array(shot())[:,:,3];check('no interior neck holes '+str(pose),bool(np.all(a[438:475,642:737]>200)),{'min_alpha':int(a[438:475,642:737].min())})
 page.evaluate('M.reset();M.renderStill()');neutral=shot();accepted=Image.open(R/'docs/verification/repair_0.9.0/upright_placement_reference.png').convert('RGBA');box=(555,250,815,390);delta=np.abs(np.array(neutral.crop(box)).astype(float)-np.array(accepted.crop(box)).astype(float));check('neutral face retained',float(delta.mean())<.25,{'mean_rgba_error':float(delta.mean())})
 # Geometry of the new head parent must also match gravity's attachment projection.
 a=page.evaluate('''()=>{M.reset();M.setParams({AngleZ:5,AngleX:5,AngleY:-10});M.auto.physics=true;M.renderStill(600);return M.rig.physics.map(d=>{const p=M.byId[d.part],r=new Float32Array([...d.pivot,...d.com]),q={_rest:r,_pos:new Float32Array(4),effects:p.effects};M._deform(q);const f=L2DGravity.frame(d,M.params);return {id:d.part,error:Math.hypot(q._pos[0]-f.pivot[0],q._pos[1]-f.pivot[1]),angle:Math.atan2(-(q._pos[2]-q._pos[0]),q._pos[3]-q._pos[1])*180/Math.PI}})}''')
 check('gravity attachments follow reference-based head pivot and settle down',all(v['error']<.0003 and abs(v['angle'])<.03 for v in a),a)
 page.evaluate('M.auto.physics=false;M.reset()')
 # Proof of visible source shading, fixed collar and complete trajectory.
 sheet=Image.new('RGB',(1650,850),(40,42,50));draw=ImageDraw.Draw(sheet)
 for i,z in enumerate([-5,0,5]):
  page.evaluate('z=>{M.reset();M.setParam("AngleZ",z);M.renderStill()}',z);im=shot();bg=Image.new('RGBA',im.size,(40,42,50));bg.alpha_composite(im);sheet.paste(bg.crop((340,0,1020,680)).resize((550,550)).convert('RGB'),(i*550,30));sheet.paste(bg.crop((570,375,810,515)).resize((550,320)).convert('RGB'),(i*550,530));draw.text((i*550+8,8),str(z),fill='white')
 sheet.save(D/'neck_review.jpg')
 temp=R/'dist/_previous_neck_render.html';temp.write_text(previous_html)
 oldpage=b.new_page(viewport={'width':1350,'height':1165},device_scale_factor=1)
 oldpage.goto('http://127.0.0.1:8089/_previous_neck_render.html');oldpage.wait_for_function('window.READY===true');oldpage.evaluate('M.stop();M.reset();M.auto={blink:false,idle:false,breath:false,physics:false,companionBlink:false};M.opts.view=[0,0,1350,1165]');oldpage.add_style_tag(content='html,body,#stage{background:transparent!important}#app{display:block}#panel,#msg{display:none}#stage{width:1350px;height:1165px}');oldpage.evaluate('M.renderStill()')
 prev=Image.open(io.BytesIO(oldpage.locator('#c').screenshot(omit_background=True))).convert('RGBA');oldpage.close();temp.unlink()
 # Stable source screenshots: material contrast is clearly shown against the rejected generated-neck output.
 proof=Image.new('RGB',(1200,380),(40,42,50));draw=ImageDraw.Draw(proof)
 for i,(label,im) in enumerate([('0.10.0 / generated neck',prev),('0.11.0 / original painted neck',neutral)]):
  bg=Image.new('RGBA',im.size,(40,42,50));bg.alpha_composite(im);proof.paste(bg.crop((570,375,810,515)).resize((600,350)).convert('RGB'),(i*600,30));draw.text((i*600+8,8),label,fill='white')
 proof.save(D/'neck_before_after.jpg')
 frames=[];page.evaluate('M.reset();M.auto.physics=true;M.auto.companionBlink=true')
 for n in range(40):
  page.evaluate('n=>{M.setParam("AngleZ",5*Math.sin(n*.1*Math.PI/2));M.renderStill(6)}',n);im=shot();bg=Image.new('RGBA',im.size,(40,42,50));bg.alpha_composite(im);frame=Image.new('RGB',(1100,600),(40,42,50));frame.paste(bg.crop((340,0,1020,680)).resize((600,600)).convert('RGB'),(0,0));frame.paste(bg.crop((585,370,805,510)).resize((500,318)).convert('RGB'),(600,120));frames.append(frame)
 frames[0].save(D/'neck_motion.gif',save_all=True,append_images=frames[1:],duration=100,loop=0)
 check('no browser script errors',not errors,errors);b.close()
(D/'v_neck11_results.json').write_text(json.dumps({'count':len(checks),'passed':checks,'scope':'V-source comparison, source RGB and renderer; physical Mac camera/OBS unverified; visual comparison remains necessary'},ensure_ascii=False,indent=2))

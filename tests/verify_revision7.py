"""Connected throat, paired bear eyelids, timed blinking and stronger reactive motion."""
from pathlib import Path
import json,zipfile,io,base64
import numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'docs/verification/repair_0.7.0';D.mkdir(exist_ok=True);results=[]
def check(name,ok,detail=None):
 assert ok,(name,detail)
 results.append({'name':name,'detail':detail});print('PASS',name,detail,flush=True)
def readrig(s):return json.JSONDecoder().raw_decode(s.split('window.__RIG__=',1)[1])[0]
rig=readrig((R/'dist/mukachi_kachi_webcam.html').read_text());parts={p['id']:p for p in rig['parts']}
with zipfile.ZipFile(R/'dist/mukachi_kachi_webcam_0.6.0.zip') as z:oldhtml=z.read('Mukachi_Webcam_0.6.0/mukachi_kachi_webcam_0.6.0.html').decode()
old=readrig(oldhtml);oldparts={p['id']:p for p in old['parts']};keep=[k for k in oldparts if k.startswith(('eye_','mouth_','earring_','tassel_','head_ear_','hair_behind_')) or k=='companion']
check('accepted features and cutouts unchanged',all(parts[k]['tex']==oldparts[k]['tex'] and parts[k]['mesh']==oldparts[k]['mesh'] for k in keep),{'layers':len(keep)})
check('head and throat use one connected mesh', 'neck' not in parts and parts['head']['effects'][0]['weight']['mode']=='neck')
check('old single clipped bear eye patch removed','companion_smile' not in parts)
for side,box in [('left',(427,403,466,441)),('right',(482,383,526,425))]:
 im=Image.open(io.BytesIO(base64.b64decode(parts['companion_eye_'+side+'_closed']['tex'].split(',',1)[1]))).convert('RGBA');actual=np.array(im);source=np.array(Image.open(R/'projects/mukachi_kachi/aligned/smile.png').convert('RGBA').crop(box));check('authored '+side+' closed eye RGB unchanged',np.array_equal(actual[:,:,:3],source[:,:,:3]));check(side+' pupil replacement opaque',bool(np.all(actual[10:25,13:29,3]==255)))
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1350,'height':1165},device_scale_factor=1);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8089/mukachi_kachi_webcam.html');page.wait_for_function('window.READY===true');check('bear blink enabled initially',page.evaluate('M.auto.companionBlink') and page.locator('#a_owlblink').is_checked())
 page.evaluate('M.stop();M.reset();M.auto={blink:false,idle:false,breath:false,physics:false,companionBlink:false};M.opts.view=[0,0,1350,1165]')
 page.add_style_tag(content='html,body,#stage{background:transparent!important}#app{display:block}#panel,#msg{display:none}#stage{width:1350px;height:1165px}')
 tiles=[]
 for label,smile,open_ in [('normal',0,1),('smile',1,1),('blink',0,0)]:
  selected=page.evaluate('''p=>{M.setParams({Smile:p[0],CompanionEyeOpen:p[1]});M.renderStill();return M.parts.filter(p=>p.id.startsWith('companion_eye_')&&p._opacity>.5).map(p=>p.id)}''',[smile,open_]);check(label+' selects complete eye pair',len(selected)==(0 if label=='normal' else 2),selected)
  im=Image.open(io.BytesIO(page.locator('#c').screenshot(omit_background=True))).convert('RGBA');bg=Image.new('RGBA',im.size,(45,47,55));bg.alpha_composite(im);tiles.append((label,bg.crop((395,380,540,460)).resize((580,320)).convert('RGB')))
 sheet=Image.new('RGB',(1740,360),(25,27,32));draw=ImageDraw.Draw(sheet)
 for i,(name,im) in enumerate(tiles):sheet.paste(im,(i*580,30));draw.text((i*580+10,7),name,fill='white')
 sheet.save(D/'bear_eyes.jpg')
 page.evaluate('document.getElementById("a_owlblink").click()');check('disabling bear blinking reopens eyes',page.evaluate('M.params.CompanionEyeOpen===1'));page.evaluate('document.getElementById("a_owlblink").click()')
 timing=page.evaluate('''()=>{M.reset();M.auto.companionBlink=true;let prev=false,onsets=[],paired=true;for(let n=1;n<=2700;n++){M._drive(.005);const closed=M.params.CompanionEyeOpen<.5;if(closed&&!prev){onsets.push(n*.005);M.renderStill();paired&&=M.parts.filter(p=>p.id.startsWith('companion_eye_')&&p._opacity>.5).length===2}prev=closed}return {onsets,paired}}''');check('bear blinks every four seconds independently',len(timing['onsets'])==3 and np.allclose(np.diff(timing['onsets']),4,atol=.01) and timing['paired'],timing)
 page.evaluate('M.reset();M.auto.companionBlink=false')
 for pose in [{'AngleZ':-5},{'AngleZ':0},{'AngleZ':5},{'AngleX':-5,'AngleY':-10,'AngleZ':-5},{'AngleX':5,'AngleY':5,'AngleZ':5}]:
  data=page.evaluate('''pose=>{M.reset();M.setParams(pose);M.renderStill();const h=M.byId.head,ix=h.mesh.tris;let folds=0;const area=(v,i,j,k)=>(v[j*2]-v[i*2])*(v[k*2+1]-v[i*2+1])-(v[j*2+1]-v[i*2+1])*(v[k*2]-v[i*2]);for(let i=0;i<ix.length;i+=3)if(area(h._rest,...ix.slice(i,i+3))*area(h._pos,...ix.slice(i,i+3))<=0)folds++;return {folds,collarDelta:Math.max(...M.byId.collar._pos.map((v,i)=>Math.abs(v-M.byId.collar._rest[i])))}}''',pose)
  check('continuous head/throat remains unfolded and collar fixed '+str(pose),data=={'folds':0,'collarDelta':0},data)
  raw=np.array(Image.open(io.BytesIO(page.locator('#c').screenshot(omit_background=True))));check('no holes within throat '+str(pose),bool(np.all(raw[435:475,648:726,3]>250)))
 # Same movement sequence in both releases isolates increased accessory sensitivity.
 drive='''()=>{M.reset();M.auto={blink:false,idle:false,breath:false,physics:true,companionBlink:false};const maxima={};for(let n=0;n<180;n++){const t=n/60;M.setParams({BodyX:.3*Math.sin(t*3.2),BodyY:.12*Math.sin(t*2.7),AngleZ:5*Math.sin(t*2.4)});M.renderStill(1);for(const p of M.rig.physics){const e=M.parts.flatMap(p=>p.effects).find(e=>e.type==='rotate'&&e.param===p.output);maxima[p.output]=Math.max(maxima[p.output]||0,Math.abs(M.params[p.output])*e.map[2][1])}}return maxima}'''
 current=page.evaluate(drive);page.evaluate('M.setParams({BodyX:0,BodyY:0,AngleZ:0});M.renderStill(300)');check('motion stops and ornaments settle',page.evaluate('Math.max(...M.rig.physics.map(p=>Math.abs(M.params[p.output])))')<.001)
 temp=R/'dist/_previous_verify.html';temp.write_text(oldhtml)
 page.goto('http://127.0.0.1:8089/_previous_verify.html');page.wait_for_function('window.READY===true');page.evaluate('M.stop()');previous=page.evaluate(drive);temp.unlink();ratio={k:current[k]/previous[k] for k in current};check('all nine ornaments more sensitive than previous release',len(ratio)==9 and min(ratio.values())>1.4,ratio)
 check('no browser script errors',not errors,errors);b.close()
(D/'revision7_results.json').write_text(json.dumps({'count':len(results),'passed':results,'scope':'actual browser rendering and simulated movement; physical Mac webcam and OBS unverified'},ensure_ascii=False,indent=2))

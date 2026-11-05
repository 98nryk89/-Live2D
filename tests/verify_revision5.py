from pathlib import Path
import io,json,zipfile,base64,re,hashlib,sys
import cv2,numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'docs/verification/repair_0.5.0';D.mkdir(exist_ok=True);sys.path.insert(0,str(R/'tools'))
from character_blinks import EYE_BOXES,ROLES,authored_eye_sprites
from character_segmentation import segmentation_masks
checks=[]
def check(name,ok,detail=None):
 assert ok,(name,detail)
 checks.append({'name':name,'detail':detail});print('PASS',name)
def rig_from_html(html):
 start=html.index('window.__RIG__=')+len('window.__RIG__=');return json.JSONDecoder().raw_decode(html[start:])[0]
html=(R/'dist/mukachi_kachi_webcam.html').read_text();rig=rig_from_html(html);parts={p['id']:p for p in rig['parts']}
with zipfile.ZipFile(R/'dist/mukachi_kachi_webcam_0.3.0.zip') as z:previous=rig_from_html(z.read('Mukachi_Webcam_0.3.0/mukachi_kachi_webcam_0.3.0.html').decode())
oldmouth={p['id']:p for p in previous['parts'] if p['id'].startswith('mouth_')}
check('all accepted mouth textures and meshes unchanged',all(parts[k]['tex']==p['tex'] and parts[k]['mesh']==p['mesh'] for k,p in oldmouth.items()),{'mouth_layers':len(oldmouth)})
check('no procedural blink frame set remains',rig.get('eyeMode')=='authored-three-poses' and all('eye_'+eye+'_'+str(i) not in parts for eye in ['left','right'] for i in range(3,40)))
for eye in ['left','right']:
 for i,role in enumerate(ROLES):
  part=parts['eye_'+eye+'_'+str(i)];png=base64.b64decode(part['tex'].split(',',1)[1]);got=cv2.imdecode(np.frombuffer(png,np.uint8),-1)
  x0,y0,x1,y1=EYE_BOXES[eye];source=cv2.imread(str(R/'projects/mukachi_kachi/aligned'/f'{role}.png'),-1)[y0:y1,x0:x1]
  check(eye+' '+role+' RGB copied from approved drawing',np.array_equal(got[:,:,:3],source[:,:,:3]))
  # Eye/core is opaque, so no old pupil can show through a transparent skin patch.
  core=got[:,:,3]>250;check(eye+' '+role+' has opaque eye core',core.sum()>1500,{'opaque_pixels':int(core.sum())})
def tex(pid):return cv2.imdecode(np.frombuffer(base64.b64decode(parts[pid]['tex'].split(',',1)[1]),np.uint8),-1)
head=tex('head');bear=tex('companion');original=cv2.imread(str(R/'character_materials/mukachi_kachi/base.png'),-1)
for x,y in [(493,350),(505,352),(514,353)]:
 check('bear ear belongs only to companion foreground '+str((x,y)),head[y,x,3]==0 and np.array_equal(bear[y,x],original[y,x]))
check('clean backing used for hair behind bear','hair_behind_companion' in parts and parts['hair_behind_companion']['z']<parts['companion']['z'])
# Smile eye assets are the literal original smile crops used before their removal.
check('original smile eyes restored',all(parts['eye_'+e+'_smile']['tex']==next(p['tex'] for p in previous['parts'] if p['id']=='eye_'+e+'_smile') for e in ['left','right']))
with zipfile.ZipFile(R/'dist/mukachi_kachi_webcam_0.4.0.zip') as z:
 old=rig_from_html(z.read('Mukachi_Webcam_0.4.0/mukachi_kachi_webcam_0.4.0.html').decode());oldparts={p['id']:p for p in old['parts']}
check('accepted three blink drawings unchanged',all(parts[f'eye_{e}_{i}']['tex']==oldparts[f'eye_{e}_{i}']['tex'] for e in ['left','right'] for i in range(3)))
masks=segmentation_masks(original)
for name,mask in masks.items():
 fg=tex(name)[:,:,3]>0
 check(name+' is cut along production mask',np.array_equal(fg,(mask>0)&(original[:,:,3]>0)))
 check(name+' pixels are absent from hair and body',not tex('head')[:,:,3][mask>0].any() and not tex('body')[:,:,3][mask>0].any())
with zipfile.ZipFile(R/'dist/mukachi_kachi_webcam_0.5.0.zip') as z:check('new ZIP contains exact verified HTML',z.testzip() is None and z.read('Mukachi_Webcam_0.5.0/mukachi_kachi_webcam_0.5.0.html')==html.encode())
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
 page=b.new_page(viewport={'width':1350,'height':1165},device_scale_factor=1);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8089/mukachi_kachi_webcam.html');page.wait_for_function('window.READY===true')
 page.evaluate('M.stop();M.auto={blink:false,breath:false,idle:false,physics:false};M.opts.view=[0,0,1350,1165]')
 page.add_style_tag(content='html,body,#stage{background:transparent!important}#app{display:block}#panel,#msg{display:none}#stage{width:1350px;height:1165px}')
 visible=page.evaluate("()=>{M.setParam('Smile',1);M.renderStill();return ['left','right'].map(e=>M.parts.filter(x=>x.id.startsWith('eye_'+e+'_')&&x._opacity>.5).map(x=>x.id))}")
 check('smile displays supplied smiling eyes',visible==[['eye_left_smile'],['eye_right_smile']],visible)
 page.locator('#c').screenshot(path=str(D/'smile.png'),omit_background=True)
 page.evaluate('M.reset()')
 tiles=[]
 for label,amount,index in [('open',1,2),('half',.5,1),('closed',0,0)]:
  visible=page.evaluate('''p=>{M.reset();M.setParams({EyeLOpen:p,EyeROpen:p});M.renderStill();return ['left','right'].map(e=>M.parts.filter(x=>x.id.startsWith('eye_'+e+'_')&&x._opacity>.5).map(x=>x.id))}''',amount)
  check(label+' selects exactly its supplied drawing',visible==[['eye_left_'+str(index)],['eye_right_'+str(index)]],visible)
  shot=Image.open(io.BytesIO(page.locator('#c').screenshot(omit_background=True))).convert('RGBA');bg=Image.new('RGBA',shot.size,(60,60,70,255));bg.alpha_composite(shot);tile=bg.crop((550,255,810,365)).resize((650,275)).convert('RGB');tiles.append((label,tile));shot.save(D/(label+'.png'))
 sheet=Image.new('RGB',(650*3,305),(50,50,60));draw=ImageDraw.Draw(sheet)
 for i,(name,tile) in enumerate(tiles):sheet.paste(tile,(i*650,0));draw.text((i*650+8,282),name,fill='white')
 sheet.save(D/'authored_blinks_rendered.jpg')
 # A monotone blink must visit only the three authored poses, in order, without image morphing.
 sequence=page.evaluate('''()=>{M.reset();const result=[];for(const p of [1,.8,.6,.4,.1,0,.2,.4,.6,.9,1]){M.setParams({EyeLOpen:p,EyeROpen:p});M.renderStill();result.push(M.parts.filter(x=>/^eye_left_[0-2]$/.test(x.id)&&x._opacity>.5).map(x=>x.id))}return result}''')
 check('blink uses only authored frames',all(len(x)==1 and x[0] in ['eye_left_0','eye_left_1','eye_left_2'] for x in sequence),sequence)
 for angle in [-5,10]:
  d=page.evaluate('''z=>{M.reset();M.setParam('AngleZ',z);M.renderStill();const p=M.byId.companion;return {angle:M.params.AngleZ,earDelta:Math.max(...Array.from(p._pos).map((v,i)=>Math.abs(v-p._rest[i])))}}''',angle)
  check('companion ear stationary under tilt '+str(angle),d['angle']==angle and d['earDelta']==0,d)
  page.locator('#c').screenshot(path=str(D/('split_tilt_'+str(angle)+'.png')),omit_background=True)
 limits=page.evaluate('''()=>{M.setParam('AngleZ',-20);const left=M.params.AngleZ;M.setParam('AngleZ',20);return [left,M.params.AngleZ]}''');check('left 5 right 10 degree limits',limits==[-5,10],limits)
 check('no browser script errors',not errors,errors);b.close()
(D/'revision5_results.json').write_text(json.dumps({'passed':checks,'count':len(checks),'scope':'approved-image fidelity, scene ownership and renderer; physical Mac webcam/OBS unverified'},ensure_ascii=False,indent=2))

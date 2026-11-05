from pathlib import Path
import io,json,sys,cv2,numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'docs/verification/repair_0.5.0';D.mkdir(exist_ok=True);checks=[]
def check(label,value,detail=None):
 assert value,(label,detail)
 checks.append({'name':label,'detail':detail});print('PASS',label)
sys.path.insert(0,str(R/'tools'));from character_features import mouth_sprites,mouth_feature
images={p.stem:cv2.imread(str(p),-1) for p in (R/'projects/mukachi_kachi/aligned').glob('*.png')}
# Every pixel outside the lips and their neutral erase region must remain original skin/outline.
sprites,box,bounds=mouth_sprites(images);x0,y0,x1,y1=box;source=images['base'][y0:y1,x0:x1]
_,_,erase,eraseBox=mouth_feature(images['base']);allowed=np.zeros(source.shape[:2],np.uint8)
ex,ey,ex1,ey1=eraseBox;allowed[ey-y0:ey1-y0,ex-x0:ex1-x0]=erase
for (role,level),s in sprites.items():
 x,y,w,h=bounds[role];mask=allowed.copy();mask[y-y0:y-y0+h,x-x0:x-x0+w]=255
 delta=np.abs(s[:,:,:3].astype(int)-source[:,:,:3].astype(int));check(f'mouth {role}/{level} preserves contour',not delta[mask==0].any())
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
 pg=b.new_page(viewport={'width':1350,'height':1165},device_scale_factor=1);errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
 pg.goto('http://127.0.0.1:8089/mukachi_kachi_webcam.html');pg.wait_for_function('window.READY===true')
 pg.evaluate('M.stop();M.auto={blink:false,idle:false,physics:false,breath:false};M.reset();M.opts.view=[0,0,1350,1165]')
 pg.add_style_tag(content='html,body,#stage{background:transparent!important}#app{display:block}#panel,#msg{display:none}#stage{width:1350px;height:1165px}')
 pg.evaluate('M.renderStill()');raw=pg.locator('#c').screenshot(omit_background=True)
 shot=Image.open(io.BytesIO(raw)).convert('RGBA');base=Image.open(R/'character_materials/mukachi_kachi/base.png').convert('RGBA');white=Image.new('RGBA',base.size,'white')
 a=np.array(Image.alpha_composite(white,base)).astype(float);bb=np.array(Image.alpha_composite(white,shot)).astype(float);err=np.abs(a[:,:,:3]-bb[:,:,:3]);check('neutral original image preserved',err.mean()<1,{'mean_rgb_error':float(err.mean())})
 shot.save(D/'neutral.png')
 face=(550,255,810,435);poses=[('open',{}),('75',{'EyeLOpen':.75,'EyeROpen':.75}),('50',{'EyeLOpen':.5,'EyeROpen':.5}),('25',{'EyeLOpen':.25,'EyeROpen':.25}),('closed',{'EyeLOpen':0,'EyeROpen':0}),('a',{'MouthOpen':1}),('i',{'MouthOpen':1,'MouthForm':1}),('e',{'MouthOpen':1,'MouthForm':2})]
 sheet=Image.new('RGB',(520*4,390*2),(44,43,51));draw=ImageDraw.Draw(sheet)
 for i,(name,params) in enumerate(poses):
  pg.evaluate('(p)=>{M.reset();M.setParams(p);M.renderStill()}',params);im=Image.open(io.BytesIO(pg.locator('#c').screenshot(omit_background=True))).convert('RGBA');crop=Image.alpha_composite(Image.new('RGBA',im.size,(60,60,70,255)),im).crop(face).resize((520,360)).convert('RGB');sheet.paste(crop,(i%4*520,i//4*390));draw.text((i%4*520+5,i//4*390+365),name,fill='white')
 sheet.save(D/'expressions_fixed.jpg')
 # Verify both roll directions, skin mesh orientation, and frame margins at full movement.
 pg.evaluate('M.opts.view=M.rig.view')
 for z in [-5,10]:
  data=pg.evaluate('''z=>{M.reset();M.setParams({AngleZ:z,BodyX:z>0?1:-1,BodyY:1});M.renderStill();let flipped=0;const p=M.byId.head,idx=p.mesh.tris,a=p._rest,b=p._pos;const cross=(v,i,j,k)=>(v[2*j]-v[2*i])*(v[2*k+1]-v[2*i+1])-(v[2*j+1]-v[2*i+1])*(v[2*k]-v[2*i]);for(let n=0;n<idx.length;n+=3)if(cross(a,...idx.slice(n,n+3))*cross(b,...idx.slice(n,n+3))<=0)flipped++;return {z:M.params.AngleZ,flipped}}''',z)
  check('roll cap and no folded mesh '+str(z),data['z']==z and data['flipped']==0,data)
  im=Image.open(io.BytesIO(pg.locator('#c').screenshot(omit_background=True)));alpha=np.array(im)[:,:,3];check('roll frame margin '+str(z),not(alpha[0].any() or alpha[-1].any() or alpha[:,0].any() or alpha[:,-1].any()))
  im.save(D/('tilt_'+str(z)+'.png'))
 # Accessories must move independently, and their anchor follows the same head/body transform.
 data=pg.evaluate('''()=>{M.reset();M.renderStill();const ids=M.parts.filter(p=>p.id.startsWith('earring_')||p.id.startsWith('tassel_')).map(p=>p.id);const before=Object.fromEntries(ids.map(id=>[id,Array.from(M.byId[id]._pos)]));M.auto.physics=true;M.setParam('BodyX',1);M.setParam('AngleZ',10);for(let i=0;i<40;i++)M._drive(1/60);M.renderStill();return ids.map(id=>({id,physics:M.params['Phys_'+id],delta:Math.max(...Array.from(M.byId[id]._pos).map((v,i)=>Math.abs(v-before[id][i])))}))}''')
 check('all dangling accessories have active springs',len(data)==9 and all(abs(d['physics'])>.0001 and d['delta']>.01 for d in data),data)
 pg.evaluate('M.auto.physics=false;M.setParams({AngleZ:0,BodyX:0});M._drive(1/60)');check('physics off settles ornaments',pg.evaluate('M.rig.physics.every(d=>M.params[d.output]===0)'))
 # Real tracker input calculation with controlled landmarks and rotation matrices (not physical hardware).
 tilt=pg.evaluate('''()=>{const model={params:{},setParam(k,v){this.params[k]=v},setParams(p){Object.assign(this.params,p)}};const t=new L2DTracker(model,{smooth:0,autoSmile:false,autoSurprise:false});const L=Array.from({length:478},()=>({x:.5,y:.5,z:0}));Object.assign(L[33],{x:.4,y:.4});Object.assign(L[263],{x:.6,y:.4});Object.assign(L[1],{x:.5,y:.48});Object.assign(L[152],{x:.5,y:.8});Object.assign(L[61],{x:.46,y:.65});Object.assign(L[291],{x:.54,y:.65});Object.assign(L[13],{y:.64});Object.assign(L[14],{y:.66});let angle=0; t.landmarker={detectForVideo(){const a=angle*Math.PI/180,c=Math.cos(a),s=Math.sin(a);return {faceLandmarks:[L],facialTransformationMatrixes:[{data:[c,s,0,0,-s,c,0,0,0,0,1,0,0,0,0,1]}]}}};t.feed(null,0);t.calibrate();angle=11;t.feed(null,33);const right=model.params.AngleZ;angle=-11;t.feed(null,66);return {right,left:model.params.AngleZ}}''')
 check('tracker limits left 5 and right 10 degrees',abs(tilt['right']-10)<.01 and abs(tilt['left']+5)<.01,tilt)
 check('no script errors',not errors,errors);b.close()
(D/'repair_results.json').write_text(json.dumps({'passed':checks,'count':len(checks),'physical_camera':'not tested'},ensure_ascii=False,indent=2))
print('TOTAL',len(checks))

"""Isolate ornament deformation from character motion; compare old/new neutral renders."""
from pathlib import Path
import json,zipfile,io
import numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'docs/verification/repair_0.6.0';results=[]
def check(name,ok,detail=None):
 assert ok,(name,detail)
 results.append({'name':name,'detail':detail});print('PASS',name,detail,flush=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1350,'height':1165},device_scale_factor=1);page.goto('http://127.0.0.1:8089/mukachi_kachi_webcam.html');page.wait_for_function('window.READY===true');page.evaluate('M.stop();M.reset();M.auto={blink:false,idle:false,breath:false,physics:true}')
 data=page.evaluate('''()=>{const maxima={};for(let n=0;n<160;n++){const t=n/60;M.setParams({BodyX:.3*Math.sin(t*3.2),BodyY:.12*Math.sin(t*2.7),AngleZ:5*Math.sin(t*2.4)});M.renderStill(1);const p=M.parts.filter(p=>/^(earring_|tassel_)/.test(p.id)),states=p.map(p=>M.params[p.effects[0].param]),before=p.map(p=>Array.from(p._pos));for(const x of p)M.params[x.effects[0].param]=0;M.renderStill();p.forEach((p,j)=>{const delta=Math.max(...p._pos.map((v,i)=>Math.abs(v-before[j][i])));maxima[p.id]=Math.max(maxima[p.id]||0,delta);M.params[p.effects[0].param]=states[j]})}return maxima}''')
 check('each ornament visibly deflects independently of body/head motion',len(data)==9 and min(data.values())>1,data)
 page.evaluate('M.reset();M.renderStill(120)');residual=page.evaluate('Math.max(...M.rig.physics.map(p=>Math.abs(M.params[p.output])))');check('reset produces no artificial ornament impulse',residual==0,residual)
 tilt=page.evaluate('''()=>{const m={params:{},setParam(k,v){this.params[k]=v},setParams(p){Object.assign(this.params,p)}};const t=new L2DTracker(m,{smooth:0,autoSmile:false,autoSurprise:false});const L=Array.from({length:478},()=>({x:.5,y:.5,z:0}));Object.assign(L[33],{x:.4,y:.4});Object.assign(L[263],{x:.6,y:.4});Object.assign(L[1],{x:.5,y:.48});Object.assign(L[152],{x:.5,y:.8});Object.assign(L[61],{x:.46,y:.65});Object.assign(L[291],{x:.54,y:.65});Object.assign(L[13],{y:.64});Object.assign(L[14],{y:.66});let angle=0;t.landmarker={detectForVideo(){const a=angle*Math.PI/180,c=Math.cos(a),s=Math.sin(a);return {faceLandmarks:[L],facialTransformationMatrixes:[{data:[c,s,0,0,-s,c,0,0,0,0,1,0,0,0,0,1]}]}}};t.feed(null,0);t.calibrate();angle=11;t.feed(null,33);const right=m.params.AngleZ;angle=-11;t.feed(null,66);return {right,left:m.params.AngleZ}}''');check('calibrated tracker clamps both directions to five degrees',tilt=={'right':5,'left':-5},tilt)
 page.evaluate('M.auto.physics=false;M.reset();M.opts.view=[0,0,1350,1165];M.renderStill()')
 page.add_style_tag(content='html,body,#stage{background:transparent!important}#app{display:block}#panel,#msg{display:none}#stage{width:1350px;height:1165px}');page.evaluate('M.renderStill()')
 after=Image.open(io.BytesIO(page.locator('#c').screenshot(omit_background=True))).convert('RGBA')
 for angle in [-5,0,5]:
  page.evaluate('angle=>{M.reset();M.setParam("AngleZ",angle);M.renderStill()}',angle);im=np.array(Image.open(io.BytesIO(page.locator('#c').screenshot(omit_background=True))))
  check('no transparency tears inside throat '+str(angle),bool(np.all(im[440:475,647:725,3]>250)))
 temp=R/'dist/_verification_previous.html'
 with zipfile.ZipFile(R/'dist/mukachi_kachi_webcam_0.5.0.zip') as z:temp.write_bytes(z.read('Mukachi_Webcam_0.5.0/mukachi_kachi_webcam_0.5.0.html'))
 page.goto('http://127.0.0.1:8089/_verification_previous.html');page.wait_for_function('window.READY===true');page.evaluate('M.stop();M.reset();M.auto={blink:false,idle:false,breath:false,physics:false};M.opts.view=[0,0,1350,1165];M.renderStill()');page.add_style_tag(content='html,body,#stage{background:transparent!important}#app{display:block}#panel,#msg{display:none}#stage{width:1350px;height:1165px}');page.evaluate('M.renderStill()')
 before=Image.open(io.BytesIO(page.locator('#c').screenshot(omit_background=True))).convert('RGBA');out=Image.new('RGB',(1200,640),(40,42,50));draw=ImageDraw.Draw(out)
 for i,(label,im) in enumerate([('0.5.0 / previous neutral',before),('0.6.0 / upright neutral',after)]):
  bg=Image.new('RGBA',im.size,(40,42,50));bg.alpha_composite(im);out.paste(bg.crop((350,0,1030,680)).resize((600,600)).convert('RGB'),(600*i,35));draw.text((600*i+10,10),label,fill='white')
 out.save(D/'neutral_before_after.jpg');temp.unlink();b.close()
(D/'motion6_results.json').write_text(json.dumps({'count':len(results),'passed':results,'scope':'rendering with simulated movement and tracker matrix; physical Mac webcam unverified'},ensure_ascii=False,indent=2))

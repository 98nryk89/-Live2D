from pathlib import Path
import json,sys,subprocess,types,cv2,numpy as np
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'docs/verification/repair_0.4.0';D.mkdir(exist_ok=True);sys.path.insert(0,str(R/'tools'))
from character_features import lip_axis,mouth_feature,mouth_axes,rotate_glyph
result=[]
def check(name,ok,detail=None):
 assert ok,(name,detail)
 result.append({'name':name,'detail':detail});print('PASS',name)
images={p.stem:cv2.imread(str(p),-1) for p in (R/'projects/mukachi_kachi/aligned').glob('*.png')}
axes=mouth_axes(images);check('normal lip axis is measured',-10<axes['base_axis_degrees_image']<-4,axes)
for role in ['mouth_i','mouth_e','smile']:
 glyph=mouth_feature(images[role])[0];flat=rotate_glyph(glyph,lip_axis(glyph));aligned=rotate_glyph(flat,-axes['base_axis_degrees_image'])
 # The corner axis is measured on the actual resampled glyph, not solely configuration metadata.
 measured=lip_axis(aligned)
 check(role+' follows normal lip slope',abs(measured-axes['base_axis_degrees_image'])<3.5,{'target':axes['base_axis_degrees_image'],'measured':measured})
glyph=mouth_feature(images['surprise'])[0]
aligned=rotate_glyph(rotate_glyph(glyph,lip_axis(glyph,round_mouth=True)),-axes['base_axis_degrees_image'])
measured=lip_axis(aligned,round_mouth=True)
check('rounded surprise follows normal lip axis',abs(measured-axes['base_axis_degrees_image'])<1.5,{'target':axes['base_axis_degrees_image'],'measured':measured})
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
 page=b.new_page();page.goto('http://127.0.0.1:8089/mukachi_kachi_webcam.html');page.wait_for_function('window.READY===true');page.evaluate('M.stop();M.auto={blink:false,physics:false,idle:false,breath:false}')
 for angle in [-5,5]:
  data=page.evaluate('''angle=>{M.reset();M.renderStill();const h=M.byId.head,body=M.byId.body;const rest=Array.from(h._rest);M.setParam('AngleZ',angle);M.renderStill();const rad=angle*Math.PI/180,c=Math.cos(rad),s=Math.sin(rad),cx=680,cy=485;let error=0;for(let i=0;i<rest.length;i+=2){const x=rest[i]-cx,y=rest[i+1]-cy;error=Math.max(error,Math.abs(h._pos[i]-(cx+x*c-y*s)),Math.abs(h._pos[i+1]-(cy+x*s+y*c)))}let bodyDelta=0;for(let i=0;i<body._rest.length;i++)bodyDelta=Math.max(bodyDelta,Math.abs(body._pos[i]-body._rest[i]));return {angle:M.params.AngleZ,maxRigidError:error,bodyDelta,effects:h.effects}}''',angle)
  check('entire head follows a single roll '+str(angle),data['maxRigidError']<.0002 and data['bodyDelta']<.0001,data)
 data=page.evaluate('''()=>{M.setParam('AngleZ',-12);const left=M.params.AngleZ;M.setParam('AngleZ',20);return {left,right:M.params.AngleZ}}''')
 check('both tilt ranges equal 5 degrees',data=={'left':-5,'right':5},data)
 # Splitting the head must preserve existing yaw/pitch behavior as well.
 for pose in [{'AngleX':-5},{'AngleX':5},{'AngleY':-10},{'AngleY':5},{'AngleX':5,'AngleY':-10,'AngleZ':5},{'AngleX':-5,'AngleY':-10,'AngleZ':-5}]:
  data=page.evaluate("""pose=>{M.reset();M.setParams(pose);M.renderStill();let flips={};for(const id of ['head','neck']){const p=M.byId[id],idx=p.mesh.tris;const cross=(v,i,j,k)=>(v[2*j]-v[2*i])*(v[2*k+1]-v[2*i+1])-(v[2*j+1]-v[2*i+1])*(v[2*k]-v[2*i]);let n=0;for(let j=0;j<idx.length;j+=3)if(cross(p._rest,...idx.slice(j,j+3))*cross(p._pos,...idx.slice(j,j+3))<=0)n++;flips[id]=n}return flips}""",pose)
  check('head and neck do not fold '+str(pose),all(v==0 for v in data.values()),data)
 b.close()
(D/'face_revision_results.json').write_text(json.dumps({'passed':result,'count':len(result),'physical_camera':'not tested'},ensure_ascii=False,indent=2))

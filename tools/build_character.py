"""Build a pixel-preserving continuous mesh and local expression replacements.
No generative repaint; only reference registration and geometric resampling.
"""
from pathlib import Path
import sys,json,copy,hashlib
import cv2,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from live2d_ai.build import make_mesh
from character_features import mouth_sprites,eye_sprites
from character_accessories import split_accessories
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'projects/mukachi_kachi';OUT=P/'out';OUT.mkdir(exist_ok=True)
images={p.stem:cv2.imread(str(p),-1) for p in (P/'aligned').glob('*.png')};base=images['base'];H,W=base.shape[:2]
weight={'mode':'y','from':615,'to':420,'excludeEllipses':[[465,462,112,106,.75]]}
head={'type':'head3d','yaw':'AngleX','pitch':'AngleY','roll':'AngleZ','center':[680,300],'pivot':[680,465],'Rx':245,'Ry':255,'Rz':155,'k':.65,'weight':weight}
effects=[head,{'type':'translate','param':'BodyX','map':[[-1,-135,0],[0,0,0],[1,135,0]]},{'type':'translate','param':'BodyY','map':[[-1,0,-70],[0,0,0],[1,0,70]]}]
parts=[]
backed,accessories=split_accessories(base,P)
def part(pid,im,x,y,selector=None):
 tex=pid+'.png';cv2.imwrite(str(OUT/tex),im)
 mesh=make_mesh(im[:,:,3]/255,x,y,12)
 es=copy.deepcopy(effects)
 if selector:es.insert(0,{'type':'feature','group':selector[0],'index':selector[1]})
 parts.append({'id':pid,'z':len(parts),'tex':tex,'mesh':mesh,'effects':es})
part('continuous_body_head',backed,0,0)

def patch(role,box,feather=7,warp=None):
 x0,y0,x1,y1=box;im=images[role][y0:y1,x0:x1].copy();h,w=im.shape[:2]
 if warp:
  cy,inner,amount=warp;cy-=y0
  # Compress only the selected feature, keeping the outer skin boundary fixed.
  yy,xx=np.mgrid[:h,:w].astype(np.float32)
  src=np.interp(yy.ravel(),[0,cy-inner*amount,cy+inner*amount,h-1],[0,cy-inner,cy+inner,h-1]).reshape(h,w).astype(np.float32)
  im=cv2.remap(im,xx,src,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
 yy,xx=np.mgrid[:h,:w];rx=(w-1)/2;ry=(h-1)/2
 radius=np.sqrt(((xx-rx)/rx)**2+((yy-ry)/ry)**2)
 a=np.clip((1-radius)*min(rx,ry)/feather,0,1)
 im[:,:,3]=np.rint(im[:,:,3]*a).astype(np.uint8)
 return im
# Fixed pupil/eyeball pixels are progressively occluded by 40 lid poses.
for eye in ['left','right']:
 sprites,box=eye_sprites(base,images['eyes_closed'],eye,levels=40)
 for level,sprite in enumerate(sprites):part('eye_'+eye+'_'+str(level),sprite,box[0],box[1],(eye,level))
 for role,index in [('smile',41),('surprise',42)]:part('eye_'+eye+'_'+role,patch(role,box),box[0],box[1],(eye,index))
mouths,box,mouth_bounds=mouth_sprites(images,levels=32)
for form,role in enumerate(['mouth_a','mouth_i','mouth_e']):
 for level in range(1,33):part(f'mouth_{form}_{level}',mouths[(role,level)],box[0],box[1],('mouth',form*32+level))
for role,index in [('smile',97),('surprise',98)]:part('mouth_'+role,mouths[(role,32)],box[0],box[1],('mouth',index))
(P/'mouth_feature_bounds.json').write_text(json.dumps(mouth_bounds,indent=2))
# Separate dangling ornaments, fixed anchor stays on the head/body.
physics=[]
for i,(name,sprite,x,y,pivot,is_head) in enumerate(accessories):
 part(name,sprite,x,y)
 es=parts[-1]['effects']
 if is_head:es[0].pop('weight',None)
 output='Phys_'+name
 es.insert(0,{'type':'rotate','param':output,'pivot':list(pivot),'map':[[-1,-4],[0,0],[1,4]],'gainParam':'AccessoryGain'})
 physics.append({'output':output,'inputs':[{'param':'AngleZ' if is_head else 'BodyX','gain':1 if is_head else 12},{'param':'BodyY','gain':5}],'freq':1.4+i*.08,'damp':.55,'inertia':.6,'drag':.3,'sway':.16})
# Only the small companion's eyes change on smiling; no shoulder/costume replacement.
box=(408,389,520,447)
part('companion_smile',patch('smile',box),box[0],box[1],('companion',1))
params=[]
def param(id,lo,hi,default,label,step=None):
 p={'id':id,'min':lo,'max':hi,'default':default,'label':label}
 if step:p['step']=step
 params.append(p)
for id,lo,hi,label in [('AngleX',-5,5,'顔 左右'),('AngleY',-10,5,'顔 下・上'),('AngleZ',-12,12,'顔 かしげ'),('BodyX',-1,1,'全体 左右'),('BodyY',-1,1,'全体 上下')]:param(id,lo,hi,0,label)
for id,label in [('EyeLOpen','左目'),('EyeROpen','右目')]:param(id,0,1,1,label)
param('MouthOpen',0,1,0,'口 開き');param('MouthForm',0,2,0,'口 0あ/1い/2え',1)
for id,label in [('Smile','笑顔'),('Surprise','驚き')]:param(id,0,1,0,label,1)
param('AccessoryGain',0,2,1,'アクセサリーの揺れ量')
for d in physics:params.append({'id':d['output'],'min':-1,'max':1,'default':0,'hidden':True})
rig={'version':1,'name':'無価値価値','modelId':'mukachi_kachi','size':[W,H],'view':[-210,-115,1770,1400],'params':params,'parts':parts,'physics':physics}
(OUT/'rig.json').write_text(json.dumps(rig,ensure_ascii=False,separators=(',',':')))
(P/'rig_spec.json').write_text(json.dumps({'method':'continuous mesh with local source-pixel replacements','head':head,'body_motion_px':[135,70],'independent_hair_physics':False,'hidden_region_backing':{'eyes':'local skin fill under moving lids','mouth':'neutral lip erased only','accessories':'local inpaint underneath selected dangling ornaments'},'mouth_steps':32,'eyes':'40 aperture poses; iris pixels not scaled','accessories':[a[0] for a in accessories],'limitations':['Continuous mesh; no separately reconstructed hidden hair/neck layers','Input closed-mouth misclassification remains an unverified baseline issue','Source silhouette colour fringe retained; local hidden ornament backing reconstructed']},ensure_ascii=False,indent=2))
print('built',len(parts),'mesh layers; source SHA',hashlib.sha256((ROOT/'character_materials/mukachi_kachi/base.png').read_bytes()).hexdigest())

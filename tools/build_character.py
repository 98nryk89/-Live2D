"""Build the original painted neck using the completed V rig as reference.
No generative repaint; only reference registration and geometric resampling.
"""
from pathlib import Path
import sys,json,copy,hashlib
import cv2,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from live2d_ai.build import make_mesh
from character_features import mouth_sprites,mouth_axes
from character_blinks import authored_eye_sprites
from character_accessories import split_accessories
from character_v_neck import split_original_neck
from character_segmentation import segmentation_masks
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'projects/mukachi_kachi';OUT=P/'out';OUT.mkdir(exist_ok=True)
images={p.stem:cv2.imread(str(p),-1) for p in (P/'aligned').glob('*.png')};base=images['base'];H,W=base.shape[:2]
v_reference=json.loads((ROOT/'reference_sources/v_completed_neck.json').read_text())
y_scale=(490-435)/(v_reference['fixed_neck_y']-v_reference['measured_chin_y'])
map_y=lambda y:435+(y-v_reference['measured_chin_y'])*y_scale
head={'type':'head3d','yaw':'AngleX','pitch':'AngleY','roll':'AngleZ','center':[680,300],'pivot':[687,map_y(v_reference['head']['pivot'][1])],'Rx':245,'Ry':255,'Rz':155,'k':.65,'restRoll':6.530486248611499,'restRollPivot':[687,435]}
head.update(rollBounds=[-5,5],extraRoll={'param': 'AngleZ', 'map': [[-8, -3], [-5, 0], [0, 0], [5, 0]], 'pivot': [687, 435]})
effects=[head,{'type':'translate','param':'BodyX','map':[[-1,-135,0],[0,0,0],[1,135,0]]},{'type':'translate','param':'BodyY','map':[[-1,0,-70],[0,0,0],[1,0,70]]}]
parts=[]
segmentation=segmentation_masks(base)
for name,mask in segmentation.items():cv2.imwrite(str(P/(name+'_foreground_mask.png')),mask)
backed,accessories=split_accessories(base,P,clean=images['clean_backing'])
def part(pid,im,x,y,selector=None):
 tex=pid+'.png';cv2.imwrite(str(OUT/tex),im)
 mesh=make_mesh(im[:,:,3]/255,x,y,6 if pid=="neck" else 4 if pid=="head" else 12)
 es=copy.deepcopy(effects)
 if selector:es.insert(0,{'type':'feature','group':selector[0],'index':selector[1]})
 parts.append({'id':pid,'z':len(parts),'tex':tex,'mesh':mesh,'effects':es})
neck_effect=copy.deepcopy(head)
neck_effect.pop('extraRoll',None)
neck_effect.update(vz=True,k=1,rigid=0,weight={'mode':'y','from':map_y(v_reference['neck']['effects'][1]['weight']['from']),'to':map_y(v_reference['neck']['effects'][1]['weight']['to'])})
# V's cylindrical neck depth, expressed in this character's existing face-depth units.
jaw_r2=((689-head['center'][0])/head['Rx'])**2+((435-head['center'][1])/head['Ry'])**2
face_z=head['k']*head['Rz']*np.sqrt(1-jaw_r2)
neck_depth=v_reference['neck_depth']*face_z/(v_reference['jaw_plane_depth']*v_reference['head']['k'])
for name,sprite in split_original_neck(backed,images['clean_backing'],segmentation):
 part(name,sprite,0,0)
 if name in ['body','collar','collar_backing','companion']:parts[-1]['effects']=copy.deepcopy(effects[1:])
 elif name=='neck':
  parts[-1]['effects']=[copy.deepcopy(neck_effect)]+copy.deepcopy(effects[1:]);parts[-1]['z']=-20
  vertices=np.array(parts[-1]['mesh']['verts']).reshape(-1,2)
  parts[-1]['mesh']['z']=(neck_depth*np.sqrt(np.clip(1-((vertices[:,0]-688)/63)**2,0,1))).round(3).tolist()
 if name=='collar_backing':parts[-1]['z']=-30
 if name=='companion':parts[-1]['z']=900
 if name=='collar':parts[-1]['z']=850


def patch(role,box,feather=7,warp=None,opaque_core=False):
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
 im[:,:,3]=np.rint((255 if opaque_core else im[:,:,3])*a).astype(np.uint8)
 return im
# Approved drawings only: closed, half-open, open. No generated intermediate poses.
for eye in ['left','right']:
 sprites,box,_=authored_eye_sprites(images,eye)
 for level,sprite in enumerate(sprites):part('eye_'+eye+'_'+str(level),sprite,box[0],box[1],(eye,level))
 for role,index in [('smile',41),('surprise',42)]:part('eye_'+eye+'_'+role,patch(role,box),box[0],box[1],(eye,index))
mouths,box,mouth_bounds=mouth_sprites(images,levels=32)
for form,role in enumerate(['mouth_a','mouth_i','mouth_e']):
 for level in range(1,33):part(f'mouth_{form}_{level}',mouths[(role,level)],box[0],box[1],('mouth',form*32+level))
for role,index in [('smile',97),('surprise',98)]:part('mouth_'+role,mouths[(role,32)],box[0],box[1],('mouth',index))
(P/'mouth_feature_bounds.json').write_text(json.dumps(mouth_bounds,indent=2))
(P/'mouth_angles.json').write_text(json.dumps(mouth_axes(images),indent=2))
# Separate dangling ornaments, fixed anchor stays on the head/body.
physics=[]
for i,(name,sprite,x,y,pivot,is_head) in enumerate(accessories):
 part(name,sprite,x,y)
 es=parts[-1]['effects']
 if not is_head:es.pop(0)
 output='Phys_'+name
 # The support is the actual attachment; alpha centroid approximates the mass centre.
 alpha=sprite[:,:,3].astype(float)/255;yy,xx=np.mgrid[:sprite.shape[0],:sprite.shape[1]]
 com=[float(x+(xx*alpha).sum()/alpha.sum()),float(y+(yy*alpha).sum()/alpha.sum())]
 definition={'mode':'gravity-pendulum','part':name,'output':output,'pivot':list(pivot),'com':com,'length':max(12,float(np.linalg.norm(np.array(com)-pivot))),'parentHead':copy.deepcopy(head) if is_head else None,'bodyScale':[135,70],'gravity':2200,'dampingRatio':.24,'accelerationFilter':.045,'limitDegrees':65}
 es.append({'type':'gravity-pendulum','definition':definition})
 physics.append(definition)

# Pair of complete authored closed eyes. Separate opaque cores cover both original pupils.
for side,box in [('left',(427,403,466,441)),('right',(482,383,526,425))]:
 sprite=patch('smile',box,feather=2,opaque_core=True)
 if side=='right':
  yy,xx=np.mgrid[box[1]:box[3],box[0]:box[2]]
  # The muzzle rises diagonally beside this eye; keep the replacement off the nose.
  sprite[:,:,3]=np.rint(sprite[:,:,3]*np.clip((xx-(491+.8*(yy-414)))/2,0,1)).astype(np.uint8)
 part('companion_eye_'+side+'_closed',sprite,box[0],box[1],('companion',1))
 parts[-1]['effects'].pop(1);parts[-1]['z']=901
params=[]
def param(id,lo,hi,default,label,step=None):
 p={'id':id,'min':lo,'max':hi,'default':default,'label':label}
 if step:p['step']=step
 params.append(p)
for id,lo,hi,label in [('AngleX',-5,5,'顔 左右'),('AngleY',-10,5,'顔 下・上'),('AngleZ',-8,5,'かしげ（顔 左8度・右5度）'),('BodyX',-1,1,'全体 左右'),('BodyY',-1,1,'全体 上下')]:param(id,lo,hi,0,label)
for id,label in [('EyeLOpen','左目'),('EyeROpen','右目')]:param(id,0,1,1,label)
param('MouthOpen',0,1,0,'口 開き');param('MouthForm',0,2,0,'口 0あ/1い/2え',1)
for id,label in [('Smile','笑顔'),('Surprise','驚き')]:param(id,0,1,0,label,1)
param('CompanionEyeOpen',0,1,1,'熊の目');params[-1]['hidden']=True
param('AccessoryGain',0,2,.5,'アクセサリーの揺れ量')
for d in physics:params.append({'id':d['output'],'min':-65,'max':65,'default':0,'hidden':True})
rig={'version':1,'name':'無価値価値','modelId':'mukachi_kachi','size':[W,H],'view':[-210,-115,1770,1400],'params':params,'parts':parts,'physics':physics,'eyeMode':'authored-three-poses'}
(OUT/'rig.json').write_text(json.dumps(rig,ensure_ascii=False,separators=(',',':')))
(P/'rig_spec.json').write_text(json.dumps({'method':'original painted neck; completed V head/neck/body layout','neck_connection':{'mesh':'neck','effect':neck_effect,'depth':float(neck_depth),'step':6,'reference':'reference_sources/v_completed_neck.json','materials':'projects/mukachi_kachi/v_neck_materials.json'},'companion_blink':{'period_seconds':4,'closed_eyes_source':'smile','independent':True},'head':head,'body_motion_px':[135,70],'independent_hair_physics':False,'hidden_region_backing':{'eyes':'approved sheet, open/half/closed source pixels only','mouth':'neutral lip erased only','accessories':'supplied clean backing beneath isolated ornaments'},'mouth_steps':32,'eyes':'three approved drawings, no local warps or synthetic intermediate frames','accessory_physics':{'mode':'gravity-pendulum','gravity_axis':'+Y','gravity':2200,'damping_ratio':.24,'limits_degrees':65,'motion_gain_default':.5},'accessories':[a[0] for a in accessories],'limitations':['Original neck pixels preserved; V-style weighting; appearance requires review; long hidden hair not reconstructed','Input closed-mouth misclassification remains an unverified baseline issue','Source silhouette colour fringe retained; local hidden ornament backing reconstructed']},ensure_ascii=False,indent=2))
print('built',len(parts),'mesh layers; source SHA',hashlib.sha256((ROOT/'character_materials/mukachi_kachi/base.png').read_bytes()).hexdigest())

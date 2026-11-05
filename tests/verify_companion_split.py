from pathlib import Path
import sys,numpy as np,cv2,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from character_head import split_head,companion_mask
im=cv2.imread(str(R/'character_materials/mukachi_kachi/base.png'),-1);parts=dict(split_head(im));mask=companion_mask(im.shape)
checks=[]
def check(name,ok):
 assert ok,name
 checks.append(name);print('PASS',name)
for x,y in [(490,342),(500,341),(508,346),(514,353),(505,365),(500,390),(450,440)]:
 check('companion owns ear/fur '+str((x,y)),parts['head'][y,x,3]==0 and parts['companion'][y,x,3]==im[y,x,3])
for x,y in [(490,330),(515,330),(539,340),(545,350),(580,340),(620,380)]:
 check('head owns hair/face '+str((x,y)),parts['head'][y,x,3]==im[y,x,3] and parts['companion'][y,x,3]==0)
check('head and companion alpha do not overlap',not np.any((parts['head'][:,:,3]>0)&(parts['companion'][:,:,3]>0)))
for x,y in [(490,342),(500,341),(508,346),(514,353)]:
 # At either maximum tilt, the shoulder companion remains stationary; its ears are not on the head mesh.
 for z in [-5,5]:
  a=np.radians(z);rot=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
  headPos=np.array([680,485])+rot@(np.array([x,y])-np.array([680,485]))
  check('ear stays on shoulder at '+str((x,y,z)),parts['head'][y,x,3]==0 and np.linalg.norm(headPos-[x,y])>5)
D=R/'docs/verification/repair_0.4.0';D.mkdir(exist_ok=True)
(D/'split_checks.json').write_text(json.dumps(checks,indent=2))
# Colour-coded ownership for visual inspection: cyan=head, amber=companion, original elsewhere.
out=im.copy();head=parts['head'][:,:,3]>0;bear=parts['companion'][:,:,3]>0
out[head,:3]=(out[head,:3]*.45+np.array([255,210,0])*.55).astype(np.uint8)
out[bear,:3]=(out[bear,:3]*.45+np.array([0,170,255])*.55).astype(np.uint8)
cv2.imwrite(str(D/'head_companion_ownership.png'),out[315:445,465:600])

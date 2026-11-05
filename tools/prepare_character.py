"""Preserve originals and register expression references by hair/ear features, not mouth/eyes."""
from pathlib import Path
import json,hashlib,shutil
import cv2,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
M=ROOT/'character_materials/mukachi_kachi'; P=ROOT/'projects/mukachi_kachi';D=ROOT/'docs/verification'
roles=['base','eyes_closed','mouth_a','mouth_i','mouth_e','smile','surprise']
source=Path('/workspace/live2d-preparation/originals')
if source.exists():
 for role,f in zip(roles,sorted(source.glob('*.png'))):
  if not (M/(role+'.png')).exists():shutil.copy2(f,M/(role+'.png'))
base=cv2.imread(str(M/'base.png'),-1);h,w=base.shape[:2]; S=cv2.SIFT_create(nfeatures=5000)
# Keep invariant hair, ears, and neck ornament; exclude expression features and torso.
mask=np.zeros((h,w),np.uint8);mask[25:265,430:900]=255;mask[330:440,770:835]=255
kb,db=S.detectAndCompute(cv2.cvtColor(base,cv2.COLOR_BGRA2GRAY),mask)
manifest={};(P/'aligned').mkdir(parents=True,exist_ok=True)
for role in roles:
 f=M/(role+'.png');im=cv2.imread(str(f),-1)
 if role=='base':A=np.array([[1.,0,0],[0,1.,0]]);inliers=0;error=0
 else:
  gray=cv2.cvtColor(im,cv2.COLOR_BGRA2GRAY);ki,di=S.detectAndCompute(gray,None)
  pairs=cv2.BFMatcher().knnMatch(db,di,k=2); good=[a for a,b in pairs if a.distance<.7*b.distance]
  src=np.float32([ki[a.trainIdx].pt for a in good]);dst=np.float32([kb[a.queryIdx].pt for a in good])
  A,inside=cv2.estimateAffinePartial2D(src,dst,method=cv2.RANSAC,ransacReprojThreshold=2,maxIters=10000)
  if A is None or inside.sum()<15:raise ValueError('Not enough matching landmarks: '+role)
  inliers=int(inside.sum());error=float(np.median(np.linalg.norm((src@A[:,:2].T+A[:,2]-dst)[inside.ravel()>0],axis=1)))
 aligned=cv2.warpAffine(im,A,(w,h),flags=cv2.INTER_LANCZOS4) if role!='base' else im
 cv2.imwrite(str(P/'aligned'/f'{role}.png'),aligned)
 manifest[role]={'original':str(f.relative_to(ROOT)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'size':[im.shape[1],im.shape[0]],'mode':'RGBA','alpha_range':[int(im[:,:,3].min()),int(im[:,:,3].max())],'transform_to_base':A.tolist(),'inliers':inliers,'median_landmark_error_px':error}
 print(role,'inliers',inliers,'error',round(error,3),'affine',A.tolist())
(P/'materials.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
sheet=Image.new('RGB',(420*4,360*2),(55,55,65));draw=ImageDraw.Draw(sheet)
for i,role in enumerate(roles):
 im=Image.open(P/'aligned'/f'{role}.png');crop=im.crop((465,245,815,440));crop.thumbnail((410,310));x=i%4*420;y=i//4*360
 sheet.paste(crop,(x,y),crop);draw.text((x+5,y+320),role,fill='white')
sheet.save(D/'aligned_faces.jpg')

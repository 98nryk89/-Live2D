"""Register supplied blink drawings and clean backing; preserve source files and panel pixels."""
from pathlib import Path
import json,hashlib,cv2,numpy as np
R=Path(__file__).resolve().parents[1];M=R/'character_materials/mukachi_kachi/revision4_originals';P=R/'projects/mukachi_kachi';D=R/'docs/verification/repair_0.4.0';D.mkdir(exist_ok=True)
(P/'aligned').mkdir(parents=True,exist_ok=True)
base=cv2.imread(str(R/'character_materials/mukachi_kachi/base.png'),-1);H,W=base.shape[:2]
sift=cv2.SIFT_create(nfeatures=5000);mask=np.zeros((H,W),np.uint8);mask[35:260,540:810]=255
kb,db=sift.detectAndCompute(cv2.cvtColor(base,cv2.COLOR_BGRA2GRAY),mask)
manifest={};raw={}
for file in sorted(M.glob('*')):
 im=cv2.imread(str(file),-1)
 if im is None:continue
 if im.shape[1]==im.shape[0]*3:
  step=im.shape[0]
  for i,name in enumerate(['blink_open','blink_half','blink_closed']):raw[name]=(im[:,i*step:(i+1)*step].copy(),file,[i*step,0,(i+1)*step,step])
 else:raw['clean_backing']=(im,file,None)
assert set(raw)=={'blink_open','blink_half','blink_closed','clean_backing'}
for name,(im,file,crop) in raw.items():
 ki,di=sift.detectAndCompute(cv2.cvtColor(im,cv2.COLOR_BGRA2GRAY),None)
 matches=cv2.BFMatcher().knnMatch(db,di,k=2);good=[a for a,b in matches if a.distance<.72*b.distance]
 src=np.float32([ki[m.trainIdx].pt for m in good]);dst=np.float32([kb[m.queryIdx].pt for m in good])
 A,inliers=cv2.estimateAffinePartial2D(src,dst,method=cv2.RANSAC,ransacReprojThreshold=2,maxIters=10000)
 assert A is not None and inliers.sum()>=15,name
 aligned=cv2.warpAffine(im,A,(W,H),flags=cv2.INTER_LANCZOS4)
 cv2.imwrite(str(P/'aligned'/f'{name}.png'),aligned)
 error=float(np.median(np.linalg.norm((src@A[:,:2].T+A[:,2]-dst)[inliers.ravel()>0],axis=1)))
 manifest[name]={'source':str(file.relative_to(R)),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'panel_crop':crop,'transform_to_base':A.tolist(),'inliers':int(inliers.sum()),'median_error_px':error}
 print(name,int(inliers.sum()),round(error,3),A.tolist())
(P/'revision4_materials.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
from PIL import Image,ImageDraw
sheet=Image.new('RGB',(600*3,360),(60,60,70));draw=ImageDraw.Draw(sheet)
for i,name in enumerate(['blink_open','blink_half','blink_closed']):
 im=Image.open(P/'aligned'/f'{name}.png').crop((550,255,810,395)).resize((600,323));sheet.paste(im,(i*600,0),im);draw.text((i*600+5,330),name,fill='white')
sheet.save(D/'supplied_eyes_aligned.jpg')

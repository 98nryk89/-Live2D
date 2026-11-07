"""Read-only source assessment: torso registration and measured head roll. No rig edits."""
from pathlib import Path
import json,hashlib,cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];M=R/'character_materials/mukachi_kachi/neck_pose_originals';D=R/'docs/verification/neck_pose_assessment';D.mkdir(exist_ok=True)
base=cv2.imread(str(R/'character_materials/mukachi_kachi/base.png'),-1);H,W=base.shape[:2];sift=cv2.SIFT_create(nfeatures=7000)
def features(im,box):
 mask=np.zeros(im.shape[:2],np.uint8);x0,y0,x1,y1=box;mask[y0:y1,x0:x1]=255;mask[im[:,:,3]<80]=0
 return sift.detectAndCompute(cv2.cvtColor(im,cv2.COLOR_BGRA2GRAY),mask)
def transform(source,target,sourcebox,targetbox):
 ks,ds=features(source,sourcebox);kt,dt=features(target,targetbox)
 pairs=cv2.BFMatcher().knnMatch(ds,dt,k=2);good=[a for a,b in pairs if a.distance<.68*b.distance]
 a=np.float32([ks[m.queryIdx].pt for m in good]);b=np.float32([kt[m.trainIdx].pt for m in good])
 A,inside=cv2.estimateAffinePartial2D(a,b,method=cv2.RANSAC,ransacReprojThreshold=1.5,maxIters=15000,confidence=.999)
 assert A is not None and inside.sum()>=20
 selected=inside.ravel()>0;error=np.linalg.norm(a@A[:,:2].T+A[:,2]-b,axis=1)[selected]
 return A,{'matched':len(good),'inliers':int(inside.sum()),'median_error_px':float(np.median(error)),'scale':float(np.hypot(A[0,0],A[1,0])),'clockwise_degrees':float(np.degrees(np.arctan2(A[1,0],A[0,0])))}
results=[];previews=[]
for p in sorted(M.glob('*.png')):
 im=cv2.imread(str(p),-1);assert im.shape==base.shape
 A,bodyfit=transform(im,base,(180,550,1170,1120),(180,550,1170,1120))
 aligned=cv2.warpAffine(im,A,(W,H),flags=cv2.INTER_LANCZOS4)
 B,headfit=transform(base,aligned,(480,35,850,245),(410,0,980,410))
 headfit['relative_to_current_upright_degrees']=headfit['clockwise_degrees']-6.530486248611499
 role='neutral_requested' if '修正' in p.name else 'screen_left' if headfit['relative_to_current_upright_degrees']<0 else 'screen_right'
 a=aligned[:,:,3];fg=(a>100)&(base[:,:,3]>100);fg[:550]=False
 rgbdiff=np.abs(aligned[:,:,:3].astype(float)-base[:,:,:3].astype(float));bodyerr=float(rgbdiff[fg].mean())
 record={'file':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'role':role,'size':[W,H],'mode':'RGBA','body_to_original':A.tolist(),'body_fit':bodyfit,'head_original_to_registered':B.tolist(),'head_fit':headfit,'registered_torso_mean_rgb_difference':bodyerr,'alpha_zero_pixels':int((im[:,:,3]==0).sum()),'alpha_low_1_to_15_pixels':int(((im[:,:,3]>0)&(im[:,:,3]<16)).sum())}
 results.append(record);previews.append((role,aligned,record));cv2.imwrite(str(D/(role+'_torso_registered.png')),aligned)
 print(role,p.name,'body rotation',round(bodyfit['clockwise_degrees'],3),'scale',round(bodyfit['scale'],5),'head vs upright',round(headfit['relative_to_current_upright_degrees'],2),'head inliers',headfit['inliers'],'bodyRGB',round(bodyerr,3),flush=True)
fontpath='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';font=ImageFont.truetype(fontpath,24);small=ImageFont.truetype(fontpath,19)
order={'screen_left':0,'neutral_requested':1,'screen_right':2};sheet=Image.new('RGB',(1800,1080),(34,36,43));draw=ImageDraw.Draw(sheet)
labels={'screen_left':'画面左へのかしげ','screen_right':'画面右へのかしげ','neutral_requested':'正面用に生成された画像'}
for i,(role,im,r) in enumerate(sorted(previews,key=lambda r:order[r[0]])):
 rgba=Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGRA2RGBA));bg=Image.new('RGBA',rgba.size,(55,57,65,255));bg.alpha_composite(rgba)
 sheet.paste(bg.crop((380,0,980,590)).convert('RGB'),(i*600,85));sheet.paste(bg.crop((570,380,810,520)).resize((600,350)).convert('RGB'),(i*600,690))
 draw.text((i*600+12,10),labels[role],font=font,fill='white');draw.text((i*600+12,45),f"既存の正面基準との差：約{r['head_fit']['relative_to_current_upright_degrees']:+.1f}度",font=small,fill='white');draw.text((i*600+12,655),'首・顎・襟の拡大（胴体を位置合わせ）',font=small,fill='white')
sheet.save(D/'neck_pose_comparison.jpg')
(R/'projects/mukachi_kachi/neck_pose_assessment.json').write_text(json.dumps({'method':'SIFT/RANSAC similarity transform; torso registration, then hair correspondence; positive roll is screen-clockwise. Head angle is image correspondence, not anatomical ground truth. No rig modified.','upright_correction_clockwise_degrees':6.530486248611499,'sources':results},ensure_ascii=False,indent=2))

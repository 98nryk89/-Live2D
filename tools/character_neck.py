"""Supplied throat texture, independent jaw shadow and fixed collar occlusion."""
from pathlib import Path
import json,hashlib,cv2,numpy as np
from character_head import split_head
R=Path(__file__).resolve().parents[1]
JAW_POINTS=np.array([[610,387],[620,399],[630,406],[640,413],[650,419],[660,424],[670,429],[680,433],[689,436],[696,435],[705,430],[715,423],[725,414],[735,405],[745,395],[752,384],[760,372]],np.float32)
LIP_POINTS=np.array([[625,450],[636,457],[650,465],[665,473],[677,479],[681,485],[684,493],[693,493],[697,481],[708,475],[722,468],[736,460],[752,450],[755,448]],np.float32)

def jaw_boundary(original):
 gray=cv2.cvtColor(original,cv2.COLOR_BGRA2GRAY);xs=np.arange(original.shape[1]);guess=np.interp(xs,JAW_POINTS[:,0],JAW_POINTS[:,1]);curve=guess.copy()
 for x in range(610,761):
  y=int(round(guess[x]));strip=gray[y-3:y+4,x].astype(float)
  curve[x]=y-3+int(np.argmin(strip))+1.8
 return cv2.GaussianBlur(curve.astype(np.float32)[None,:],(5,1),.6)[0]

def prepare_skin(images,outdir):
 files=sorted((R/'character_materials/mukachi_kachi/neck_skin_originals').glob('*.png'));assert len(files)==1
 path=files[0];im=cv2.imread(str(path),-1);H,W=im.shape[:2];assert im.shape==images['base'].shape
 n,labels,stats,_=cv2.connectedComponentsWithStats((im[:,:,3]>16).astype(np.uint8),8);label=1+np.argmax(stats[1:,cv2.CC_STAT_AREA]);keep=cv2.dilate((labels==label).astype(np.uint8),np.ones((3,3),np.uint8));im[:,:,3]=np.where(keep,im[:,:,3],0)
 # Move the supplied skin upward: its scoop must overlap behind the jaw rather than end at it.
 skin=cv2.warpAffine(im,np.array([[1,0,0],[0,1,-20]],np.float32),(W,H),flags=cv2.INTER_LINEAR)
 manifest=json.loads((R/'projects/mukachi_kachi/neck_pose_assessment.json').read_text());ref=next(s for s in manifest['sources'] if s['role']=='neutral_requested');raw=cv2.imread(str(R/ref['file']),-1)
 raw=cv2.warpAffine(raw,np.array(ref['body_to_original'],np.float32),(W,H),flags=cv2.INTER_LANCZOS4)
 refHead=cv2.warpAffine(raw,cv2.invertAffineTransform(np.array(ref['head_original_to_registered'],np.float32)),(W,H),flags=cv2.INTER_LANCZOS4)
 region=np.zeros((H,W),bool);region[442:472,646:734]=True
 color=raw[:,:,:3].astype(float)
 valid=region&(skin[:,:,3]>220)&(raw[:,:,3]>220)&(color[:,:,2]>color[:,:,1]+10)&(color[:,:,1]>color[:,:,0]+3)
 assert valid.sum()>200
 offset=np.clip(np.median(raw[valid,:3].astype(float),axis=0)-np.median(skin[valid,:3].astype(float),axis=0),-32,32)
 skin[:,:,:3]=np.clip(skin[:,:,:3].astype(float)+offset,0,255).astype(np.uint8)
 cv2.imwrite(str(Path(outdir)/'neck_skin_registered.png'),skin)
 record={'source':str(path.relative_to(R)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_size':[W,H],'translation':[0,-20],'alpha_cleanup':'largest neck component at alpha>16, with one-pixel boundary margin; original unchanged','bgr_color_offset':offset.tolist(),'shadow_source':ref['file'],'shadow_alignment':'torso registration then inverse head registration','no_new_illustration_generated':True}
 (R/'projects/mukachi_kachi/neck_materials.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
 return skin,refHead

def split_with_neck(original,clean,segmentation,skin,shadow_reference):
 parts=dict(split_head(original,clean,segmentation));H,W=original.shape[:2];yy,xx=np.mgrid[:H,:W];jaw=jaw_boundary(original);lip=np.interp(np.arange(W),LIP_POINTS[:,0],LIP_POINTS[:,1]);opening=(xx>=627)&(xx<=754)&(yy>jaw[None,:])&(yy<lip[None,:]-1)
 # The head ends at its actual jaw, not a horizontal crop or a band of stretched skin.
 head=original.copy();alpha=parts['head'][:,:,3].copy();alpha[opening|(yy>448)]=0;head[:,:,3]=alpha
 bear=segmentation['companion'];ears=np.maximum(segmentation['head_ear_left'],segmentation['head_ear_right'])
 collar=parts['collar'].copy();ca=cv2.erode(collar[:,:,3],np.ones((5,5),np.uint8));ca[opening]=0
 backmask=((yy<435)|((xx<630)&(yy<452))|((xx>748)&(yy<452)))&(ca>0)
 back=collar.copy();back[:,:,3]=np.where(backmask,ca,0);collar[:,:,3]=np.where(backmask,0,ca)
 body=original.copy();body[:,:,3]=np.where((yy<435)|(alpha>0)|opening|(bear>0)|(ears>0)|backmask,0,body[:,:,3])
 # Source-colour jaw shadow follows the head, and is clipped to the new moving skin.
 distance=yy-jaw[None,:];a=np.clip(1-distance/19,0,1)**2*np.clip((xx-627)/9,0,1)*np.clip((754-xx)/9,0,1)
 a[(distance<0)|(distance>19)]=0
 shadow=shadow_reference.copy();shadow[:,:,3]=np.rint(a*.60*255).astype(np.uint8)
 result=[('neck_skin',skin),('jaw_shadow',shadow),('collar_back',back),('body',body),('collar',collar)]
 for name in ['hair_behind_companion','hair_behind_head_ears','companion']:result.append((name,parts[name]))
 result.append(('head',head))
 for name in ['head_ear_left','head_ear_right']:result.append((name,parts[name]))
 cv2.imwrite(str(R/'projects/mukachi_kachi/neck_opening_mask.png'),opening.astype(np.uint8)*255)
 return result

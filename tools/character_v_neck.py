"""Original painted neck using the finished V rig's split, linear weighting and depth model."""
from pathlib import Path
import json,hashlib,cv2,numpy as np
from scipy.ndimage import distance_transform_edt
from character_head import split_head
R=Path(__file__).resolve().parents[1]
JAW=np.array([[610,387],[620,399],[630,406],[640,413],[650,419],[660,424],[670,429],[680,433],[689,436],[696,435],[705,430],[715,423],[725,414],[735,405],[745,395],[752,384],[760,372]],float)
LIP=np.array([[625,450],[636,457],[650,465],[665,473],[677,479],[681,485],[684,493],[693,493],[697,481],[708,475],[722,468],[736,460],[752,450],[755,448]],float)

def split_original_neck(original,clean,segmentation):
 legacy=dict(split_head(original,clean,segmentation));H,W=original.shape[:2];yy,xx=np.mgrid[:H,:W];xs=np.arange(W)
 jaw=np.interp(xs,JAW[:,0],JAW[:,1]);gray=cv2.cvtColor(original,cv2.COLOR_BGRA2GRAY)
 for x in range(610,761):
  y=int(round(jaw[x]));jaw[x]=y-3+int(np.argmin(gray[y-3:y+4,x]))+1.8
 jaw=cv2.GaussianBlur(jaw.astype(np.float32)[None,:],(5,1),.6)[0]
 lip=np.interp(xs,LIP[:,0],LIP[:,1]);left=np.interp(yy,[380,405,420,435,450,455],[627,627,629,631,631,634]);right=np.interp(yy,[370,395,405,415,425,450,455],[752,751,749,748,748,748,749])
 sides=(xx>=left-1)&(xx<=right+1)
 visible=sides&(yy>jaw[None,:])&(yy<lip[None,:]-1)
 domain=sides&(yy>=jaw[None,:]-20)&(yy<=lip[None,:]+7)
 # Exactly the completed V technique: erase the duplicate jaw only in the occluded backing.
 lab=cv2.cvtColor(original[:,:,:3],cv2.COLOR_BGR2LAB)
 seeds=sides&(yy>jaw[None,:]+7)&(yy<jaw[None,:]+24)&(yy<lip[None,:]-6)&(xx>635)&(xx<745)
 seeds&=(lab[:,:,0]>120)&(lab[:,:,1]>=132)&(lab[:,:,2]>=129)
 assert seeds.sum()>100
 _,indices=distance_transform_edt(~seeds,return_indices=True);sample=original[indices[0],indices[1],:3]
 neck=original.copy();duplicate=domain&(yy>=jaw[None,:]-5)&(yy<=jaw[None,:]+2.5)
 collar_overlap=domain&(yy>=lip[None,:]-1)
 neck[duplicate|collar_overlap,:3]=sample[duplicate|collar_overlap]
 neck[:,:,3]=np.where(domain,original[:,:,3],0)
 # Keep the painted sides, cast shadow and volume shading. Do not smooth/replace visible skin.
 head=original.copy();ha=legacy['head'][:,:,3].copy();ha[visible|(yy>448)]=0;head[:,:,3]=ha
 bear=segmentation['companion'];ears=np.maximum(segmentation['head_ear_left'],segmentation['head_ear_right'])
 body=original.copy();body[:,:,3]=np.where((yy<435)|(ha>0)|visible|(bear>0)|(ears>0),0,body[:,:,3])
 collar=legacy['collar'].copy();ca=cv2.erode(collar[:,:,3],np.ones((5,5),np.uint8));ca[visible]=0
 collar[:,:,3]=ca
 # Source collar is foreground; the original outline remains in front of the neck overlap.
 # V also supplies hidden costume backing: extend only the original collar lining behind gaps.
 backing=np.zeros_like(original)
 for box,poly in [((616,438,629,450),[[617,428],[628,422],[638,430],[641,451],[628,458],[617,448]]),((750,438,760,450),[[743,427],[754,422],[764,430],[764,449],[750,458],[741,450]])]:
  x0,y0,x1,y1=box;seed=np.zeros((H,W),bool);seed[y0:y1,x0:x1]=True
  b,g,r=[original[:,:,i].astype(float) for i in range(3)]
  seed&=(np.abs(b-g)<12)&(r-g<65)&(r-g>12)&(g>90)&(g<210)&(original[:,:,3]>200)
  assert seed.sum()>10
  _,idx=distance_transform_edt(~seed,return_indices=True);fill=original[idx[0],idx[1],:3];mask=np.zeros((H,W),np.uint8);cv2.fillPoly(mask,[np.array(poly,np.int32)],255)
  backing[mask>0,:3]=fill[mask>0];backing[:,:,3]=np.maximum(backing[:,:,3],mask)
 output=[('collar_backing',backing),('neck',neck),('body',body),('collar',collar)]
 for n in ['hair_behind_companion','hair_behind_head_ears','companion']:output.append((n,legacy[n]))
 output.append(('head',head))
 for n in ['head_ear_left','head_ear_right']:output.append((n,legacy[n]))
 P=R/'projects/mukachi_kachi';cv2.imwrite(str(P/'v_neck_visible_mask.png'),visible.astype(np.uint8)*255);cv2.imwrite(str(P/'v_neck_occluded_repair_mask.png'),(duplicate|collar_overlap).astype(np.uint8)*255)
 # Expose exact-pixel preservation in the source-visible throat, away from the hidden jaw seam.
 preserved=visible&~duplicate&~collar_overlap
 assert np.array_equal(neck[preserved,:3],original[preserved,:3])
 (P/'v_neck_materials.json').write_text(json.dumps({'source':'character_materials/mukachi_kachi/base.png','source_sha256':hashlib.sha256((R/'character_materials/mukachi_kachi/base.png').read_bytes()).hexdigest(),'source_neck_pixels_preserved':int(preserved.sum()),'neck_texture':'original RGB, including contour and shading','underjaw_backing':'same-image neck skin copied only into the occluded duplicate jaw stroke','collar_overlap':'same-image skin beneath foreground collar; collar stroke retained in foreground','collar_backing':'original lining sampled into small hidden side regions behind the neck','generated_neck_layers_used':[],'reference':'98nryk89/V @91f240f75a437830697126397fce60a8202b6b16 tools/refine_face.py and neck rig'},ensure_ascii=False,indent=2))
 return output

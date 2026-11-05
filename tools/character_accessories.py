"""Source masks and local backing for dangling ornaments. Fixed attachments stay in the base."""
import cv2,numpy as np
from pathlib import Path

TASSELS=[
 ('tassel_left_upper',(390,716,439,803),(415,716)),
 ('tassel_left_middle',(438,804,493,904),(466,804)),
 ('tassel_right_upper',(885,677,935,755),(908,677)),
 ('tassel_right_middle',(943,739,992,833),(967,739)),
 ('tassel_right_lower',(957,841,1014,952),(984,841)),
 ('tassel_left_lower',(288,1011,354,1132),(322,1011)),
 ('tassel_center_lower',(867,985,919,1096),(891,985))]
EARRINGS=[
 ('earring_red',[(580,371),(586,378),(594,391),(587,406),(577,421),(568,408),(562,391),(574,378)],(580,371)),
 ('earring_name',[(795,362),(804,372),(810,375),(813,449),(795,463),(781,448),(781,376),(790,370)],(795,362))]

def split_accessories(original,outdir):
 base=original.copy();H,W=base.shape[:2];accessories=[];masks=[]
 for name,polygon,pivot in EARRINGS:
  mask=np.zeros((H,W),np.uint8);cv2.fillPoly(mask,[np.array(polygon,np.int32)],255)
  masks.append((name,mask,pivot,True))
 for name,box,pivot in TASSELS:
  x0,y0,x1,y1=box;roi=original[y0:y1,x0:x1];col=roi[:,:,:3]
  # White/pink threads only; restrict to explicit boxes to keep shirt and costume out.
  white=((col.min(axis=2)>145)&((col.max(axis=2)-col.min(axis=2))<92)).astype(np.uint8)*255
  count,labels,stats,_=cv2.connectedComponentsWithStats(white,8)
  if count<2:raise ValueError(name)
  i=1+np.argmax(stats[1:,cv2.CC_STAT_AREA]);m=(labels==i).astype(np.uint8)*255
  contours,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
  cv2.drawContours(m,contours,-1,255,cv2.FILLED);m=cv2.dilate(m,np.ones((3,3),np.uint8))
  mask=np.zeros((H,W),np.uint8);mask[y0:y1,x0:x1]=m
  # The small cap underneath its fixed attachment moves with the threads.
  px,py=pivot;cap=np.array([[px,py],[px+7,py+8],[px+7,py+21],[px-7,py+21],[px-7,py+8]])
  cv2.fillPoly(mask,[cap.astype(np.int32)],255)
  masks.append((name,mask,pivot,False))
 union=np.zeros((H,W),np.uint8)
 for name,mask,pivot,is_head in masks:
  union=np.maximum(union,mask)
  x,y,w,h=cv2.boundingRect(mask);sprite=original[y:y+h,x:x+w].copy();sprite[:,:,3]=np.where(mask[y:y+h,x:x+w]>0,sprite[:,:,3],0)
  accessories.append((name,sprite,x,y,pivot,is_head))
  cv2.imwrite(str(Path(outdir)/(name+'_mask.png')),mask)
 # Reconstruct only the newly uncovered pixels underneath each selected ornament.
 # Work in premultiplied RGBA so transparent surroundings don't introduce black/colour fringes.
 alpha=original[:,:,3].astype(np.float32)/255
 pm=np.rint(original[:,:,:3]*alpha[:,:,None]).astype(np.uint8)
 filled=cv2.inpaint(pm,union,5,cv2.INPAINT_TELEA)
 newalpha=cv2.inpaint(original[:,:,3],union,5,cv2.INPAINT_TELEA)
 col=np.clip(filled.astype(np.float32)/np.maximum(newalpha[:,:,None]/255,.01),0,255).astype(np.uint8)
 base[union>0,:3]=col[union>0];base[union>0,3]=newalpha[union>0]
 cv2.imwrite(str(Path(outdir)/'accessory_backing.png'),base)
 return base,accessories

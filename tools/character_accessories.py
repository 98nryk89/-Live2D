"""Source masks and local backing for dangling ornaments. Fixed attachments stay in the base."""
import cv2,numpy as np
from pathlib import Path
from character_segmentation import refine_contour

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

def split_accessories(original,outdir,clean=None):
 base=original.copy();H,W=base.shape[:2];accessories=[];masks=[]
 for name,polygon,pivot in EARRINGS:
  if name=='earring_red':
   # Trace the complete gold-edged ruby, including its dark lower facet and tip.
   # Colour-only segmentation left the bottom gold outline attached to the hair.
   contour=[[583,382],[586,389],[590,394],[596,400],[596,404],[591,414],[586,424],[582,430],[578,424],[573,414],[568,404],[567,400],[573,394],[579,386]]
   mask=np.zeros((H,W),np.uint8);cv2.fillPoly(mask,[np.array(contour,np.int32)],255)
  else:mask=refine_contour(original,polygon)
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
  contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
  hull=cv2.convexHull(np.concatenate(contours));mask=refine_contour(original,hull[:,0,:].tolist())
  masks.append((name,mask,pivot,False))
 union=np.zeros((H,W),np.uint8)
 for name,mask,pivot,is_head in masks:
  union=np.maximum(union,mask)
  x,y,w,h=cv2.boundingRect(mask);sprite=original[y:y+h,x:x+w].copy();sprite[:,:,3]=np.where(mask[y:y+h,x:x+w]>0,sprite[:,:,3],0)
  # Pivot on the actual attachment pixels, not above an absent stem.
  first=np.flatnonzero(np.any(mask>0,axis=1))[0];cols=np.flatnonzero(mask[first]>0)
  anchor=(float(np.median(cols)),int(first))
  accessories.append((name,sprite,x,y,anchor,is_head))
  cv2.imwrite(str(Path(outdir)/(name+'_mask.png')),mask)
 # Use the supplied actual background drawing beneath moving ornaments.
 if clean is None:raise ValueError('Clean backing required for accessory cutouts')
 base[union>0]=clean[union>0]
 cv2.imwrite(str(Path(outdir)/'accessory_backing.png'),base)
 return base,accessories

"""Use approved open/half/closed drawings verbatim; no eye/skin warp or generated in-betweens."""
import cv2,numpy as np

EYE_BOXES={'left':(561,272,671,341),'right':(690,253,799,326)}
POLYGONS={
 'left':[[569,313],[580,302],[598,286],[620,281],[641,286],[656,298],[664,306],[660,324],[642,334],[613,339],[586,334],[575,326]],
 'right':[[696,288],[708,275],[726,263],[746,262],[767,268],[783,279],[792,288],[786,303],[766,313],[740,317],[719,315],[705,304]]}
ROLES=['blink_closed','blink_half','blink_open']

def authored_eye_sprites(images,eye):
 box=EYE_BOXES[eye];x0,y0,x1,y1=box
 mask=np.zeros((y1-y0,x1-x0),np.uint8)
 p=np.array(POLYGONS[eye],np.int32)-[x0,y0];cv2.fillPoly(mask,[p.astype(np.int32)],255)
 # Subpixel seam only; every interior pixel is an unmodified registered source pixel.
 mask=cv2.GaussianBlur(mask,(3,3),.5)
 if eye=='right':
  yy,xx=np.mgrid[y0:y1,x0:x1];mask[(xx>=743)&(yy>=312)]=0
 sprites=[]
 for role in ROLES:
  if role not in images:raise ValueError('Missing approved blink drawing: '+role)
  sprite=images[role][y0:y1,x0:x1].copy()
  sprite[:,:,3]=np.rint(sprite[:,:,3]*(mask/255)).astype(np.uint8)
  sprites.append(sprite)
 return sprites,box,mask

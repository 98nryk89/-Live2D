"""Pixel-level cutouts: bounded contour refinement of authored part outlines."""
import cv2,numpy as np

COMPANION_OUTLINE=[[476,346],[485,340],[500,338],[512,342],[520,350],[524,362],[519,376],
 [536,385],[548,391],[555,404],[559,420],[562,433],[559,448],[570,461],[579,478],
 [579,496],[570,511],[555,520],[546,536],[527,547],[507,552],[484,553],[460,551],
 [437,554],[412,545],[396,540],[383,531],[375,520],[359,515],[351,507],[350,495],
 [355,485],[359,493],[366,499],[374,503],[381,484],[383,466],[385,449],[381,435],
 [377,421],[380,405],[387,400],[383,389],[386,377],[397,370],[409,372],[419,378],
 [434,372],[447,368],[460,369],[473,373]]
HEAD_EARS={
 'head_ear_left':[[482,145],[482,132],[486,119],[495,110],[507,105],[521,101],[535,102],[547,106],[560,114],[568,124],[571,134],[564,146],[557,158],[549,170],[539,181],[529,190],[513,186],[502,178],[491,164],[485,154]],
 'head_ear_right':[[764,123],[772,111],[784,102],[797,96],[812,96],[826,99],[839,108],[847,120],[851,135],[848,150],[840,162],[827,172],[815,181],[798,182],[785,172],[776,158],[769,141]]}

def refine_contour(original,polygon,extra_foreground=None):
 H,W=original.shape[:2];m=np.zeros((H,W),np.uint8);cv2.fillPoly(m,[np.array(polygon,np.int32)],255)
 x,y,w,h=cv2.boundingRect(m);x0=max(0,x-12);y0=max(0,y-12);x1=min(W,x+w+12);y1=min(H,y+h+12)
 roi=original[y0:y1,x0:x1];p=m[y0:y1,x0:x1]
 sure=cv2.erode(p,np.ones((13,13),np.uint8));loose=cv2.dilate(p,np.ones((11,11),np.uint8))
 labels=np.where(loose>0,cv2.GC_PR_BGD,cv2.GC_BGD).astype(np.uint8)
 labels[p>0]=cv2.GC_PR_FGD;labels[sure>0]=cv2.GC_FGD;labels[roi[:,:,3]<16]=cv2.GC_BGD
 if extra_foreground is not None:
  seed=extra_foreground[y0:y1,x0:x1]&(roi[:,:,3]>80);labels[seed]=cv2.GC_FGD
 cv2.setRNGSeed(5082)
 cv2.grabCut(roi[:,:,:3].copy(),labels,None,np.zeros((1,65),np.float64),np.zeros((1,65),np.float64),8,cv2.GC_INIT_WITH_MASK)
 result=np.zeros((H,W),np.uint8);result[y0:y1,x0:x1]=np.where((labels==cv2.GC_FGD)|(labels==cv2.GC_PR_FGD),255,0)
 return result

def segmentation_masks(original):
 masks={name:refine_contour(original,polygon) for name,polygon in {'companion':COMPANION_OUTLINE,**HEAD_EARS}.items()}
 # GrabCut classifies the dark outer ear line as adjoining hair. Preserve the
 # authored contour in this small, traced ear region; never repaint source RGB.
 ear=np.array([[474,372],[474,367],[476,360],[479,354],[484,349],
  [489,346],[494,345],[497,344],[501,345],[505,345],[510,347],
  [514,349],[519,353],[522,356],[522,362],[524,366],[524,373],
  [522,378],[519,383],[510,378],[490,374]],np.int32)
 cv2.fillPoly(masks['companion'],[ear],255)
 return masks

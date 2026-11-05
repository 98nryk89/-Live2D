"""V's completed rig separates head, neck, and body: no shoulder exclusion on the face."""
import cv2,numpy as np

def split_head(original):
 h,w=original.shape[:2];yy,xx=np.mgrid[:h,:w]
 # The companion stays on the shoulder. Its boundary is outside the face, not a feathered ellipse across the cheek.
 boundary=np.interp(yy[:,0],[0,329,345,365,390,415,435],[0,0,531,546,555,563,568])[:,None]
 head=((yy<435)&(xx>=boundary)).astype(np.uint8)*255
 for poly in [
  [[560,425],[613,420],[611,436],[595,440],[578,447],[569,444]],
  [[750,420],[815,420],[796,444],[775,448],[753,436]]]:
  cv2.fillPoly(head,[np.array(poly,np.int32)],255)
 neck=np.zeros((h,w),np.uint8)
 cv2.fillPoly(neck,[np.array([[619,435],[750,435],[751,446],[699,476],[691,490],[679,491],[671,475],[621,451]],np.int32)],255)
 neck[head>0]=0
 body=original.copy();body[:,:,3]=np.where((head>0)|(neck>0),0,body[:,:,3])
 face=original.copy();face[:,:,3]=np.where(head>0,face[:,:,3],0)
 neckSprite=original.copy();neckSprite[:,:,3]=np.where(neck>0,neckSprite[:,:,3],0)
 # Under-jaw backing, hidden at neutral. Sample intact neck skin rather than copying a jaw outline.
 backing=np.zeros_like(original);cover=np.zeros((h,w),np.uint8)
 poly=np.array([[633,410],[726,410],[752,442],[699,476],[691,490],[679,491],[671,475],[621,451],[619,434]],np.int32)
 cv2.fillPoly(cover,[poly],255)
 samples=original[442:446,640:736,:3].mean(axis=0)
 for x in range(619,753):backing[:,x,:3]=samples[min(95,max(0,x-640))]
 backing[:,:,3]=cover
 return [('neck_backing',backing),('body',body),('neck',neckSprite),('head',face)]

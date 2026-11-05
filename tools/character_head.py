"""V's completed rig separates head, neck, and body: no shoulder exclusion on the face."""
import cv2,numpy as np

def companion_mask(shape):
 mask=np.zeros(shape[:2],np.uint8)
 outline=[[476,346],[485,340],[500,338],[512,342],[520,350],[524,362],[519,376],
 [536,385],[548,391],[555,404],[559,420],[562,433],[559,448],[570,461],[579,478],
 [579,496],[570,511],[555,520],[546,536],[527,547],[507,552],[484,553],[460,551],
 [437,554],[412,545],[396,540],[383,531],[375,520],[359,515],[349,508],[351,492],
 [357,493],[364,502],[374,503],[381,484],[383,466],[385,449],[381,435],[377,421],
 [380,405],[387,400],[383,389],[386,377],[397,370],[409,372],[419,378],[434,372],
 [447,368],[460,369],[473,373]]
 cv2.fillPoly(mask,[np.array(outline,np.int32)],255)
 return mask

def split_head(original,clean=None):
 h,w=original.shape[:2];yy,xx=np.mgrid[:h,:w]
 # The companion stays on the shoulder. Its boundary is outside the face, not a feathered ellipse across the cheek.
 boundary=np.interp(yy[:,0],[0,329,345,365,390,415,435],[0,0,531,546,555,563,568])[:,None]
 head=((yy<435)&(xx>=boundary)).astype(np.uint8)*255
 for poly in [
  [[560,425],[613,420],[611,436],[595,440],[578,447],[569,444]],
  [[750,420],[815,420],[796,444],[775,448],[753,436]]]:
  cv2.fillPoly(head,[np.array(poly,np.int32)],255)
 bear=companion_mask(original.shape)
 head[bear>0]=0
 neck=np.zeros((h,w),np.uint8)
 cv2.fillPoly(neck,[np.array([[619,435],[750,435],[751,446],[699,476],[691,490],[679,491],[671,475],[621,451]],np.int32)],255)
 neck[(head>0)|(bear>0)]=0
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
 companion=original.copy();companion[:,:,3]=np.where(bear>0,companion[:,:,3],0)
 parts=[('neck_backing',backing),('body',body)]
 if clean is not None:
  # The supplied clean illustration supplies genuine hair pixels hidden by the companion.
  # Do not copy the reference's changed shirt or replace visible original hair.
  region=np.zeros((h,w),np.uint8);region[312:435,465:620]=255
  hair=clean.copy();hair[:,:,3]=np.where((bear>0)&(region>0),hair[:,:,3],0)
  parts.append(('hair_behind_companion',hair))
 parts.extend([('companion',companion),('neck',neckSprite),('head',face)])
 return parts

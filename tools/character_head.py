"""Separate hair/head, attached animal ears, shoulder companion, neck and body."""
import cv2,numpy as np
from scipy.ndimage import distance_transform_edt
from character_segmentation import segmentation_masks

def companion_mask(shape):
 # Legacy helper for callers that need the seed outline; production uses refined source-pixel masks.
 from character_segmentation import COMPANION_OUTLINE
 mask=np.zeros(shape[:2],np.uint8);cv2.fillPoly(mask,[np.array(COMPANION_OUTLINE,np.int32)],255);return mask

def split_head(original,clean=None,segmentation=None):
 h,w=original.shape[:2];yy,xx=np.mgrid[:h,:w]
 masks=segmentation if segmentation is not None else segmentation_masks(original)
 bear=masks['companion'];ears=np.maximum(masks['head_ear_left'],masks['head_ear_right'])
 # Do not leave short static hair fragments on the shoulder/body layer.
 head=(yy<435).astype(np.uint8)*255
 for poly in [[[560,425],[613,420],[611,436],[595,440],[578,447],[569,444]],[[750,420],[815,420],[796,444],[775,448],[753,436]]]:
  cv2.fillPoly(head,[np.array(poly,np.int32)],255)
 guard=np.maximum(cv2.dilate(bear,np.ones((7,7),np.uint8)),cv2.dilate(ears,np.ones((3,3),np.uint8)))
 head[guard>0]=0
 # Exact front collar contour, fixed to the torso and drawn in front of the throat.
 collar=np.zeros((h,w),np.uint8)
 cv2.fillPoly(collar,[np.array([[618,430],[607,438],[598,461],[581,508],[580,570],[801,570],[783,491],[770,457],[764,438],[752,430],[753,444],[747,452],[731,461],[710,471],[700,477],[695,486],[693,493],[680,493],[676,480],[667,474],[649,466],[631,457],[619,451]],np.int32)],255)
 # Overlap the original under-jaw skin: shared transforms at the top eliminate the old y=435 tear.
 neck=np.zeros((h,w),np.uint8);cv2.fillPoly(neck,[np.array([[625,405],[743,405],[744,436],[744,442],[739,447],[728,456],[707,466],[697,473],[692,481],[690,488],[683,488],[680,478],[670,470],[651,462],[631,452],[623,446]],np.int32)],255)
 neck[(collar>0)|(guard>0)]=0
 head[collar>0]=0
 # Only erase the neck where it is actually under the moving head; keep the clothing fixed.
 body=original.copy();body[:,:,3]=np.where((yy<435)|(head>0)|(neck>0)|(bear>0)|(ears>0),0,body[:,:,3])
 face=original.copy();face[:,:,3]=np.where(head>0,face[:,:,3],0)
 neckSprite=original.copy();neckSprite[:,:,3]=np.rint(neckSprite[:,:,3]*np.minimum(1,cv2.distanceTransform(neck,cv2.DIST_L2,3)/2)).astype(np.uint8)
 collarSprite=original.copy();collarSprite[:,:,3]=np.where(collar>0,collarSprite[:,:,3],0)
 # Keep the original collar seam fixed; extrapolate only the hidden skin under its lip.
 # Nearest actual throat pixels avoid pulling any black collar line into the moving neck.
 skin=np.zeros((h,w),np.uint8)
 cv2.fillPoly(skin,[np.array([[635,442],[735,442],[731,450],[709,461],[697,468],[687,480],[679,470],[660,462],[639,451]],np.int32)],255)
 _,idx=distance_transform_edt(skin==0,return_indices=True)
 backing=original[idx[0],idx[1]].copy();cover=np.zeros((h,w),np.uint8)
 cv2.fillPoly(cover,[np.array([[626,423],[742,423],[753,444],[747,452],[731,461],[710,471],[700,477],[695,486],[693,493],[680,493],[676,480],[667,474],[649,466],[631,457],[619,451],[619,438]],np.int32)],255)
 backing[:,:,3]=cover
 parts=[('neck_backing',backing),('body',body),('collar',collarSprite)]
 if clean is not None:
  region=np.zeros((h,w),np.uint8);region[300:435,450:625]=255
  hair=clean.copy();hair[:,:,3]=np.where((cv2.dilate(bear,np.ones((7,7),np.uint8))>0)&(region>0),hair[:,:,3],0)
  parts.append(('hair_behind_companion',hair))
  hair=clean.copy();hair[:,:,3]=np.where(cv2.dilate(ears,np.ones((3,3),np.uint8))>0,hair[:,:,3],0)
  parts.append(('hair_behind_head_ears',hair))
 companion=original.copy();companion[:,:,3]=np.where(bear>0,companion[:,:,3],0)
 parts.extend([('companion',companion),('neck',neckSprite),('head',face)])
 for name in ['head_ear_left','head_ear_right']:
  sprite=original.copy();sprite[:,:,3]=np.where(masks[name]>0,sprite[:,:,3],0);parts.append((name,sprite))
 return parts

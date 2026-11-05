"""Separate hair/head, attached animal ears, shoulder companion, neck and body."""
import cv2,numpy as np
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
 neck=np.zeros((h,w),np.uint8);cv2.fillPoly(neck,[np.array([[619,435],[750,435],[751,446],[699,476],[691,490],[679,491],[671,475],[621,451]],np.int32)],255)
 neck[(head>0)|(guard>0)]=0
 body=original.copy();body[:,:,3]=np.where((yy<435)|(head>0)|(neck>0)|(bear>0)|(ears>0),0,body[:,:,3])
 face=original.copy();face[:,:,3]=np.where(head>0,face[:,:,3],0)
 neckSprite=original.copy();neckSprite[:,:,3]=np.where(neck>0,neckSprite[:,:,3],0)
 backing=np.zeros_like(original);cover=np.zeros((h,w),np.uint8)
 cv2.fillPoly(cover,[np.array([[633,410],[726,410],[752,442],[699,476],[691,490],[679,491],[671,475],[621,451],[619,434]],np.int32)],255)
 samples=original[442:446,640:736,:3].mean(axis=0)
 for x in range(619,753):backing[:,x,:3]=samples[min(95,max(0,x-640))]
 backing[:,:,3]=cover
 parts=[('neck_backing',backing),('body',body)]
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

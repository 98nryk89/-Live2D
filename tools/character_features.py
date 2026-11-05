"""Local source-pixel feature isolation. No global image warp or generative repaint."""
import cv2,numpy as np

def oval_alpha(w,h,feather=5):
 yy,xx=np.mgrid[:h,:w];rx=(w-1)/2;ry=(h-1)/2
 return np.clip((1-np.sqrt(((xx-rx)/rx)**2+((yy-ry)/ry)**2))*min(rx,ry)/feather,0,1)

def mouth_feature(image):
 # Exclude jaw, nose, hair and neck before searching for a lip component.
 x0,y0,x1,y1=640,350,733,414
 roi=image[y0:y1,x0:x1];gray=cv2.cvtColor(roi,cv2.COLOR_BGRA2GRAY)
 r=roi[:,:,2].astype(int);g=roi[:,:,1].astype(int)
 mask=((gray<150)|((r-g>65)&(g<195))).astype(np.uint8)*255
 n,labels,stats,cent=cv2.connectedComponentsWithStats(mask,8)
 options=[]
 for i in range(1,n):
  x,y,w,h,area=stats[i];cx,cy=cent[i]
  if area>=8 and x>0 and y>0 and x+w<roi.shape[1] and y+h<roi.shape[0]:
   options.append((abs(cx-43)+abs(cy-30)*.8,i))
 if not options:raise ValueError('Mouth feature not found')
 ids=[i for _,i in options]
 mask=np.isin(labels,ids).astype(np.uint8)*255
 points=cv2.findNonZero(mask);hull=cv2.convexHull(points)
 mask[:]=0;cv2.fillConvexPoly(mask,hull,255)
 mask=cv2.dilate(mask,np.ones((5,5),np.uint8))
 mask=cv2.GaussianBlur(mask,(3,3),.6)
 x,y,w,h=cv2.boundingRect(mask)
 feature=roi[y:y+h,x:x+w].copy();a=mask[y:y+h,x:x+w]
 feature[:,:,3]=np.minimum(feature[:,:,3],a)
 return feature,(x0+x,y0+y,w,h),mask,(x0,y0,x1,y1)

def mouth_sprites(images,levels=32):
 base=images['base'];box=(631,342,745,416);x0,y0,x1,y1=box
 clean=base[y0:y1,x0:x1].copy()
 _,_,mask,mb=mouth_feature(base)
 erase=np.zeros(clean.shape[:2],np.uint8);mx,my,mx1,my1=mb
 erase[my-y0:my1-y0,mx-x0:mx1-x0]=mask
 clean[:,:,:3]=cv2.inpaint(clean[:,:,:3],erase,3,cv2.INPAINT_TELEA)
 out={};bounds={}
 for role in ['mouth_a','mouth_i','mouth_e','smile','surprise']:
  feature,(fx,fy,fw,fh),_,_=mouth_feature(images[role]);bounds[role]=[fx,fy,fw,fh]
  for level in (range(1,levels+1) if role.startswith('mouth_') else [levels]):
   amount=level/levels;newh=max(2,round(fh*amount))
   glyph=cv2.resize(feature,(fw,newh),interpolation=cv2.INTER_AREA if amount<1 else cv2.INTER_LINEAR)
   # Move only the glyph; the surrounding skin, chin, and contour stay fixed.
   dst=clean.copy();tx=fx-x0;ty=round(fy+fh/2-newh/2)-y0
   alpha=glyph[:,:,3:4].astype(np.float32)/255
   region=dst[ty:ty+newh,tx:tx+fw]
   region[:,:,:3]=np.rint(glyph[:,:,:3]*alpha+region[:,:,:3]*(1-alpha)).astype(np.uint8)
   dst[:,:,3]=np.rint(dst[:,:,3]*oval_alpha(dst.shape[1],dst.shape[0])).astype(np.uint8)
   out[(role,level)]=dst
 return out,box,bounds

EYES={
 'left':{'box':(561,272,671,341),'xs':[574,585,600,620,640,655],
         'upper':[315,306,296,293,295,303],'lower':[315,316,323,322,313,303],
         'closed':[320,324,321,314,312,315], 'target_closed':[315,317,317,314,309,303]},
 'right':{'box':(690,253,799,326),'xs':[701,710,725,745,765,784],
          'upper':[293,287,279,276,281,288],'lower':[293,300,306,306,301,288],
          'closed':[307,309,300,298,301,307],'target_closed':[293,300,302,300,296,288]}}

def eye_sprites(base,closed,eye,levels=40):
 spec=EYES[eye];x0,y0,x1,y1=spec['box'];raw=base[y0:y1,x0:x1].copy();cl=closed[y0:y1,x0:x1].copy();h,w=raw.shape[:2]
 yy,xx=np.mgrid[:h,:w].astype(np.float32);gx=xx+x0
 top=np.interp(gx,spec['xs'],spec['upper'])-y0
 bottom=np.interp(gx,spec['xs'],spec['lower'])-y0
 sourceEnd=np.interp(gx,spec['xs'],spec['closed'])-y0
 end=np.interp(gx,spec['xs'],spec['target_closed'])-y0
 valid=(gx>=spec['xs'][0])&(gx<=spec['xs'][-1])
 eyeMask=((yy>=top-7)&(yy<=bottom+4)&valid).astype(np.uint8)*255
 closedMask=((yy>=end-7)&(yy<=end+7)&valid).astype(np.uint8)*255
 removal=cv2.dilate(np.maximum(eyeMask,closedMask),np.ones((3,3),np.uint8))
 skin=raw.copy();skin[:,:,:3]=cv2.inpaint(raw[:,:,:3],removal,5,cv2.INPAINT_TELEA)
 # Opacity coverage must cover the original eye throughout every blink stage.
 cover=cv2.GaussianBlur(cv2.dilate(removal,np.ones((7,7),np.uint8)),(0,0),1.4)/255
 cover=np.where(removal>0,1,cover)
 results=[]
 for level in range(levels):
  opened=level/levels;closure=1-opened
  targetTop=top*opened+end*closure
  targetBottom=bottom*opened+end*closure
  dst=skin.copy()
  # Fixed iris/eyeball: eyelid aperture clips source pixels rather than squeezing them.
  aperture=np.clip(yy-targetTop+.5,0,1)*np.clip(targetBottom-yy+.5,0,1)*valid
  dst[:,:,:3]=np.rint(raw[:,:,:3]*aperture[:,:,None]+dst[:,:,:3]*(1-aperture[:,:,None])).astype(np.uint8)
  # Source lash bands follow the lid. Blend co-located bands, never two eye images.
  mapOpen=(yy-targetTop+top).astype(np.float32);mapClosed=(yy-targetTop+sourceEnd).astype(np.float32)
  lashOpen=cv2.remap(raw,xx,mapOpen,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
  lashClosed=cv2.remap(cl,xx,mapClosed,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
  band=(np.clip(6-np.abs(yy-targetTop),0,1)*valid)
  grayOpen=cv2.cvtColor(lashOpen,cv2.COLOR_BGRA2GRAY);grayClosed=cv2.cvtColor(lashClosed,cv2.COLOR_BGRA2GRAY)
  ao=band*np.clip((135-grayOpen.astype(float))/45,0,1)*opened
  ac=band*np.clip((135-grayClosed.astype(float))/45,0,1)*closure
  a=ao+ac;rgb=(lashOpen[:,:,:3]*ao[:,:,None]+lashClosed[:,:,:3]*ac[:,:,None])/(a[:,:,None]+1e-6)
  dst[:,:,:3]=np.rint(rgb*a[:,:,None]+dst[:,:,:3]*(1-a[:,:,None])).astype(np.uint8)
  dst[:,:,3]=np.rint(dst[:,:,3]*cover).astype(np.uint8)
  results.append(dst)
 return results,spec['box']

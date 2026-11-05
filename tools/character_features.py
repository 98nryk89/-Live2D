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

def lip_axis(feature,round_mouth=False):
 if round_mouth:
  y,x=np.where(feature[:,:,3]>128)
  values,vectors=np.linalg.eigh(np.cov(np.stack([x,y])))
  # A near-circle has no stable principal direction; treat its authored pose as upright.
  if values[-1]/values[0]<1.1:return 0.
  i=np.argmax(np.abs(vectors[0]));angle=np.degrees(np.arctan2(vectors[1,i],vectors[0,i]))
  return float((angle+90)%180-90)
 gray=cv2.cvtColor(feature,cv2.COLOR_BGRA2GRAY)
 m=(feature[:,:,3]>128)&(gray<145)
 y,x=np.where(m)
 lo,hi=np.quantile(x,[.1,.9]);left=y[x<=lo];right=y[x>=hi]
 return float(np.degrees(np.arctan2(np.median(right)-np.median(left),np.median(x[x>=hi])-np.median(x[x<=lo]))))

def rotate_glyph(rgba,angle):
 h,w=rgba.shape[:2];rad=np.radians(angle);nw=int(np.ceil(abs(w*np.cos(rad))+abs(h*np.sin(rad))))+2;nh=int(np.ceil(abs(h*np.cos(rad))+abs(w*np.sin(rad))))+2
 A=cv2.getRotationMatrix2D((w/2,h/2),angle,1);A[:,2]+=[(nw-w)/2,(nh-h)/2]
 pm=rgba.astype(np.float32);pm[:,:,:3]*=pm[:,:,3:4]/255
 dst=cv2.warpAffine(pm,A,(nw,nh),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
 dst[:,:,:3]/=np.maximum(dst[:,:,3:4]/255,.001)
 return np.clip(np.rint(dst),0,255).astype(np.uint8)

def mouth_axes(images):
 target=lip_axis(mouth_feature(images['base'])[0])
 return {'base_axis_degrees_image':target,'roles':{role:{'source_axis':lip_axis(mouth_feature(images[role])[0],round_mouth=role in ['mouth_a','surprise']),'target_axis':target} for role in ['mouth_a','mouth_i','mouth_e','smile','surprise']}}

def mouth_sprites(images,levels=32):
 base=images['base'];box=(628,335,749,421);x0,y0,x1,y1=box
 clean=base[y0:y1,x0:x1].copy()
 base_feature,_,mask,mb=mouth_feature(base);angle=lip_axis(base_feature)
 erase=np.zeros(clean.shape[:2],np.uint8);mx,my,mx1,my1=mb
 erase[my-y0:my1-y0,mx-x0:mx1-x0]=mask
 clean[:,:,:3]=cv2.inpaint(clean[:,:,:3],erase,3,cv2.INPAINT_TELEA)
 out={};bounds={}
 for role in ['mouth_a','mouth_i','mouth_e','smile','surprise']:
  feature,(fx,fy,fw,fh),_,_=mouth_feature(images[role]);flat=rotate_glyph(feature,lip_axis(feature,round_mouth=role in ['mouth_a','surprise']))
  for level in (range(1,levels+1) if role.startswith('mouth_') else [levels]):
   amount=level/levels;newh=max(2,round(flat.shape[0]*amount))
   scaled=cv2.resize(flat,(flat.shape[1],newh),interpolation=cv2.INTER_AREA if amount<1 else cv2.INTER_LINEAR)
   glyph=rotate_glyph(scaled,-angle);gh,gw=glyph.shape[:2]
   dst=clean.copy();tx=round(fx+fw/2-gw/2)-x0;ty=round(fy+fh/2-gh/2)-y0
   if tx<0 or ty<0 or tx+gw>dst.shape[1] or ty+gh>dst.shape[0]:raise ValueError((role,level,'mouth patch crop'))
   alpha=glyph[:,:,3:4].astype(np.float32)/255;region=dst[ty:ty+gh,tx:tx+gw]
   region[:,:,:3]=np.rint(glyph[:,:,:3]*alpha+region[:,:,:3]*(1-alpha)).astype(np.uint8)
   dst[:,:,3]=np.rint(dst[:,:,3]*oval_alpha(dst.shape[1],dst.shape[0],feather=3)).astype(np.uint8)
   out[(role,level)]=dst
   if level==levels:bounds[role]=[tx+x0,ty+y0,gw,gh]
 return out,box,bounds

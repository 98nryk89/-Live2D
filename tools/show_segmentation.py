"""Visual audit of actual production ownership masks, with literal source cutouts."""
from pathlib import Path
import sys,cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from character_segmentation import segmentation_masks
from character_head import split_head
D=R/'docs/verification/repair_0.5.0';D.mkdir(exist_ok=True)
base=cv2.imread(str(R/'character_materials/mukachi_kachi/base.png'),-1);clean=cv2.imread(str(R/'projects/mukachi_kachi/aligned/clean_backing.png'),-1)
masks=segmentation_masks(base);backed=cv2.imread(str(R/'projects/mukachi_kachi/accessory_backing.png'),-1);parts=dict(split_head(backed,clean=clean,segmentation=masks))
colors={'body':(125,130,140),'head':(40,210,235),'companion':(235,60,190),'head_ear_left':(255,170,35),'head_ear_right':(255,170,35),'neck':(125,130,140)}
rgb=cv2.cvtColor(base,cv2.COLOR_BGRA2RGBA);paint=rgb.copy();owner=np.zeros(base.shape[:2],np.uint8)
for n,code in [('head',2),('neck',1),('body',1),('head_ear_left',4),('head_ear_right',4),('companion',3)]:
 select=parts[n][:,:,3]>16;paint[select,:3]=(paint[select,:3]*.28+np.array(colors[n])*.72).astype(np.uint8);owner[select]=code
bg=Image.new('RGBA',(base.shape[1],base.shape[0]),(37,39,45,255));bg.alpha_composite(Image.fromarray(paint))
original=Image.new('RGBA',bg.size,(37,39,45,255));original.alpha_composite(Image.fromarray(rgb))
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',25)
small=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',20)
# Full ownership and two detailed junctions in one reviewable figure.
canvas=Image.new('RGB',(1550,1100),(25,27,32));draw=ImageDraw.Draw(canvas)
draw.text((24,12),'実際の切り分けマスク（0.5.0）',font=font,fill='white')
full=bg.convert('RGB');full.thumbnail((830,940));canvas.paste(full,(0,95))
draw.text((850,95),'頭上の熊耳／髪の境界',font=small,fill='white')
zoom=bg.crop((460,80,865,215)).resize((660,220),Image.Resampling.NEAREST).convert('RGB');canvas.paste(zoom,(850,135))
draw.text((850,385),'肩の熊の耳／髪の境界',font=small,fill='white')
zoom=bg.crop((440,310,615,455)).resize((660,547),Image.Resampling.NEAREST).convert('RGB');canvas.paste(zoom,(850,425))
for x,col,text in [(24,(40,210,235),'水色：頭・髪'),(380,(235,60,190),'紫：肩の熊'),(760,(255,170,35),'橙：頭上の熊耳'),(1190,(125,130,140),'灰：衣装・首')]:
 draw.rectangle((x,1050,x+25,1075),fill=col);draw.text((x+35,1045),text,font=small,fill='white')
canvas.save(D/'segmentation_overview.png')
# Detail: original, ownership colour, actual head foreground, actual shoulder companion.
box=(450,315,605,450);tilew,tileh=465,405
strip=Image.new('RGB',(tilew*4,tileh+60),(25,27,32));draw=ImageDraw.Draw(strip)
for i,(name,im) in enumerate([('元絵',original),('色分け',bg),('頭・髪だけ',Image.fromarray(cv2.cvtColor(parts['head'],cv2.COLOR_BGRA2RGBA))),('肩の熊だけ',Image.fromarray(cv2.cvtColor(parts['companion'],cv2.COLOR_BGRA2RGBA)))]):
 tile=im.crop(box);back=Image.new('RGBA',tile.size,(65,67,75,255));back.alpha_composite(tile);strip.paste(back.convert('RGB').resize((tilew,tileh),Image.Resampling.NEAREST),(i*tilew,50));draw.text((i*tilew+12,8),name,font=font,fill='white')
strip.save(D/'segmentation_bear_zoom.png')
for n in ['head','companion','head_ear_left','head_ear_right']:
 cv2.imwrite(str(D/(n+'_actual_cutout.png')),parts[n]);cv2.imwrite(str(D/(n+'_mask.png')),np.where(parts[n][:,:,3]>0,255,0).astype(np.uint8))
cv2.imwrite(str(D/'ownership_ids.png'),owner)
print(D/'segmentation_overview.png')

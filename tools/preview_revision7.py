"""Review source-preserving throat deformation and independent bear blink in the real renderer."""
from pathlib import Path
from PIL import Image,ImageDraw
import io,math
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'docs/verification/repair_0.7.0';D.mkdir(exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1350,'height':1165},device_scale_factor=1);page.goto('http://127.0.0.1:8089/mukachi_kachi_webcam.html');page.wait_for_function('window.READY===true');page.evaluate('M.stop();M.reset();M.auto={blink:false,breath:false,idle:false,physics:false,companionBlink:false};M.opts.view=[0,0,1350,1165]')
 page.add_style_tag(content='html,body,#stage{background:transparent!important}#app{display:block}#panel,#msg{display:none}#stage{width:1350px;height:1165px}')
 def shot():
  im=Image.open(io.BytesIO(page.locator('#c').screenshot(omit_background=True))).convert('RGBA');bg=Image.new('RGBA',im.size,(40,42,50));bg.alpha_composite(im);return bg
 sheet=Image.new('RGB',(1650,850),(40,42,50));draw=ImageDraw.Draw(sheet)
 for i,z in enumerate([-5,0,5]):
  page.evaluate('z=>{M.reset();M.setParam("AngleZ",z);M.renderStill()}',z);bg=shot();sheet.paste(bg.crop((340,0,1020,680)).resize((550,550)).convert('RGB'),(i*550,30));sheet.paste(bg.crop((570,380,790,500)).resize((550,300)).convert('RGB'),(i*550,550));draw.text((i*550+5,5),str(z),fill='white')
 sheet.save(D/'neck_review.jpg')
 # Continuous simulated movements, not camera footage. One bear blink appears around t=3.9 s.
 page.evaluate('M.reset();M.auto.physics=true;M.auto.companionBlink=true')
 frames=[]
 for n in range(42):
  page.evaluate('''n=>{const t=n*.1;M.setParams({AngleZ:5*Math.sin(t*2.2),BodyX:.12*Math.sin(t*2.7),BodyY:.05*Math.sin(t*3.1)});M.renderStill(6)}''',n)
  bg=shot();frame=Image.new('RGB',(1100,600),(40,42,50));frame.paste(bg.crop((340,0,1020,680)).resize((600,600)).convert('RGB'),(0,0));frame.paste(bg.crop((600,380,800,500)).resize((500,300)).convert('RGB'),(600,0));frame.paste(bg.crop((400,377,540,461)).resize((500,300)).convert('RGB'),(600,300));frames.append(frame)
 frames[0].save(D/'neck_bear_motion.gif',save_all=True,append_images=frames[1:],duration=100,loop=0)
 b.close()
print(D/'neck_bear_motion.gif')

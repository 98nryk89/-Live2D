"""Capture real renderer motion; fixed pose isolates ornaments from tracking/body motion."""
from pathlib import Path
import io,json
import numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'docs/verification/repair_0.5.0'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 page=b.new_page(viewport={'width':1350,'height':1165},device_scale_factor=1);page.goto('http://127.0.0.1:8089/mukachi_kachi_webcam.html');page.wait_for_function('window.READY===true')
 assert page.evaluate('M.auto.physics')
 page.evaluate('M.stop();M.reset();M.auto={blink:false,idle:false,breath:false,physics:true};M.opts.view=[0,0,1350,1165]')
 page.add_style_tag(content='html,body,#stage{background:transparent!important}#app{display:block}#panel,#msg{display:none}#stage{width:1350px;height:1165px}')
 frames=[];positions={};anchor_errors=[]
 for n in range(40):
  data=page.evaluate('''()=>{M.renderStill(6);return M.parts.filter(p=>/^(earring_|tassel_)/.test(p.id)).map(p=>({id:p.id,xy:Array.from(p._pos),pivot:p.effects[0].pivot,rot:p.effects[0].map,phys:M.params[p.effects[0].param]}))}''')
  for row in data:positions.setdefault(row['id'],[]).append(row['xy'])
  shot=Image.open(io.BytesIO(page.locator('#c').screenshot(omit_background=True))).convert('RGBA');bg=Image.new('RGBA',shot.size,(44,46,54,255));bg.alpha_composite(shot)
  canvas=Image.new('RGB',(1040,650),(25,27,32));draw=ImageDraw.Draw(canvas)
  canvas.paste(bg.crop((555,345,825,470)).resize((702,325)).convert('RGB'),(8,35))
  canvas.paste(bg.crop((880,660,1015,960)).resize((270,600)).convert('RGB'),(755,35))
  draw.text((10,10),'EARRINGS / fixed head and body',fill='white');draw.text((755,10),'TASSELS',fill='white')
  draw.text((10,390),'Actual browser render / physics ON / no tracking input',fill='white')
  frames.append(canvas)
 ranges={k:float(np.max(np.ptp(np.array(v),axis=0))) for k,v in positions.items()}
 assert len(ranges)==9 and min(ranges.values())>2,ranges
 page.evaluate('M.auto.physics=false;M._drive(1/60)');assert page.evaluate('M.rig.physics.every(p=>M.params[p.output]===0)')
 frames[0].save(D/'ornaments_motion.gif',save_all=True,append_images=frames[1:],duration=100,loop=0)
 (D/'ornaments_motion_results.json').write_text(json.dumps({'fixed_pose_motion_range_source_px':ranges,'physics_default_on':True,'physics_off_resets':True,'scope':'actual browser renderer with simulated time; physical camera unverified'},indent=2))
 print(ranges);b.close()

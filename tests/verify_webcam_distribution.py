from pathlib import Path
import io,json,zipfile,re,hashlib
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];D=R/'docs/verification'
results=[]
def check(label,ok):
 assert ok,label
 results.append(label);print('PASS',label)
html=(R/'dist/mukachi_kachi_webcam.html').read_text()
check('no iPhone transport or bridge bundled','WebSocket(' not in html and 'iOSTrackingDataRequest' not in html and 'L2DInput' not in html)
with zipfile.ZipFile(R/'dist/mukachi_kachi_webcam_0.6.0.zip') as z:check('archive contains exact standalone HTML',z.read('Mukachi_Webcam_0.6.0/mukachi_kachi_webcam_0.6.0.html')==html.encode())
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream'])
 pg=b.new_page(viewport={'width':1400,'height':1000});errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
 pg.goto('http://127.0.0.1:8089/mukachi_kachi_webcam.html');pg.wait_for_function('window.READY===true')
 check('standalone model loads and camera button present',pg.locator('#cam').is_visible())
 pg.screenshot(path=str(D/'webcam_standalone.png'))
 # Face detector is mocked here; getUserMedia acquires Chromium's real synthetic capture device.
 pg.evaluate("()=>{L2DTracker.prototype.load=async function(){this.landmarker={detectForVideo(){return {faceLandmarks:[]}},close(){}}}}")
 pg.locator('#cam').click();pg.wait_for_function('window.webcamTracker?.running===true')
 check('camera stream starts without relay',pg.evaluate('document.querySelector("#vid").srcObject.getVideoTracks()[0].readyState==="live"'))
 pg.locator('#cam').click();check('stop releases capture device',pg.evaluate('document.querySelector("#vid").srcObject.getVideoTracks().every(t=>t.readyState==="ended")'))
 pg.evaluate("()=>{navigator.mediaDevices.getUserMedia=async()=>{throw new DOMException('Permission denied','NotAllowedError')}}")
 pg.locator('#cam').click();pg.wait_for_function("document.querySelector('#camst').textContent.includes('Macの')")
 check('denied camera has clear guidance',not pg.evaluate('webcamTracker.running'))
 check('no browser script errors',not errors)
 b.close()
(D/'webcam_distribution_results.json').write_text(json.dumps({'passed':results,'count':len(results),'scope':'model and native fake camera verified; face detector mocked, actual MediaPipe model network restricted; physical Mac camera unverified'},ensure_ascii=False,indent=2))

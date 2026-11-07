/* Neck surface: two moving jaw attachments, a fixed collar base and a curved centreline. */
(function(global){
 'use strict';
 const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
 function frame(d,P){
  const parent={parentHead:d.head,bodyScale:[0,0]},L=L2DGravity.parentPoint(parent,P,...d.left),R=L2DGravity.parentPoint(parent,P,...d.right);
  const span=Math.hypot(R[0]-L[0],R[1]-L[1]),top=[(L[0]+R[0])/2,(L[1]+R[1])/2],axis=[-(R[1]-L[1])/span,(R[0]-L[0])/span],base=d.base,h=Math.hypot(base[0]-top[0],base[1]-top[1]);
  return {points:[top,[top[0]+axis[0]*h*.36,top[1]+axis[1]*h*.36],[base[0],base[1]-h*.36],base],topHalf:span/2,axis,cross:[(R[0]-L[0])/span,(R[1]-L[1])/span]};
 }
 function point(d,P,x,y,f=frame(d,P)){
  const v=(y-d.restTop)/(d.restBottom-d.restTop),t=clamp(v,0,1),a=1-t,q=f.points;
  let X=a*a*a*q[0][0]+3*a*a*t*q[1][0]+3*a*t*t*q[2][0]+t*t*t*q[3][0],Y=a*a*a*q[0][1]+3*a*a*t*q[1][1]+3*a*t*t*q[2][1]+t*t*t*q[3][1];
  let dx=3*a*a*(q[1][0]-q[0][0])+6*a*t*(q[2][0]-q[1][0])+3*t*t*(q[3][0]-q[2][0]),dy=3*a*a*(q[1][1]-q[0][1])+6*a*t*(q[2][1]-q[1][1])+3*t*t*(q[3][1]-q[2][1]);
  const length=Math.hypot(dx,dy)||1;dx/=length;dy/=length;
  if(v<0){X+=dx*v*(d.restBottom-d.restTop);Y+=dy*v*(d.restBottom-d.restTop);}
  if(v>1){X+=dx*(v-1)*(d.restBottom-d.restTop);Y+=dy*(v-1)*(d.restBottom-d.restTop);}
  const radius=f.topHalf*(1-t)+d.bottomHalf*t+1.2*Math.sin(Math.PI*t),u=(x-d.sourceCenterX)/d.sourceHalf;
  // Interpolate the skin cross-section independently of centreline curvature.
  // This avoids inverting the broad hidden skirt when yaw/pitch shorten the neck.
  const blend=t*t*(3-2*t),angle=Math.atan2(f.cross[1],f.cross[0])*(1-blend);
  return [X+Math.cos(angle)*u*radius,Y+Math.sin(angle)*u*radius];
 }
 function deform(part,d,P){const f=frame(d,P);for(let i=0;i<part._pos.length;i+=2){const q=point(d,P,part._pos[i],part._pos[i+1],f);part._pos[i]=q[0];part._pos[i+1]=q[1];}}
 global.L2DNeck={frame,point,deform};
})(window);

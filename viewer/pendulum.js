/* Planar pendulum in model-pixel coordinates: +Y is gravity, support can move. */
(function(global){
  'use strict';
  const DEG=Math.PI/180,clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
  function parentPoint(d,P,x,y){
    const e=d.parentHead;
    if(e){
      const g=e.gain??1,a=((P[e.yaw]||0)+(P.IdleX||0)*(e.idle||0))*DEG*g;
      const b=((P[e.pitch]||0)+(P.IdleY||0)*(e.idle||0))*DEG*g;
      const [cx,cy]=e.center,u=x-cx,v=y-cy;
      const r2=(u/(e.Rx||e.R))**2+(v/(e.Ry||e.R))**2;
      const z=(e.zoff||0)+(e.k??1)*(e.Rz||e.R)*Math.sqrt(Math.max(1-r2,e.zmin||0));
      const X=cx+u*Math.cos(a)+z*Math.sin(a),z1=-u*Math.sin(a)+z*Math.cos(a);
      x=X;y=cy+v*Math.cos(b)-z1*Math.sin(b);
      if(e.restRoll){const a=e.restRoll*DEG,c=Math.cos(a),s=Math.sin(a),p=e.restRollPivot||e.pivot||e.center,dx=x-p[0],dy=y-p[1];x=p[0]+dx*c-dy*s;y=p[1]+dx*s+dy*c;}
      const p=e.pivot||e.center,r=(P[e.roll]||0)*DEG*(e.rgain??1),c=Math.cos(r),s=Math.sin(r),dx=x-p[0],dy=y-p[1];x=p[0]+dx*c-dy*s;y=p[1]+dx*s+dy*c;
    }
    return [x+(P.BodyX||0)*d.bodyScale[0],y+(P.BodyY||0)*d.bodyScale[1]];
  }
  function frame(d,P){
    const pivot=parentPoint(d,P,...d.pivot),com=parentPoint(d,P,...d.com);
    return {pivot,com,angle:Math.atan2(-(com[0]-pivot[0]),com[1]-pivot[1])};
  }
  function step(s,d,P,dt){
    const pivot=frame(d,P).pivot;
    if(!s.pendulum)s.pendulum={theta:0,omega:0,pivot:pivot.slice(),vx:0,vy:0,ax:0,ay:0};
    const q=s.pendulum,hdt=Math.max(dt,1e-5),vx=(pivot[0]-q.pivot[0])/hdt,vy=(pivot[1]-q.pivot[1])/hdt;
    const filter=1-Math.exp(-hdt/(d.accelerationFilter||.045));
    q.ax+=(clamp((vx-q.vx)/hdt,-12000,12000)-q.ax)*filter;
    q.ay+=(clamp((vy-q.vy)/hdt,-12000,12000)-q.ay)*filter;
    q.vx=vx;q.vy=vy;q.pivot=pivot;
    const g=d.gravity||2200,L=Math.max(12,d.length),damping=2*(d.dampingRatio||.24)*Math.sqrt(g/L),gain=P.AccessoryGain??1;
    const n=Math.max(1,Math.ceil(hdt/.004)),h=hdt/n,limit=(d.limitDegrees||65)*DEG;
    for(let i=0;i<n;i++){
      // Support acceleration changes effective gravity. theta=0 hangs vertically down.
      const acceleration=(gain*q.ax*Math.cos(q.theta)-(g-gain*q.ay)*Math.sin(q.theta))/L-damping*q.omega;
      q.omega+=acceleration*h;q.theta+=q.omega*h;
      if(Math.abs(q.theta)>limit){q.theta=clamp(q.theta,-limit,limit);if(q.theta*q.omega>0)q.omega=0;}
    }
    P[d.output]=q.theta/DEG;
  }
  function deform(part,d,P){
    const f=frame(d,P),angle=(P[d.output]||0)*DEG-f.angle,c=Math.cos(angle),s=Math.sin(angle),[px,py]=f.pivot;
    for(let i=0;i<part._pos.length;i+=2){const dx=part._pos[i]-px,dy=part._pos[i+1]-py;part._pos[i]=px+dx*c-dy*s;part._pos[i+1]=py+dx*s+dy*c;}
  }
  global.L2DGravity={parentPoint,frame,step,deform};
})(window);

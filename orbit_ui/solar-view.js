'use strict';
// Coordinates come from Python; only the projection and drawing happen here.
const SolarView = (() => {
  let scene = null, time = 0, seconds = 0, scope = 'all';
  const byId = id => document.getElementById(id);
  const clamp = (n,a,b) => Math.min(b,Math.max(a,n));
  function pointAt(body,t) {
    const points = body.trajectory;
    if(t >= points.at(-1)[0]) return points.at(-1).slice(1);
    let low=0,high=points.length-1;
    while(high-low>1){const m=(low+high)>>1;if(points[m][0]<t)low=m;else high=m;}
    const a=points[low],b=points[high],f=clamp((t-a[0])/(b[0]-a[0]),0,1);
    return [a[1]+(b[1]-a[1])*f,a[2]+(b[2]-a[2])*f];
  }
  function receive(data) {
    scene = data.scene; time=0; seconds=0;
    if(!scene) return;
    byId('solar-legend').innerHTML=scene.bodies.map(b=>`<span><i style="background:${b.color}"></i>${escapeHTML(b.name)}</span>`).join('');
    byId('scene-model-note').textContent=scene.note;
    byId('scene-detail-note').textContent=scene.detail;
    byId('scene-projection-note').textContent=scene.projection_note;
    const titles={blackhole:'추가 천체가 지구를 끌어당겨요',sirius:'태양빛에 별빛이 더해져요',earth_mass:'크기는 같아도 끄는 힘은 달라져요',earth_rotation:'하루가 달라지는 지구',earth_distance:'달라진 거리에서 받는 햇빛',solar_luminosity:'태양이 밝아지면 지구는?',earth_albedo:'햇빛을 얼마나 돌려보낼까요?',atmosphere_loss:'지구를 감싼 대기의 양',magnetic_field:'지구를 감싼 자기권의 크기'};
    byId('earth-focus-title').textContent=titles[scene.focus.kind];
    const m=scene.focus.metric;
    byId('earth-focus-value').textContent=`${m.label} ${fmt(m.value,2)} ${m.unit}`;
    const notes={earth_mass:'지구의 반지름은 그대로예요. 화살표로 끄는 힘을 비교해요.',earth_rotation:'자전은 속도 차이를 보기 쉽게 느리게 보여줘요.',earth_albedo:'노란 빛은 들어오고, 밝은 빛은 반사되어 나가요.',atmosphere_loss:'남은 대기의 양을 파란 띠로 표현해요.',magnetic_field:'점선은 현재 자기권의 기준 크기예요. 0%에서는 고유 자기장 띠를 그리지 않아요.'};
    byId('earth-focus-note').textContent=notes[scene.focus.kind] || (scene.source?'수치 표는 시작 순간의 조건을 기준으로 비교해요.':'빛과 열의 변화를 비교하는 모형 그림이에요.');
    byId('solar-system-canvas').setAttribute('aria-label',`${data.scenario.title} 실험. 태양과 수성·금성·지구·화성·목성·토성·천왕성·해왕성을 표시해요. ${scene.note}`);
    byId('earth-focus-canvas').setAttribute('aria-label',`${titles[scene.focus.kind]}. ${m.label} ${fmt(m.value,2)}${m.unit}. ${byId('earth-focus-note').textContent}`);
    updateTime();
  }
  function updateTime() {
    if(!scene)return;
    const day=Math.round(time*365.25);
    byId('scene-day').textContent=`${day}일째`;
    byId('scene-timeline').value=time/scene.duration_years*1000;
    byId('scene-timeline').setAttribute('aria-valuetext',`${day}일째, 총 ${Math.round(scene.duration_years*365.25)}일`);
    const ended=scene.bodies.filter(b=>b.status!=='complete'&&time>=b.end_years);
    const near=ended.filter(b=>b.status==='close_approach'),limited=ended.filter(b=>b.status==='step_limit');
    const message=[near.length?`${near.map(b=>b.name).join('·')}: 근접하여 궤도 표시를 멈췄어요.`:'',limited.length?`${limited.map(b=>b.name).join('·')}: 계산 한도에 도달해 표시를 멈췄어요.`:'',ended.length?'이후 위치나 충돌 여부는 이 모형으로 판단하지 않아요.':''].filter(Boolean).join(' ');
    byId('scene-events').hidden=!message;
    if(byId('scene-events').textContent!==message)byId('scene-events').textContent=message;
  }
  function setScope(value){scope=value==='inner'?'inner':'all';document.querySelectorAll('[data-scene-view]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.sceneView===scope));byId('scene-view-label').textContent=scope==='all'?'태양계 전체 · 거리 간격 축소':'안쪽 행성 · 거리 간격 축소';draw();}
  function reset(){time=0;seconds=0;updateTime();draw();}
  function seek(fraction){if(!scene)return;time=clamp(fraction,0,1)*scene.duration_years;seconds=time/.12;updateTime();draw();}
  function tick(delta){if(!scene||!playing)return;time=Math.min(scene.duration_years,time+delta*.12*speed);seconds+=delta*speed;if(time>=scene.duration_years){playing=false;updatePlayButton();}updateTime();draw();}
  function arrow(ctx,x,y,tx,ty,color,width=1.5){const a=Math.atan2(ty-y,tx-x);ctx.strokeStyle=color;ctx.fillStyle=color;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(tx,ty);ctx.stroke();ctx.beginPath();ctx.moveTo(tx,ty);ctx.lineTo(tx-7*Math.cos(a-.45),ty-7*Math.sin(a-.45));ctx.lineTo(tx-7*Math.cos(a+.45),ty-7*Math.sin(a+.45));ctx.closePath();ctx.fill();}
  function sphere(ctx,x,y,r,color,ring=false){const g=ctx.createRadialGradient(x-r*.3,y-r*.3,0,x,y,r);g.addColorStop(0,color);g.addColorStop(1,'#233040');ctx.fillStyle=g;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();if(ring){ctx.save();ctx.translate(x,y);ctx.rotate(-.3);ctx.strokeStyle='#dac994aa';ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(0,0,r*1.8,r*.5,0,0,Math.PI*2);ctx.stroke();ctx.restore();}}
  function drawSystem(){
    const info=canvasContext('solar-system-canvas');if(!info)return;
    const {ctx,w,h}=info,extent=scope==='all'?35:5.8,pad=w<400?30:40,R=Math.min(w/2-pad,h/2-28),cx=w/2,cy=h/2;
    // Monotonic radial compression preserves direction, not physical distances.
    const project=(x,y)=>{const r=Math.hypot(x,y),k=r?R*Math.log1p(r/.4)/Math.log1p(extent/.4)/r:0;return[cx+x*k,cy-y*k];};
    for(let i=0;i<110;i++){const x=((Math.sin(i*54.31+4)*43758.54)%1+1)%1*w,y=((Math.sin(i*12.91+8)*27182.31)%1+1)%1*h;ctx.fillStyle=i%8?'#7491ba33':'#a4bbd755';ctx.beginPath();ctx.arc(x,y,i%8?.5:.9,0,Math.PI*2);ctx.fill();}
    ctx.save();ctx.beginPath();ctx.rect(7,18,w-14,h-25);ctx.clip();
    scene.bodies.forEach(b=>{const r=project(b.radius_au,0)[0]-cx;ctx.setLineDash([3,5]);ctx.strokeStyle=b.id==='earth'?'#8eafa855':'#4b5f773c';ctx.lineWidth=1;ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.stroke();});ctx.setLineDash([]);
    if(scene.focus.kind==='earth_distance'){ctx.strokeStyle='#b6c0ce66';ctx.setLineDash([2,5]);ctx.beginPath();ctx.arc(cx,cy,project(1,0)[0]-cx,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);}
    if(scene.source)scene.bodies.forEach(b=>{ctx.beginPath();b.trajectory.forEach((p,i)=>{const q=project(p[1],p[2]);i?ctx.lineTo(...q):ctx.moveTo(...q);});ctx.strokeStyle=b.id==='earth'?'#76e6cf55':`${b.color}26`;ctx.lineWidth=b.id==='earth'?1.5:.9;ctx.stroke();ctx.beginPath();b.trajectory.filter(p=>p[0]<=time).forEach((p,i)=>{const q=project(p[1],p[2]);i?ctx.lineTo(...q):ctx.moveTo(...q);});ctx.strokeStyle=b.id==='earth'?'#8bf9df':`${b.color}aa`;ctx.lineWidth=b.id==='earth'?2:1;ctx.stroke();});
    const earth=scene.bodies.find(b=>b.id==='earth'),earthPoint=pointAt(earth,time),ep=project(...earthPoint);
    const sourcePoint=scene.source?project(scene.source.x,scene.source.y):null;
    if(['sirius','solar_luminosity','earth_distance','earth_albedo','atmosphere_loss'].includes(scene.focus.kind)){
      ctx.strokeStyle='#f9cf7755';ctx.lineWidth=clamp(scene.focus.brightness*2,1,4);ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(...ep);ctx.stroke();
      if(sourcePoint){ctx.strokeStyle='#b6dfff88';ctx.beginPath();ctx.moveTo(...sourcePoint);ctx.lineTo(...ep);ctx.stroke();}
    }
    if(scene.source&&time<earth.end_years){const dx=sourcePoint[0]-ep[0],dy=sourcePoint[1]-ep[1],len=Math.hypot(dx,dy);if(len>20)arrow(ctx,ep[0],ep[1],ep[0]+dx*.65,ep[1]+dy*.65,'#d9b3fb',1.3);}
    const glow=ctx.createRadialGradient(cx,cy,0,cx,cy,44);glow.addColorStop(0,`rgba(255,185,93,${clamp(.25*scene.focus.brightness,.08,.6)})`);glow.addColorStop(1,'#ffb95d00');ctx.fillStyle=glow;ctx.beginPath();ctx.arc(cx,cy,44,0,Math.PI*2);ctx.fill();sphere(ctx,cx,cy,11,'#ffdb8b');ctx.font='12px -apple-system,sans-serif';ctx.fillStyle='#e7c78e';ctx.textAlign='center';ctx.fillText('태양',cx,cy+26);
    if(scene.source){const [sx,sy]=sourcePoint;ctx.shadowBlur=15;ctx.shadowColor='#bd89ee';if(scene.source.kind==='blackhole'){ctx.fillStyle='#05050a';ctx.strokeStyle='#d6b1ff';ctx.lineWidth=2;ctx.beginPath();ctx.arc(sx,sy,10,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.beginPath();ctx.ellipse(sx,sy,17,5,-.45,0,Math.PI*2);ctx.stroke();}else sphere(ctx,sx,sy,12,'#d2eaff');ctx.shadowBlur=0;ctx.fillStyle='#dbc3f4';ctx.fillText(scene.source.name,clamp(sx,40,w-40),clamp(sy-20,35,h-20));}
    const labelBoxes=[[cx-16,cy+13,32,16]];
    if(sourcePoint)labelBoxes.push([sourcePoint[0]-25,sourcePoint[1]-32,50,18]);
    function planetLabel(text,x,y,color){
      const tw=ctx.measureText(text).width;
      const candidates=[[x+12,y-8],[x-tw-12,y-8],[x+10,y+21],[x-tw-10,y+21],[x-tw/2,y-28],[x-tw/2,y+34],[x+26,y-33],[x-tw-26,y+37]].map(([lx,ly])=>[clamp(lx,5,w-tw-5),clamp(ly,34,h-10)]);
      const cost=([lx,ly])=>labelBoxes.reduce((sum,[bx,by,bw,bh])=>sum+(lx<bx+bw+4&&lx+tw>bx-4&&ly-12<by+bh+3&&ly>by-3?1000:0),0)+Math.hypot(lx-x,ly-y)*.1;
      candidates.sort((a,b)=>cost(a)-cost(b));const [lx,ly]=candidates[0];
      labelBoxes.push([lx,ly-12,tw,15]);ctx.strokeStyle='#a3b8ca44';ctx.lineWidth=.6;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(lx+tw/2,ly-5);ctx.stroke();ctx.fillStyle=color;ctx.textAlign='left';ctx.fillText(text,lx,ly);
    }
    [...scene.bodies].sort((a,b)=>Number(b.id==='earth')-Number(a.id==='earth')).forEach(b=>{const [x,y]=project(...pointAt(b,time));if(x<6||x>w-6||y<18||y>h-8)return;const ended=b.status!=='complete'&&time>=b.end_years;ctx.globalAlpha=ended ? .5 : 1;sphere(ctx,x,y,b.size*(w<400?.8:1),b.color,b.id==='saturn');if(b.id==='earth'){ctx.strokeStyle='#7cf2d1';ctx.lineWidth=1;ctx.beginPath();ctx.arc(x,y,10,0,Math.PI*2);ctx.stroke();}ctx.font=`${b.id==='earth'?12:11}px -apple-system,sans-serif`;planetLabel(b.name+(ended?' ×':''),x,y,b.id==='earth'?'#b9f9e7':'#aebbd1');if(ended){ctx.strokeStyle='#f0b66c';ctx.beginPath();ctx.moveTo(x-4,y-4);ctx.lineTo(x+4,y+4);ctx.moveTo(x+4,y-4);ctx.lineTo(x-4,y+4);ctx.stroke();}ctx.globalAlpha=1;});
    ctx.restore();
  }
  function drawEarth(){
    const info=canvasContext('earth-focus-canvas');if(!info)return;
    const {ctx,w,h}=info,f=scene.focus,x=w/2,y=h/2+4,r=31;
    if(f.kind==='magnetic_field'){
      ctx.strokeStyle='#94a9c066';ctx.setLineDash([3,4]);ctx.beginPath();ctx.ellipse(x,y,r+23,r+15,0,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);
      if(f.field>0){const scale=Math.cbrt(f.field);ctx.strokeStyle='#8ee6cf';ctx.lineWidth=1.5;for(const factor of [1,.8]){ctx.beginPath();ctx.ellipse(x,y,(r+23)*scale*factor,(r+15)*scale,0,0,Math.PI*2);ctx.stroke();}}
      for(let j=-1;j<=1;j++)arrow(ctx,3,y+j*20,22,y+j*20,'#edc47f99');
    }else if(f.kind==='atmosphere_loss'&&f.atmosphere>0){ctx.strokeStyle=`rgba(118,194,255,${.2+f.atmosphere*.6})`;ctx.lineWidth=2+f.atmosphere*12;ctx.beginPath();ctx.arc(x,y,r+7+f.atmosphere*4,0,Math.PI*2);ctx.stroke();}
    if(['sirius','solar_luminosity','earth_distance','earth_albedo'].includes(f.kind)){
      for(let j=-1;j<=1;j++){arrow(ctx,2,y+j*16,x-r-5,y+j*16,'#f5c77c',clamp(Math.sqrt(f.flux),.6,4));if(f.kind==='earth_albedo')arrow(ctx,x-r-2,y+j*16,15,y+j*29,'#dceefa',.5+f.albedo*3);}
      if(f.temperature_c>20){ctx.fillStyle=`rgba(245,153,98,${clamp((f.temperature_c-20)/400,0,.35)})`;ctx.beginPath();ctx.arc(x,y,r+13,0,Math.PI*2);ctx.fill();}
    }
    sphere(ctx,x,y,r,'#6fc9d4');
    ctx.save();ctx.beginPath();ctx.arc(x,y,r-1,0,Math.PI*2);ctx.clip();
    const spin=seconds*Math.PI/6*24/f.rotation_hours;
    ctx.fillStyle='#85b88b';for(let i=0;i<4;i++){const lon=spin+i*1.8;const px=x+Math.sin(lon)*r*.7;ctx.globalAlpha=Math.cos(lon)>.05?.85:.15;ctx.beginPath();ctx.ellipse(px,y+(i%3-1)*12,9+Math.cos(lon)*3,10+i%2*6,.4,0,Math.PI*2);ctx.fill();}ctx.globalAlpha=1;
    ctx.strokeStyle='#caebed77';ctx.lineWidth=.7;for(let i=-1;i<=1;i++){ctx.beginPath();ctx.ellipse(x,y+i*r*.45,Math.sqrt(1-(i*.45)**2)*r,4,0,0,Math.PI*2);ctx.stroke();}ctx.beginPath();ctx.ellipse(x,y,Math.abs(Math.cos(spin))*r*.8,r,0,0,Math.PI*2);ctx.stroke();
    const night=ctx.createLinearGradient(x-r,y,x+r,y);night.addColorStop(0,'#07142300');night.addColorStop(.5,'#07142300');night.addColorStop(1,'#071423bb');ctx.fillStyle=night;ctx.fillRect(x-r,y-r,r*2,r*2);ctx.restore();
    if(f.kind==='earth_rotation'){ctx.strokeStyle='#89ddc7';ctx.lineWidth=1.5;ctx.beginPath();ctx.ellipse(x,y,r+15,8,-.15,.2,Math.PI*1.8);ctx.stroke();ctx.fillStyle='#b9eedc';ctx.font='11px -apple-system,sans-serif';ctx.textAlign='center';ctx.fillText(`${fmt(f.rotation_hours,0)}시간에 한 바퀴`,x,h-6);}
    if(f.kind==='earth_mass'){ctx.fillStyle='#ffce85';ctx.fillRect(x-8,y-r-26,16,12);arrow(ctx,x,y-r-15,x,y-r-4,'#ffce85',clamp(f.gravity*1.5,1,4));ctx.font='10px -apple-system,sans-serif';ctx.textAlign='center';ctx.fillText('50 kg',x,y-r-31);}
    if(f.kind==='blackhole')arrow(ctx,x+r+3,y,x+r+28,y,'#d4b4f6',2);
  }
  function draw(){if(!scene||!isScenario()||activeView!=='lab'||scene.focus.kind!==settings.scenario)return;drawSystem();drawEarth();}
  return {receive,draw,tick,reset,seek,setScope,atEnd:()=>scene&&time>=scene.duration_years};
})();

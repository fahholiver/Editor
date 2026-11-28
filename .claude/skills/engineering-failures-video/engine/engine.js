// Engineering Failures engine: dark navy grid, white evidence boxes, handwritten notes with arrows, neon diagrams.
// window.SHOTS use ABSOLUTE times; window.OFF is this chunk's start. Video media is overlaid in post at box rects.
(function(){
const S=STUDIO, root=S.root, seg=(t,a,d,e)=>S.seg(t,a,d,e);
const NS='http://www.w3.org/2000/svg';
const add=(cls,css,html,parent)=>{const d=document.createElement('div');if(cls)d.className=cls;Object.assign(d.style,css||{});if(html!=null)d.innerHTML=html;(parent||root).appendChild(d);return d;};
const sv=(tag,attrs,parent)=>{const e=document.createElementNS(NS,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);parent.appendChild(e);return e;};
const fmt=(n,dec)=>dec? n.toFixed(dec): Math.round(n).toLocaleString('en-US');
const W=1920,H=1080,M=110;
const INK='#EEF1F8', YEL='#FFD23F', RED='#FF4D5E', MUTED='#AEB6CC', NAVY='#0B0D14', LN='#56E1FF';
const GLOWY='0 0 26px rgba(255,210,63,0.5)', GLOWR='0 0 26px rgba(255,77,94,0.5)';
const OFF=window.OFF||0;

// ---------- ground ----------
const ground=document.createElement('canvas'); ground.width=W; ground.height=H; Object.assign(ground.style,{position:'absolute',left:0,top:0}); root.appendChild(ground);
{const g=ground.getContext('2d'); g.fillStyle=NAVY; g.fillRect(0,0,W,H);
 const v=g.createRadialGradient(W*0.32,H*0.42,20,W*0.32,H*0.42,W*0.75); v.addColorStop(0,'#1C2438'); v.addColorStop(1,'rgba(11,13,20,0)'); g.fillStyle=v; g.fillRect(0,0,W,H);
 g.strokeStyle='rgba(255,255,255,0.035)'; g.lineWidth=1; for(let x=0;x<=W;x+=60){g.beginPath();g.moveTo(x+0.5,0);g.lineTo(x+0.5,H);g.stroke();} for(let y=0;y<=H;y+=60){g.beginPath();g.moveTo(0,y+0.5);g.lineTo(W,y+0.5);g.stroke();}
 const r=S.rng(7); for(let i=0;i<1400;i++){g.fillStyle=`rgba(200,220,255,${0.015+r()*0.04})`; g.fillRect(r()*W,r()*H,1.4,1.4);}}
{const fs=document.createElementNS(NS,'svg'); fs.setAttribute('width',0); fs.setAttribute('height',0); fs.style.position='absolute'; root.appendChild(fs);
 fs.innerHTML='<defs><filter id="nglow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter><filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>';}
const stage=add('',{position:'absolute',left:0,top:0,width:W+'px',height:H+'px'});

// ---------- chapter tag + source line (persistent) ----------
const mast=add('',{position:'absolute',left:0,top:0,width:W+'px',height:H+'px',zIndex:50,pointerEvents:'none'});
const tagM=add('mask',{left:'80px',top:'52px',width:'1200px',height:'56px'},null,mast);
const tag=add('abs ant',{fontSize:'36px',lineHeight:'56px',letterSpacing:'0.06em',whiteSpace:'nowrap',color:INK},'',tagM);
const srcM=add('mask',{left:(W-80-1000)+'px',top:'58px',width:'1000px',height:'40px'},null,mast);
const src=add('abs',{fontFamily:'Arial',fontWeight:500,fontSize:'21px',lineHeight:'40px',whiteSpace:'nowrap',width:'1000px',textAlign:'right',color:'#8C94AA'},'',srcM);

// ---------- helpers ----------
function wordLines(parent, lines, o){
  const out=[]; let y=0;
  lines.forEach((ln,li)=>{
    const m=add('mask',{left:'0px',top:y+'px',width:(o.w||1700)+'px',height:o.lh+'px'},null,parent);
    const acc=(o.accent!=null&&(o.accent===li||(Array.isArray(o.accent)&&o.accent.includes(li))));
    const col=acc?(o.acol||YEL):(o.color||INK);
    const ws=String(ln).split(' ').filter(Boolean).map(w=>add('abs '+(o.cls||'ant'),{fontSize:o.fs+'px',lineHeight:o.lh+'px',whiteSpace:'nowrap',color:col,textShadow:acc?((o.acol===RED)?GLOWR:GLOWY):'none'},w,m));
    out.push({m,ws}); y+=o.lh;
  });
  const layout=()=>out.forEach(({m,ws})=>{let x=0; const gap=o.fs*0.26; const tot=ws.reduce((a,s)=>a+s.offsetWidth,0)+gap*(ws.length-1); if(o.align==='center') x=((o.w||1700)-tot)/2; ws.forEach(s=>{s.style.left=x+'px'; x+=s.offsetWidth+gap;});});
  return {out,layout,height:y};
}
function animWords(wl,t,t0,t1,o){
  wl.layout();
  wl.out.forEach(({ws},li)=>ws.forEach((s,k)=>{
    const st=(o&&o.at&&o.at[li]!=null)?o.at[li]+k*0.05:t0+0.12+li*0.2+k*0.05;
    const inn=seg(t,st,0.55,'expo.out'), out=seg(t,t1-0.35+k*0.02,0.3,'power2.in');
    const h=parseFloat(s.style.lineHeight);
    s.style.transform=`translateY(${t<t1-0.35?(1-inn)*h:-out*h}px)`;
  }));
}
const ease={out:(t,t1)=>seg(t,t1-0.35,0.35,'power2.in')};
function svgLayer(L){const s=sv('svg',{width:W,height:H,viewBox:`0 0 ${W} ${H}`},L); Object.assign(s.style,{position:'absolute',left:0,top:0,overflow:'visible',zIndex:5}); return s;}
// hand-drawn arrow: returns updater(p) for draw progress
function arrow(svg,a,b,color,bend){
  const mx=(a[0]+b[0])/2, my=(a[1]+b[1])/2; const dx=b[0]-a[0], dy=b[1]-a[1]; const len=Math.hypot(dx,dy)||1; const k=(bend==null?0.22:bend)*len;
  const cx=mx-dy/len*k, cy=my+dx/len*k;
  const pu=sv('path',{d:`M ${a[0]} ${a[1]} Q ${cx} ${cy} ${b[0]} ${b[1]}`,stroke:'#06070B','stroke-width':13,fill:'none','stroke-linecap':'round'},svg);
  const p=sv('path',{d:`M ${a[0]} ${a[1]} Q ${cx} ${cy} ${b[0]} ${b[1]}`,stroke:color,'stroke-width':6,fill:'none','stroke-linecap':'round'},svg);
  const L=p.getTotalLength(); p.setAttribute('stroke-dasharray',L);
  const tx=b[0]-cx, ty=b[1]-cy, tl=Math.hypot(tx,ty)||1, ux=tx/tl, uy=ty/tl; const hs=30;
  const h1=[b[0]-ux*hs+(-uy)*hs*0.62, b[1]-uy*hs+ux*hs*0.62], h2=[b[0]-ux*hs-(-uy)*hs*0.62, b[1]-uy*hs-ux*hs*0.62];
  const hu=sv('path',{d:`M ${h1[0]} ${h1[1]} L ${b[0]} ${b[1]} L ${h2[0]} ${h2[1]}`,stroke:'#06070B','stroke-width':13,fill:'none','stroke-linecap':'round','stroke-linejoin':'round'},svg);
  const hd=sv('path',{d:`M ${h1[0]} ${h1[1]} L ${b[0]} ${b[1]} L ${h2[0]} ${h2[1]}`,stroke:color,'stroke-width':6,fill:'none','stroke-linecap':'round','stroke-linejoin':'round'},svg);
  const HL=hd.getTotalLength(); hd.setAttribute('stroke-dasharray',HL);
  pu.setAttribute('stroke-dasharray',L); hu.setAttribute('stroke-dasharray',HL);
  return pr=>{const a1=L*(1-Math.min(1,pr/0.8)), a2=HL*(1-Math.max(0,(pr-0.75)/0.25)); p.setAttribute('stroke-dashoffset',a1); pu.setAttribute('stroke-dashoffset',a1); hd.setAttribute('stroke-dashoffset',a2); hu.setAttribute('stroke-dashoffset',a2);};
}
function note(L,n){ // handwritten note with optional arrow
  const col=n.color==='red'?RED:n.color==='yellow'?YEL:INK; const fs=n.size||60;
  const box=add('abs',{left:n.x+'px',top:n.y+'px',width:(n.w||640)+'px',textAlign:n.align||'left',zIndex:6},null,L);
  const tx=add('',{fontFamily:'"EFV Hand","Segoe Print","Comic Sans MS",cursive',fontWeight:700,fontSize:fs+'px',lineHeight:1.0,color:col,textShadow:'0 2px 10px rgba(0,0,0,0.85)'},n.text,box);
  let sub=null; if(n.sub) sub=add('',{fontFamily:'"EFV Hand","Segoe Print","Comic Sans MS",cursive',fontWeight:600,fontSize:(n.subSize||Math.round(fs*0.6))+'px',lineHeight:1.1,color:'#C2C9DB',marginTop:'6px',textShadow:'0 2px 8px rgba(0,0,0,0.85)'},n.sub,box);
  return {box,tx,sub,n};
}
function noteUpdate(o,t,arrowUp){
  const n=o.n; const p=seg(t,n.at,0.7,'power1.inOut');
  o.tx.style.clipPath=`inset(-20% ${(1-p)*100}% -20% 0)`;
  if(o.sub){const q=seg(t,n.at+0.45,0.6,'power1.inOut'); o.sub.style.clipPath=`inset(-20% ${(1-q)*100}% -20% 0)`;}
  if(arrowUp) arrowUp(seg(t,n.at+0.25,0.55,'power2.inOut'));
}

// ---------- shot builders ----------
const B={};

// white evidence boxes + notes
B.box=(sh,L)=>{
  const items=(sh.boxes||[]).map(b=>{
    const pad=b.pad==null?18:b.pad, capH=b.cap?58:pad;
    const outer=add('abs',{left:(b.x-pad)+'px',top:(b.y-pad)+'px',width:(b.w+2*pad)+'px',height:(b.h+pad+capH)+'px',background:'#FBFAF6',boxShadow:'0 28px 70px rgba(0,0,0,0.62), 0 0 0 1px rgba(0,0,0,0.15)',transformOrigin:'50% 50%',zIndex:3},null,L);
    const win=add('mask',{left:pad+'px',top:pad+'px',width:b.w+'px',height:b.h+'px',background:b.vid?'#050608':(b.bg||'#111')},null,outer);
    let im=null; if(b.img) im=add('abs',{width:b.w+'px',height:b.h+'px',backgroundImage:`url("media/${b.img.split('/').map(encodeURIComponent).join('/')}")`,backgroundSize:b.fit||'cover',backgroundRepeat:'no-repeat',backgroundPosition:b.pos||'center',backgroundColor:b.bg||'#111'},null,win);
    let cap=null; if(b.cap) cap=add('abs',{left:(pad+6)+'px',top:(pad+b.h+8)+'px',fontFamily:'"EFV Hand","Segoe Print","Comic Sans MS",cursive',fontWeight:700,fontSize:(b.capSize||34)+'px',lineHeight:'44px',color:'#23252C',whiteSpace:'nowrap'},b.cap,outer);
    return {outer,im,b,cap,win};
  });
  const svg=svgLayer(L);
  const notes=(sh.notes||[]).map(n=>{const o=note(L,n); const au=n.arrow?arrow(svg,n.arrow[0],n.arrow[1],n.color==='red'?RED:n.color==='yellow'?YEL:INK,n.bend):null; return {o,au};});
  let head=null; if(sh.head){const h=sh.head; head=wordLines(add('abs',{left:h.x+'px',top:h.y+'px',zIndex:6},null,L),h.lines,{fs:h.fs||96,lh:Math.round((h.fs||96)*1.12),w:h.w||800,accent:h.accent,acol:h.acol==='red'?RED:YEL,align:h.align});}
  return t=>{L.style.opacity=1-ease.out(t,sh.t1);
    items.forEach(({outer,im,b,win})=>{const at=b.at!=null?b.at:sh.t0; const p=seg(t,at,0.35,'power3.out'); const r=b.rot||0;
      if(b.vid){ const key=t>=(b.keyFrom!=null?b.keyFrom:at+0.12) && t<sh.t1-0.36; win.style.background=key?'#FF00FF':'#050608'; win.style.boxShadow='inset 0 0 0 3px #0A0B0F'; }
      outer.style.opacity=p>0.001?Math.min(1,p*1.6):0;
      outer.style.transform=`translate(${(1-p)*(b.dx||0)}px,${(1-p)*(b.dy==null?-50:b.dy)}px) rotate(${r+(1-p)*(b.vid?0:(r>=0?4:-4))}deg) scale(${b.vid?1:1.04-0.04*p})`;
      if(im){const z=b.push==null?0.06:b.push; const kp=seg(t,at,sh.t1-at+0.3,'sine.inOut'); im.style.transformOrigin=b.origin||'50% 50%'; im.style.transform=`scale(${1+z*kp}) translate(${(b.pan||0)*kp}px,${(b.panY||0)*kp}px)`;}});
    notes.forEach(({o,au})=>noteUpdate(o,t,au));
    if(head) animWords(head,t,sh.head.at||sh.t0+0.3,sh.t1,{at:sh.head.ats});};
};

B.full=(sh,L)=>{L.style.background='#FF00FF'; return t=>{};}; // footage overlaid in post

B.title=(sh,L)=>{
  const wl=wordLines(add('abs',{left:M+'px',top:'300px'},null,L),sh.lines||['Engineering','Failures'],{fs:190,lh:205,w:W-2*M,accent:1,acol:RED});
  const km=add('mask',{left:(M+4)+'px',top:'250px',width:W+'px',height:'44px'},null,L);
  const k=add('abs',{width:W+'px',textAlign:'left',fontFamily:'Arial',fontWeight:600,fontSize:'26px',lineHeight:'44px',letterSpacing:'0.3em',color:MUTED,textTransform:'uppercase'},sh.kicker||'Engineering investigation',km);
  const sm=add('mask',{left:(M+4)+'px',top:'740px',width:W+'px',height:'60px'},null,L);
  const st=add('abs',{width:W+'px',textAlign:'left',fontFamily:'"EFV Hand","Segoe Print","Comic Sans MS",cursive',fontWeight:700,fontSize:'52px',lineHeight:'60px',color:YEL},sh.sub||'',sm);
  return t=>{L.style.opacity=1-ease.out(t,sh.t1); animWords(wl,t,sh.t0,sh.t1,{at:[sh.t0+0.1,sh.t0+0.35]});
    k.style.transform=`translateY(${(1-seg(t,sh.t0,0.5,'expo.out'))*44}px)`; st.style.clipPath=`inset(0 ${(1-seg(t,sh.t0+0.8,0.8,'power1.inOut'))*100}% 0 0)`;
    L.style.transform=`scale(${1+0.025*seg(t,sh.t0,sh.t1-sh.t0,'sine.inOut')})`;};
};

B.section=(sh,L)=>{
  const no=add('mask',{left:M+'px',top:'150px',width:'560px',height:'400px'},null,L);
  const not=add('abs ant',{fontSize:'380px',lineHeight:'400px',color:RED,textShadow:GLOWR},sh.no,no);
  const nm=wordLines(add('abs',{left:M+'px',top:'560px'},null,L),sh.name,{fs:120,lh:132,w:1000});
  const ym=add('mask',{left:(M+4)+'px',top:(560+sh.name.length*132+14)+'px',width:'1000px',height:'60px'},null,L);
  const yt=add('abs',{fontFamily:'"EFV Hand","Segoe Print","Comic Sans MS",cursive',fontWeight:700,fontSize:'50px',lineHeight:'60px',color:YEL,whiteSpace:'nowrap'},sh.sub||'',ym);
  const bx={x:1040,y:250,w:720,h:520};
  const outer=add('abs',{left:(bx.x-18)+'px',top:(bx.y-18)+'px',width:(bx.w+36)+'px',height:(bx.h+36+50)+'px',background:'#FBFAF6',boxShadow:'0 28px 70px rgba(0,0,0,0.6)'},null,L);
  const win=add('mask',{left:'18px',top:'18px',width:bx.w+'px',height:bx.h+'px'},null,outer);
  const im=add('abs',{width:bx.w+'px',height:bx.h+'px',backgroundImage:`url("media/${sh.img.split('/').map(encodeURIComponent).join('/')}")`,backgroundSize:'cover',backgroundPosition:sh.pos||'center'},null,win);
  add('abs',{left:'24px',top:(18+bx.h+6)+'px',fontFamily:'"EFV Hand","Segoe Print","Comic Sans MS",cursive',fontWeight:700,fontSize:'34px',lineHeight:'44px',color:'#23252C'},sh.cap||'',outer);
  return t=>{L.style.opacity=1-ease.out(t,sh.t1);
    not.style.transform=`translateY(${(1-seg(t,sh.t0+0.05,0.7,'expo.out'))*400}px)`;
    animWords(nm,t,sh.t0+0.25,sh.t1); yt.style.clipPath=`inset(-20% ${(1-seg(t,sh.t0+0.7,0.7,'power1.inOut'))*100}% -20% 0)`;
    const p=seg(t,sh.t0+0.15,0.65,'power3.out'); outer.style.opacity=Math.min(1,p*1.6); outer.style.transform=`translate(${(1-p)*120}px,${(1-p)*-30}px) rotate(${2+(1-p)*5}deg)`;
    im.style.transform=`scale(${1.02+0.06*seg(t,sh.t0,sh.t1-sh.t0,'sine.inOut')})`;};
};

B.head=(sh,L)=>{
  const fs=sh.fs||118, lh=Math.round(fs*1.12);
  const tot=sh.lines.length*lh; const y=sh.y!=null?sh.y:Math.round(150+(760-tot)/2);
  const wl=wordLines(add('abs',{left:(sh.x||M)+'px',top:y+'px'},null,L),sh.lines,{fs,lh,w:sh.w||(W-2*M),accent:sh.accent,acol:sh.acol==='red'?RED:YEL,align:sh.align});
  let sub=null; if(sh.sub){const sm=add('mask',{left:(sh.x||M)+'px',top:(y+tot+18)+'px',width:(sh.w||(W-2*M))+'px',height:'70px'},null,L); sub=add('abs',{fontFamily:'"EFV Hand","Segoe Print","Comic Sans MS",cursive',fontWeight:700,fontSize:'56px',lineHeight:'70px',color:MUTED,width:'100%',textAlign:sh.align==='center'?'center':'left',whiteSpace:'nowrap'},sh.sub,sm);}
  return t=>{L.style.opacity=1-ease.out(t,sh.t1); animWords(wl,t,sh.t0,sh.t1,{at:sh.at});
    if(sub) sub.style.clipPath=`inset(-20% ${(1-seg(t,(sh.subAt||sh.t0+0.6),0.7,'power1.inOut'))*100}% -20% 0)`;
    L.style.transform=`scale(${1+0.02*seg(t,sh.t0,sh.t1-sh.t0,'sine.inOut')})`; L.style.transformOrigin='30% 50%';};
};

B.doc=(sh,L)=>{
  const x=sh.x||260, y=sh.y||220, w=sh.w||1400;
  const card=add('abs',{left:x+'px',top:y+'px',width:w+'px',background:'#FBFAF6',boxShadow:'0 28px 70px rgba(0,0,0,0.6)',padding:'40px 56px 46px'},null,L);
  add('',{fontFamily:'"Courier New",monospace',fontSize:'22px',color:'#6B5E55',letterSpacing:'0.04em',paddingBottom:'14px',borderBottom:'2px solid #1A1A1A',marginBottom:'24px'},sh.header,card);
  const body=add('',{fontFamily:'"Courier New",monospace',fontSize:(sh.fs||40)*1.25+'px',lineHeight:1.6,color:'#1A1A1A',position:'relative'},sh.body.replace(/\[\[(.+?)\]\]/,'<span class="hl" style="background-image:linear-gradient(rgba(255,210,63,0.75),rgba(255,210,63,0.75));background-repeat:no-repeat;background-position:0 70%;background-size:0% 62%">$1</span>'),card);
  const hl=body.querySelector('.hl');
  const svg=svgLayer(L);
  const notes=(sh.notes||[]).map(n=>({o:note(L,n),au:n.arrow?arrow(svg,n.arrow[0],n.arrow[1],n.color==='red'?RED:n.color==='yellow'?YEL:INK,n.bend):null}));
  return t=>{L.style.opacity=1-ease.out(t,sh.t1);
    const di=seg(t,sh.t0,0.65,'power3.out'); card.style.opacity=Math.min(1,di*1.5); card.style.transform=`translateY(${(1-di)*-50}px) rotate(${(sh.rot||-1)+(1-di)*-3}deg) scale(${1+0.025*seg(t,sh.t0+0.5,sh.t1-sh.t0,'sine.inOut')})`;
    if(hl){const hp=seg(t,sh.hlAt||sh.t0+1,1.2,'power2.inOut'); hl.style.backgroundSize=(hp*100)+'% 62%';}
    notes.forEach(({o,au})=>noteUpdate(o,t,au));};
};

B.counter=(sh,L)=>{
  const x=sh.x||M, fs=sh.fs||300;
  const moreM=add('mask',{left:x+'px',top:'190px',width:'1600px',height:'70px'},null,L);
  const more=add('abs',{fontFamily:'"EFV Hand","Segoe Print","Comic Sans MS",cursive',fontWeight:700,fontSize:'58px',lineHeight:'70px',color:MUTED,whiteSpace:'nowrap'},sh.more||'',moreM);
  const bigM=add('mask',{left:x+'px',top:'262px',width:'1700px',height:fs*1.12+'px'},null,L);
  const big=add('abs ant',{fontSize:fs+'px',lineHeight:fs*1.12+'px',whiteSpace:'nowrap'},'0',bigM);
  const yR=262+fs*1.12+10;
  const rule=add('abs',{left:x+'px',top:yR+'px',height:'8px',background:INK},null,L);
  const labM=add('mask',{left:x+'px',top:(yR+22)+'px',width:'1700px',height:'76px'},null,L);
  const labs=sh.steps.map(s=>add('abs',{fontFamily:'"EFV Hand","Segoe Print","Comic Sans MS",cursive',fontWeight:700,fontSize:'64px',lineHeight:'76px',color:s.accent?RED:INK,whiteSpace:'nowrap'},s.label,labM));
  return t=>{L.style.opacity=1-ease.out(t,sh.t1);
    more.style.clipPath=`inset(-20% ${(1-seg(t,sh.t0,0.6,'power1.inOut'))*100}% -20% 0)`;
    big.style.transform=`translateY(${(1-seg(t,sh.t0+0.05,0.6,'expo.out'))*fs*1.12}px)`;
    let val=sh.from||0, acc=false;
    sh.steps.forEach((s,i)=>{const p=seg(t,s.at,s.dur||1.3,'power2.out'); const prev=i?sh.steps[i-1].value:(sh.from||0); if(t>=s.at){val=prev+(s.value-prev)*p; acc=!!s.accent;}});
    big.textContent=(sh.prefix||'')+fmt(val,sh.dec)+(sh.suffix||''); big.style.color=acc?RED:INK; big.style.textShadow=acc?'0 0 40px rgba(255,77,94,0.55)':'none'; rule.style.background=acc?RED:INK;
    rule.style.width=(big.offsetWidth*seg(t,sh.steps[0].at,1.0,'power2.out'))+'px';
    labs.forEach((l,i)=>{const s=sh.steps[i]; const inn=seg(t,s.at+0.3,0.5,'power1.inOut'); const nx=sh.steps[i+1]; const out=nx&&t>=nx.at-0.1; l.style.clipPath=`inset(-20% ${(1-inn)*100}% -20% 0)`; l.style.opacity=out?0:1;});
    bigM.style.transform=`scale(${1+0.02*seg(t,sh.t0,sh.t1-sh.t0,'sine.inOut')})`; bigM.style.transformOrigin='0 50%';};
};

B.list=(sh,L)=>{
  const fs=sh.fs||104, lh=Math.round(fs*1.12); const y0=sh.y||Math.round(160+(760-sh.items.length*lh)/2);
  const els=sh.items.map((it,i)=>{const m=add('mask',{left:(sh.x||M)+'px',top:(y0+i*lh)+'px',width:'1700px',height:lh+'px'},null,L); return {el:add('abs ant',{fontSize:fs+'px',lineHeight:lh+'px',whiteSpace:'nowrap',color:it.accent?YEL:INK},it.text,m),at:it.at};});
  return t=>{L.style.opacity=1-ease.out(t,sh.t1); els.forEach(e=>e.el.style.transform=`translateY(${(1-seg(t,e.at,0.5,'expo.out'))*lh}px)`);};
};

B.saiddid=(sh,L)=>{
  const half=(W-2*M-80)/2;
  const mk=(x,text,col)=>{const m=add('mask',{left:x+'px',top:'210px',width:half+'px',height:'76px'},null,L); return add('abs',{fontFamily:'"EFV Hand","Segoe Print","Comic Sans MS",cursive',fontWeight:700,fontSize:'66px',lineHeight:'76px',color:col,whiteSpace:'nowrap'},text,m);};
  const lkt=mk(M,sh.lk,MUTED), rkt=mk(M+half+80,sh.rk,MUTED);
  const div=add('abs',{left:(M+half+38)+'px',top:'210px',width:'4px',background:INK},null,L);
  const said=wordLines(add('abs',{left:M+'px',top:'310px'},null,L),sh.said,{fs:sh.sfs||120,lh:Math.round((sh.sfs||120)*1.12),w:half,color:INK});
  const did=wordLines(add('abs',{left:(M+half+80)+'px',top:'310px'},null,L),sh.did,{fs:sh.dfs||120,lh:Math.round((sh.dfs||120)*1.12),w:half,color:RED});
  return t=>{L.style.opacity=1-ease.out(t,sh.t1);
    lkt.style.clipPath=`inset(-20% ${(1-seg(t,sh.t0,0.6,'power1.inOut'))*100}% -20% 0)`; div.style.height=(600*seg(t,sh.t0+0.1,0.8,'power2.inOut'))+'px';
    animWords(said,t,sh.t0+0.2,sh.t1,{at:sh.saidAt});
    rkt.style.clipPath=`inset(-20% ${(1-seg(t,sh.didAt-0.2,0.6,'power1.inOut'))*100}% -20% 0)`;
    animWords(did,t,sh.didAt,sh.t1,{at:[sh.didAt,sh.didAt+0.25,sh.didAt+0.5]});};
};

B.timeline=(sh,L)=>{
  const X0=M+40,X1=W-M-40,Y=600; const n=sh.events.length;
  const IN=260; const xs=sh.events.map((e,i)=>X0+IN+(X1-X0-2*IN)*(n===1?0.5:i/(n-1)));
  const base=add('abs',{left:X0+'px',top:Y+'px',height:'4px',background:INK},null,L);
  const gap=sh.gap?add('abs',{top:(Y-6)+'px',height:'16px',background:RED,boxShadow:GLOWR},null,L):null;
  const ev=sh.events.map((e,i)=>{const tk=add('abs',{left:(xs[i]-2)+'px',top:(Y-26)+'px',width:'4px',height:'56px',background:e.accent?RED:INK},null,L);
    const dm=add('mask',{left:(xs[i]-260)+'px',top:(Y-180)+'px',width:'520px',height:'140px'},null,L);
    const d=add('abs ant',{width:'520px',textAlign:'center',fontSize:'110px',lineHeight:'140px',color:e.accent?RED:INK},e.date,dm);
    const lm=add('mask',{left:(xs[i]-260)+'px',top:(Y+50)+'px',width:'520px',height:'140px'},null,L);
    const l=add('abs',{width:'520px',textAlign:'center',fontFamily:'"EFV Hand","Segoe Print","Comic Sans MS",cursive',fontWeight:700,fontSize:'52px',lineHeight:'60px',color:INK},e.label,lm); return {tk,d,l,e};});
  let gl=null; if(sh.gap){const gm=add('mask',{top:(Y+200)+'px',width:'900px',height:'80px'},null,L); gl={m:gm,el:add('abs',{fontFamily:'"EFV Hand","Segoe Print","Comic Sans MS",cursive',fontWeight:700,fontSize:'66px',lineHeight:'80px',color:RED,whiteSpace:'nowrap',width:'900px',textAlign:'center'},sh.gap.label,gm)};}
  return t=>{L.style.opacity=1-ease.out(t,sh.t1);
    base.style.width=((X1-X0)*seg(t,sh.t0,0.8,'expo.out'))+'px';
    ev.forEach(o=>{const p=seg(t,o.e.at,0.5,'expo.out'); o.tk.style.transform=`scaleY(${p})`; o.d.style.transform=`translateY(${(1-p)*140}px)`; o.l.style.clipPath=`inset(-20% ${(1-seg(t,o.e.at+0.2,0.6,'power1.inOut'))*100}% -20% 0)`;});
    if(gap){const a=xs[sh.gap.from],b=xs[sh.gap.to]; const p=seg(t,sh.gap.at,0.9,'power2.inOut'); gap.style.left=a+'px'; gap.style.width=((b-a)*p)+'px';
      gl.m.style.left=((a+b)/2-450)+'px'; gl.el.style.clipPath=`inset(-20% ${(1-seg(t,sh.gap.at+0.4,0.6,'power1.inOut'))*100}% -20% 0)`;}};
};

B.bars=(sh,L)=>{ // two bars: cost vs payout
  const base=860, maxH=520, x0=560;
  const svg=svgLayer(L);
  const items=sh.bars.map((b,i)=>{const x=x0+i*520; const bar=add('abs',{left:x+'px',width:'300px',background:b.color==='red'?RED:INK,boxShadow:b.color==='red'?GLOWR:'none'},null,L);
    const vm=add('mask',{left:(x-110)+'px',width:'520px',height:'130px'},null,L); const v=add('abs ant',{width:'520px',textAlign:'center',fontSize:'110px',lineHeight:'130px',color:b.color==='red'?RED:INK},b.value,vm);
    const lm=add('mask',{left:(x-110)+'px',top:(base+14)+'px',width:'520px',height:'60px'},null,L); const l=add('abs',{width:'520px',textAlign:'center',fontFamily:'"EFV Hand","Segoe Print","Comic Sans MS",cursive',fontWeight:700,fontSize:'52px',lineHeight:'60px',color:MUTED},b.label,lm);
    return {bar,vm,v,l,b,x};});
  const top=wordLines(add('abs',{left:M+'px',top:'150px'},null,L),sh.lines||[],{fs:84,lh:94,w:W-2*M});
  const notes=(sh.notes||[]).map(n=>({o:note(L,n),au:n.arrow?arrow(svg,n.arrow[0],n.arrow[1],n.color==='red'?RED:n.color==='yellow'?YEL:INK,n.bend):null}));
  return t=>{L.style.opacity=1-ease.out(t,sh.t1); animWords(top,t,sh.t0,sh.t1,{at:sh.at});
    items.forEach(({bar,vm,v,l,b})=>{const p=seg(t,b.at,1.0,'power3.out'); const h=maxH*b.h*p; bar.style.top=(base-h)+'px'; bar.style.height=h+'px'; vm.style.top=(base-h-140)+'px'; v.style.opacity=p>0.05?1:0; l.style.clipPath=`inset(-20% ${(1-seg(t,b.at+0.2,0.6,'power1.inOut'))*100}% -20% 0)`;});
    notes.forEach(({o,au})=>noteUpdate(o,t,au));};
};

// ---------- neon diagrams ----------
B.blueprint=(sh,L)=>{
  const svg=sv('svg',{width:W,height:H,viewBox:`0 0 ${W} ${H}`},L); Object.assign(svg.style,{position:'absolute',left:0,top:0});
  const g=sv('g',{filter:'url(#nglow)'},svg);
  const strokes=[]; const D=(e,at,dur)=>{const len=e.getTotalLength?Math.ceil(e.getTotalLength())+2:2000; e.setAttribute('stroke-dasharray',len); strokes.push({e,len,at,dur:dur||0.9}); return e;};
  const P=(d,col,w,at,dur,extra)=>D(sv('path',Object.assign({d,fill:'none',stroke:col||LN,'stroke-width':w||4,'stroke-linecap':'round','stroke-linejoin':'round'},extra||{}),g),at,dur);
  const labs=[]; const lab=(x,y,text,at,col,o)=>{o=o||{}; const el=add('abs',{left:x+'px',top:y+'px',fontFamily:o.mono?'"Courier New",monospace':'"EFV Hand","Segoe Print","Comic Sans MS",cursive',fontWeight:700,fontSize:(o.fs||(o.mono?30:56))+'px',lineHeight:1.05,color:col||INK,whiteSpace:'nowrap',textShadow:'0 0 14px rgba(0,0,0,0.9)',textAlign:o.align||'left',transform:o.align==='center'?'translateX(-50%)':'none'},text,L); labs.push({el,at}); return el;};
  const dyn=[]; const t0=sh.t0, k=sh.kind, Y=YEL, R=RED;
  const title=lab(80,150,sh.title||'',t0+0.15,MUTED,{fs:46});
  if(k==='chain'){
    const nodes=sh.nodes;
    const first=nodes.length===2?625:410, step=nodes.length===2?670:550;
    nodes.forEach((node,i)=>{
      const x=first+i*step, at=node.at, c=node.accent?R:LN;
      P(`M ${x-225} 400 H ${x+225} V 635 H ${x-225} Z`,c,5,at,0.5);
      lab(x,425,String(i+1).padStart(2,'0'),at,c,{fs:34,align:'center',mono:true});
      lab(x,500,node.label,at+0.18,INK,{fs:44,align:'center',mono:true});
      if(node.detail) lab(x,564,node.detail,at+0.36,MUTED,{fs:35,align:'center'});
      if(i>0){
        const left=x-step+228, right=x-231;
        P(`M ${left} 520 H ${right} M ${right-18} 508 L ${right} 520 L ${right-18} 532`,Y,5,at-0.25,0.3);
      }
    });
  }
  if(k==='structure'){
    const items=sh.paths||[];
    items.forEach(item=>P(item.d,item.color==='red'?R:item.color==='yellow'?Y:LN,item.width||5,item.at,item.dur||0.7));
    (sh.labels||[]).forEach(item=>lab(item.x,item.y,item.text,item.at,item.color==='red'?R:item.color==='yellow'?Y:INK,{fs:item.size||44,align:item.align||'left'}));
  }
  return t=>{const i=seg(t,t0,0.35,'power2.out'), o=ease.out(t,sh.t1); L.style.opacity=i*(1-o);
    strokes.forEach(s=>s.e.setAttribute('stroke-dashoffset',s.len*(1-seg(t,s.at,s.dur,'power1.inOut'))));
    dyn.forEach(f=>f(t)); labs.forEach(l=>{const p=seg(t,l.at,0.6,'power1.inOut'); l.el.style.clipPath=`inset(-30% ${(1-p)*100}% -30% -5%)`;});};
};

// ---------- build ----------
const shots=(window.SHOTS||[]).map((sh,i)=>{const L=add('',{position:'absolute',left:0,top:0,width:W+'px',height:H+'px',zIndex:10+i,display:'none'},null,stage); const up=B[sh.type](sh,L); return {sh,L,up};});
const CH=window.CHAP||{};
window.__timelines["main"]=S.play(function(tl){
  const t=tl+OFF;
  shots.forEach(({sh,L,up})=>{const on=t>=sh.t0-0.02 && t<=sh.t1+0.02; L.style.display=on?'block':'none'; if(on) up(t);});
  const hide=(CH.hideTag||[]).some(([a,b])=>t>=a&&t<b);
  mast.style.opacity=hide?0:1;
  let tg=''; (CH.tags||[]).forEach(k=>{if(t>=k.at) tg=k.html;}); if(tag.innerHTML!==tg) tag.innerHTML=tg;
  let sline=''; let sAt=0; shots.forEach(({sh})=>{if(t>=sh.t0&&t<=sh.t1&&sh.src){sline=sh.src; sAt=sh.t0;}});
  src.textContent=sline? 'Source: '+sline : ''; src.style.transform=`translateY(${(1-seg(t,sAt+0.4,0.4,'expo.out'))*40}px)`;
},{loop:false});
})();

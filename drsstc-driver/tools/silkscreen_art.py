import re,math,random,uuid,shutil,collections
F='drsstc-driver.kicad_pcb'
t=open(F).read()
shutil.copy(F,F+'.pre-art5.bak')
# remove earlier artwork (uuid prefix a57a57)
def strip(t):
    out=[];i=0
    for m in re.finditer(r'\n\t\((gr_line|gr_circle|gr_text|gr_poly)\b',t):
        pass
    parts=re.split(r'(?=\n\t\((?:gr_line|gr_circle|gr_text|gr_poly|gr_arc|gr_rect|zone|footprint|segment|via|embedded_fonts|group|net|setup|layers|general|paper|title_block)\b)',t)
    return ''.join(p for p in parts if not (re.match(r'\n\t\(gr_(line|circle|text|poly)',p) and '(uuid "a57a57' in p))
t=strip(t)
# black mask / white silk / gold finish in the stackup (render + fab notes)
t=re.sub(r'\(type "(Top|Bottom) Solder Mask"\)\s*(?:\(color "[^"]*"\)\s*)?',lambda m:f'(type "{m.group(1)} Solder Mask")\n\t\t\t\t(color "Black")\n\t\t\t\t',t)
t=re.sub(r'\(type "(Top|Bottom) Silk Screen"\)\s*(?:\(color "[^"]*"\)\s*)?',lambda m:f'(type "{m.group(1)} Silk Screen")\n\t\t\t\t(color "White")\n\t\t\t',t)
if 'copper_finish' in t: t=re.sub(r'\(copper_finish "[^"]*"\)','(copper_finish "ENIG")',t)
# through-hole pads, grouped by ref
tht=[];byref=collections.defaultdict(list)
for blk in t.split('\n\t(footprint ')[1:]:
    m=re.search(r'\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)',blk); ref=re.search(r'\(property "Reference" "([^"]+)"',blk).group(1)
    fx,fy=float(m.group(1)),float(m.group(2)); r=math.radians(float(m.group(3) or 0))
    for pm in re.finditer(r'\(pad "[^"]*" (thru_hole|np_thru_hole) \w+\s*\(at ([-\d.]+) ([-\d.]+)(?: [-\d.]+)?\)\s*\(size ([\d.]+) ([\d.]+)\)',blk):
        px,py=float(pm.group(2)),float(pm.group(3))
        X=fx+px*math.cos(r)+py*math.sin(r); Y=fy-px*math.sin(r)+py*math.cos(r)
        tht.append((X,Y,max(float(pm.group(4)),float(pm.group(5)))/2+0.45)); byref[ref].append((X,Y))
boxes=[]; out=[]
def U(): return 'a57a57'+uuid.uuid4().hex[6:8]+'-'+str(uuid.uuid4())[9:]
def ok(x,y,pad=0.0,usebox=True):
    if not (100.8<x<189.2 and 100.8<y<164.2): return False
    if usebox:
        for (a,b,c,d) in boxes:
            if a-pad<x<c+pad and b-pad<y<d+pad: return False
    for (px,py,pr) in tht:
        if (x-px)**2+(y-py)**2<(pr+pad)**2: return False
    return True
drawn=collections.defaultdict(list)   # coarse hash of drawn line points (for dot knock-out)
def mark(x,y): drawn[(int(x),int(y))].append((x,y))
def near_drawn(x,y,d):
    for i in (-1,0,1):
        for j in (-1,0,1):
            for (a,b) in drawn.get((int(x)+i,int(y)+j),()):
                if (a-x)**2+(b-y)**2<d*d: return True
    return False
def line(a,b,w,clip=True,usebox=True,track=True):
    w=max(w,0.15)
    L=math.hypot(b[0]-a[0],b[1]-a[1]); n=max(1,int(L/0.35))
    pts=[(a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n) for i in range(n+1)]
    segs=[];cur=[]
    for p in pts:
        if (not clip) or ok(p[0],p[1],w/2+0.15,usebox): cur.append(p)
        else:
            if len(cur)>1: segs.append((cur[0],cur[-1]))
            cur=[]
    if len(cur)>1: segs.append((cur[0],cur[-1]))
    for s,e in segs:
        if track:
            m=max(1,int(math.hypot(e[0]-s[0],e[1]-s[1])/0.4))
            for i in range(m+1): mark(s[0]+(e[0]-s[0])*i/m,s[1]+(e[1]-s[1])*i/m)
        out.append(f'\t(gr_line\n\t\t(start {s[0]:.4f} {s[1]:.4f})\n\t\t(end {e[0]:.4f} {e[1]:.4f})\n\t\t(stroke\n\t\t\t(width {w})\n\t\t\t(type solid)\n\t\t)\n\t\t(layer "B.SilkS")\n\t\t(uuid "{U()}")\n\t)\n')
def poly(pts,w,closed=False,**k):
    P=pts+[pts[0]] if closed else pts
    for i in range(len(P)-1): line(P[i],P[i+1],w,**k)
def ellipse(cx,cy,rx,ry,w,a0=0,a1=360,n=90,**k):
    poly([(cx+rx*math.cos(math.radians(a0+(a1-a0)*i/n)),cy+ry*math.sin(math.radians(a0+(a1-a0)*i/n))) for i in range(n+1)],w,**k)
def dot(x,y,r,check=True):
    if (not check) or ok(x,y,r+0.2): out.append(f'\t(gr_circle\n\t\t(center {x:.4f} {y:.4f})\n\t\t(end {x+r:.4f} {y:.4f})\n\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill yes)\n\t\t(layer "B.SilkS")\n\t\t(uuid "{U()}")\n\t)\n')
def fpoly(pts):
    if all(ok(x,y,0.2,False) for x,y in pts):
        s=' '.join(f'(xy {x:.4f} {y:.4f})' for x,y in pts)
        out.append(f'\t(gr_poly\n\t\t(pts {s})\n\t\t(stroke\n\t\t\t(width 0.1)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill yes)\n\t\t(layer "B.SilkS")\n\t\t(uuid "{U()}")\n\t)\n')
texts=[]
def text(s,x,y,size,th=None,box=True,ko=False,front=False):
    th=max(0.15,th or round(size*0.15,3)); w=len(s)*size*0.98+0.8+(1.4 if ko else 0); h=size*1.5+0.5+(0.9 if ko else 0)
    if front:
        texts.append(f'\t(gr_text "{s}"\n\t\t(at {x:.3f} {y:.3f} 0)\n\t\t(layer "F.SilkS"{" knockout" if ko else ""})\n\t\t(uuid "{U()}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t\t(thickness {th})\n\t\t\t)\n\t\t)\n\t)\n')
        return
    bad=[(px,py) for (px,py,pr) in tht if x-w/2-pr<px<x+w/2+pr and y-h/2-pr<py<y+h/2+pr]
    if bad: print('TEXT HITS PAD:',s,(x,y),bad[:3])
    if box: boxes.append((x-w/2,y-h/2,x+w/2,y+h/2))
    texts.append(f'\t(gr_text "{s}"\n\t\t(at {x:.3f} {y:.3f} 0)\n\t\t(layer "B.SilkS"{" knockout" if ko else ""})\n\t\t(uuid "{U()}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t\t(thickness {th})\n\t\t\t)\n\t\t\t(justify mirror)\n\t\t)\n\t)\n')
# ---------------- text first (defines knock-out boxes)
text("THUNDER",120,129.0,3.2,0.55); text("CHORD",120,133.55,3.2,0.55,ko=True); text("DRSSTC MUSICAL COIL DRIVER",120,137.5,1.0)
text("CLAYNICHOLSON.COM",134.2,161.5,1.3,0.2,ko=True)
text("THUNDER",105.3,109.3,1.15,0.18,front=True); text("CHORD",105.3,111.4,1.15,0.18,ko=True,front=True); text("CLAYNICHOLSON.COM",116.5,152.0,1.0,0.15,ko=True,front=True)
# connector legends, placed inward from each part's through-hole pads
names={'J3':'24V ALT','J10':'24V DC','J7':'E-STOP','J8':'NTC','J9':'FAN','J4':'GDT','J5':'FB CT','J6':'OCD CT','J1':'MIDI','J2':'USB','FC1':'FIBRE','R1':'PHASE','R2':'OCD','U2':'DRV A','U3':'DRV B'}
for ref,nm in names.items():
    P=byref.get(ref)
    if not P: print('no tht for',ref); continue
    xs=[p[0] for p in P]; ys=[p[1] for p in P]; cx=sum(xs)/len(xs); cy=sum(ys)/len(ys); s=1.0; w=len(nm)*s*0.98
    if ref in('R1','R2'): x,y=cx,min(ys)-2.3
    elif ref=='J2': x,y=186.0,125.0
    elif ref=='J10': x,y=cx,max(ys)+3.4
    elif ref=='FC1': x,y=cx,min(ys)-2.4
    elif cy<112: x,y=cx,max(ys)+2.6
    elif cy>154: x,y=cx,min(ys)-2.6
    elif cx>176: x,y=min(xs)-w/2-2.0,cy
    else: x,y=max(xs)+w/2+2.0,cy
    text(nm,x,y,s)

# ---------------- sparks: one discharge point, bolts to every edge, plus loose arcs
rng=random.Random(1899)
bpts=collections.defaultdict(list)          # bolt points, hashed on a 1 mm grid, for the glow
def bmark(a,b):
    n=max(1,int(math.hypot(b[0]-a[0],b[1]-a[1])/0.3))
    for i in range(n+1):
        x=a[0]+(b[0]-a[0])*i/n; y=a[1]+(b[1]-a[1])*i/n; bpts[(int(x),int(y))].append((x,y))
def bolt(a,b,disp,w,depth=0):
    pts=[a,b]
    for _ in range(6):
        new=[pts[0]]
        for i in range(len(pts)-1):
            p,q=pts[i],pts[i+1]; mx,my=(p[0]+q[0])/2,(p[1]+q[1])/2
            L=math.hypot(q[0]-p[0],q[1]-p[1]) or 1; nx,ny=-(q[1]-p[1])/L,(q[0]-p[0])/L
            d=rng.gauss(0,1)*disp*L*0.17
            new+=[(mx+nx*d,my+ny*d),q]
        pts=new
    n=len(pts)
    for i in range(n-1):
        ww=max(0.15,round(w*(1-0.6*i/n),2)); line(pts[i],pts[i+1],ww); bmark(pts[i],pts[i+1])
    if depth<3:
        for k in range(4 if depth==0 else (2 if depth==1 else 1)):
            i=rng.randrange(n//8,7*n//8); p=pts[i]
            ang=math.atan2(b[1]-a[1],b[0]-a[0])+rng.choice([-1,1])*rng.uniform(0.35,1.0)
            L=math.hypot(b[0]-a[0],b[1]-a[1])*rng.uniform(0.25,0.55)
            bolt(p,(p[0]+L*math.cos(ang),p[1]+L*math.sin(ang)),disp,max(0.15,w*0.62),depth+1)
O=(147.0,131.0)
ends=[(101.5,101.5),(118,101),(136,101),(154,101),(172,101),(188.5,101.5),(189,117),(189,133),(189,149),(188.5,163.5),
      (171,164),(153,164),(135,164),(117,164),(101.5,163.5),(101,148),(101,116)]
for e in ends: bolt(O,e,1.0,0.45)
for a,b in [((104,122),(128,104)),((166,160),(187,140)),((106,160),(126,143)),((160,104),(186,124))]:   # loose arcs
    bolt(a,b,1.1,0.3,1)
# ---------------- title flourishes
for sx,fl in ((108.6,1),(131.4,-1)):
    fpoly([(sx+fl*0.6,131.5),(sx-fl*0.85,133.9),(sx-fl*0.05,133.9),(sx-fl*0.65,135.9),(sx+fl*0.9,133.3),(sx+fl*0.1,133.3)])
line((107.5,139.0),(132.5,139.0),0.25,usebox=False,track=False)
# ---------------- halftone over the whole board: dots swell near a spark, shrink away from it
def dist_bolt(x,y,R=7):
    best=R*R
    cx_,cy_=int(x),int(y)
    for i in range(-R,R+1):
        for j in range(-R,R+1):
            for (a,b) in bpts.get((cx_+i,cy_+j),()):
                d=(a-x)**2+(b-y)**2
                if d<best: best=d
    return math.sqrt(best)
nd=0; pitch=1.25; j=0; yy=101.2
while yy<164.0:
    xx=101.2+(pitch/2 if j%2 else 0)
    while xx<189.0:
        d=dist_bolt(xx,yy)
        r=0.14+0.38*math.exp(-((max(d-0.9,0))/2.6))
        r=min(r,0.5)
        if d>r+0.42 and ok(xx,yy,r+0.25):
            dot(xx,yy,round(r,3),check=False); nd+=1
        xx+=pitch
    yy+=pitch*0.866; j+=1
dot(O[0],O[1],1.1,check=False)
art=''.join(out)+''.join(texts)
i=t.rindex('\t(embedded_fonts')
open(F,'w').write(t[:i]+art+t[i:])
print(len(out),'graphics,',len(texts),'texts,',nd,'halftone dots')

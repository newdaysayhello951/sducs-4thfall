"""Generate report figures using Pillow (bundled; no matplotlib dependency)."""
import json, math, os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pandas as pd

ROOT = Path(r"C:\Users\86134\Desktop\大四上\社交网络实验五\__社交媒体摘要生成(Twitter&weibo)\社交舆论论文复现\sumblr_repro")
OUT = ROOT / "report_assets"
OUT.mkdir(exist_ok=True)
W, H = 1200, 650
FONT = r"C:\Windows\Fonts\msyh.ttc"
try:
    font = ImageFont.truetype(FONT, 22); small = ImageFont.truetype(FONT, 16); title = ImageFont.truetype(FONT, 28)
except Exception:
    font = small = title = ImageFont.load_default()


def base(title_text, xlabel="", ylabel=""):
    im = Image.new("RGB", (W,H), "white"); d=ImageDraw.Draw(im)
    d.text((W//2,20), title_text, fill="#16324f", anchor="ma", font=title)
    d.line((100,80,100,570), fill="#334155", width=2); d.line((100,570,1130,570), fill="#334155", width=2)
    d.text((610,605), xlabel, fill="#334155", anchor="ma", font=font)
    d.text((28,325), ylabel, fill="#334155", anchor="mm", font=font)
    return im,d

def save(im,name): im.save(OUT/name)
def scale(v,a,b,lo,hi): return lo+(v-a)/(b-a if b!=a else 1)*(hi-lo)
def line_chart(title_text, xs, series, xlabel, ylabel, name, logy=False):
    im,d=base(title_text,xlabel,ylabel); x0,x1=100,1130; y0,y1=570,90
    xmin,xmax=min(xs),max(xs)
    vals=[v for _,ys,c in series for v in ys if v is not None]
    if logy: vals=[max(v,1e-3) for v in vals]; lo,hi=math.log10(min(vals)),math.log10(max(vals))
    else: lo,hi=min(vals),max(vals)
    if hi==lo: hi=lo+1
    for t in range(6):
        vv=lo+(hi-lo)*t/5; label=(10**vv if logy else vv)
        y=scale(vv,lo,hi,y0,y1); d.line((x0,y,x1,y),fill="#e2e8f0",width=1); d.text((x0-10,y),f"{label:.2g}",fill="#475569",anchor="ra",font=small)
    for i,x in enumerate(xs):
        px=scale(x,xmin,xmax,x0,x1); d.text((px,y1-2),str(x),fill="#475569",anchor="ma",font=small)
    for label,ys,color in series:
        pts=[]
        for x,v in zip(xs,ys):
            z=math.log10(max(v,1e-3)) if logy else v; pts.append((scale(x,xmin,xmax,x0,x1),scale(z,lo,hi,y0,y1)))
        d.line(pts,fill=color,width=4)
        for p in pts: d.ellipse((p[0]-5,p[1]-5,p[0]+5,p[1]+5),fill=color)
    lx=760
    for label,ys,color in series:
        d.line((lx,50,lx+32,50),fill=color,width=4); d.text((lx+42,50),label,fill="#334155",anchor="lm",font=small); lx+=150
    save(im,name)

def bar_chart(title_text, labels, vals, xlabel, ylabel, name):
    im,d=base(title_text,xlabel,ylabel); x0,x1=110,1130; y0,y1=570,100; vmax=max(vals)*1.15
    bw=(x1-x0)/len(vals)*.65
    for i,(lab,v) in enumerate(zip(labels,vals)):
        x=x0+(i+.5)*(x1-x0)/len(vals); top=scale(v,0,vmax,y0,y1)
        d.rectangle((x-bw/2,top,x+bw/2,y0),fill="#2f6f9f")
        d.text((x,top-8),f"{v:.0f}",fill="#16324f",anchor="ms",font=small); d.text((x,y0+12),lab,fill="#475569",anchor="ma",font=small)
    save(im,name)

def load(name): return json.load(open(ROOT/"output"/name,encoding="utf-8"))

# Daily volume
df=pd.read_csv(ROOT/"data"/"turkey_earthquake_tweets.csv")
dt=pd.to_datetime(df.date,errors="coerce",utc=True); daily=dt.dt.date.value_counts().sort_index()
bar_chart("Turkey Earthquake Tweet Stream: Daily Volume",[str(x)[5:] for x in daily.index],daily.tolist(),"Date","Tweets","fig01_daily_volume.png")
# Pipeline diagram
im=Image.new("RGB",(1400,360),"white"); d=ImageDraw.Draw(im); boxes=[("Raw tweet\nstream","#dbeafe"),("Preprocess\n+ TF-IDF","#e0f2fe"),("Online clustering\n+ TCV","#dcfce7"),("PTF pyramid\n(snapshots)","#fef3c7"),("TCV-Rank\nsummary","#fce7f3"),("Timeline\nEq. (3)","#ede9fe")]
for i,(txt,col) in enumerate(boxes):
 x=30+i*230; d.rounded_rectangle((x,110,x+180,230),radius=16,fill=col,outline="#334155",width=2); d.multiline_text((x+90,170),txt,anchor="mm",align="center",fill="#16324f",font=font)
 if i<len(boxes)-1: d.line((x+180,170,x+220,170),fill="#475569",width=3); d.polygon([(x+220,170),(x+208,163),(x+208,177)],fill="#475569")
d.text((700,300),"Historical summary: retrieve two PTF snapshots → Definition 4 subtraction → TCV-Rank",anchor="mm",fill="#334155",font=small); save(im,"fig02_pipeline.png")
step=load("exp_step_sweep_w3000.json"); xs=[int(x) for x in step["steps"]]; ms=[("Sumblr","#c2410c"),("ClusterSum","#2563eb"),("LexRank","#64748b"),("DSDR","#7c3aed"),("Random","#16a34a")]
line_chart("ROUGE-1 F1 vs. Step Size",xs,[(m,[step["by_step"][str(x)][m]["rouge1_f"] for x in xs],c) for m,c in ms],"Step size (tweets)","ROUGE-1 F1","fig03_step_quality.png")
line_chart("Runtime vs. Step Size (log scale)",xs,[(m,[step["by_step"][str(x)][m]["runtime_sec"] for x in xs],c) for m,c in ms],"Step size (tweets)","Runtime (s)","fig04_step_runtime.png",True)
scalej=load("exp_scalability.json")["by_size"]; xs=[int(x) for x in scalej]; ms2=[("Sumblr","#c2410c"),("ClusterSum","#2563eb"),("LexRank","#64748b"),("DSDR","#7c3aed")]
line_chart("Runtime vs. Window Size",xs,[(m,[scalej[str(x)][m] for x in xs],c) for m,c in ms2],"Window size (tweets)","Runtime (s)","fig05_scalability.png",True)
# Parameter curves: use 5 separate compact images
params=load("exp_params.json")
for key,label in [("beta","β"),("n_max","Nmax"),("mc","mc"),("m","m"),("lam","λ")]:
 vals=list(params[key]); x=[float(v) for v in vals]; y=[params[key][v]["mean_idf"] for v in vals]
 line_chart(f"Effect of {label}",x,[("Mean selected-term IDF",y,"#0f766e")],label,"Mean IDF",f"fig06_{key}.png")
flex=load("exp_flexibility.json"); xs=[int(x) for x in flex]; line_chart("PTF Flexibility: Eq.5 Score vs. l",xs,[("Eq.5 score",[flex[str(x)]["mean_score_eq5"] for x in xs],"#2563eb"),("Snapshots/1000",[flex[str(x)]["ptf"]["n_live"]/1000 for x in xs],"#c2410c")],"PTF depth l","Score / snapshots(×1000)","fig07_ptf_flexibility.png")
tl=load("exp_timeline.json"); xs=[float(x) for x in tl["by_tau"]]; line_chart("Timeline Precision / Recall / F1 vs. τ",xs,[("Precision",[tl["by_tau"][str(x)]["precision"] for x in xs],"#2563eb"),("Recall",[tl["by_tau"][str(x)]["recall"] for x in xs],"#c2410c"),("F1",[tl["by_tau"][str(x)]["f1"] for x in xs],"#16a34a")],"τ","Score","fig08_timeline_tau.png")
print("generated",len(list(OUT.glob("*.png"))))

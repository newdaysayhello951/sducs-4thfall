import json, re, sys, io, os

src = r"C:\Users\86134\AppData\Local\Temp\dsh-spill-f6YMwT\session-f8f531e38818\b2ecd6e7fa15-workflow.txt"
raw = open(src, encoding="utf-8").read()
start = raw.index("[")
data = json.loads(raw[start:])

out = io.StringIO()
order = ["file","title","venue_year","task","method_summary","datasets",
         "dataset_availability_claimed","evaluation","baselines",
         "implementation_complexity","repro_obstacles","notes"]
for i, p in enumerate(data, 1):
    out.write("=" * 100 + "\n")
    out.write("PAPER %d\n" % i)
    out.write("=" * 100 + "\n")
    for k in order:
        v = p.get(k, "")
        out.write("\n### %s\n%s\n" % (k.upper(), v))
    out.write("\n")

dst = r"C:\Users\86134\Desktop\大四上\社交网络实验五\__社交媒体摘要生成(Twitter&weibo)\社交舆论论文复现\_extracted\_paper_analysis.txt"
open(dst, "w", encoding="utf-8").write(out.getvalue())
print("wrote", dst, len(out.getvalue()))
print("papers:", len(data))
for i, p in enumerate(data, 1):
    print(i, p.get("implementation_complexity"), "|", p.get("title", "")[:80])

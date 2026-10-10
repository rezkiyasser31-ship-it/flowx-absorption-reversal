import sys
sys.stdout.reconfigure(encoding='utf-8')

for name in ["FLOWX_QUANTITATIVE_RESEARCH_REPORT_EN.html", "FLOWX_RAPPORT_DE_RECHERCHE_QUANTITATIVE_FR.html"]:
    print(f"=== {name} ===")
    with open(name, "r", encoding="utf-8") as f:
        html = f.read()
    chunks = html.split('<div class="math-box">')
    for idx, c in enumerate(chunks[1:], 1):
        box_inner = c.split("</div>")[0].strip()
        print(f"  Box {idx}: {box_inner}")

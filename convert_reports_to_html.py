import os
import re

def clean_inline(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    text = text.replace(r'\$', '$')
    return text

def render_md_to_html(md_path, html_path, title, lang="en"):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    html_lines = []
    in_table = False
    in_code = False
    
    css = """
    <style>
        :root {
            --primary: #0f172a;
            --accent: #1d4ed8;
            --accent-bg: #eff6ff;
            --success: #15803d;
            --danger: #b91c1c;
            --text: #1e293b;
            --muted: #64748b;
            --border: #cbd5e1;
            --bg-card: #f8fafc;
        }
        @media print {
            body { font-size: 10pt; margin: 0; padding: 12mm; }
            .no-print { display: none !important; }
            .page-break { page-break-before: always; }
            h1, h2, h3 { page-break-after: avoid; }
            table { page-break-inside: avoid; }
            pre { page-break-inside: avoid; }
            .math-box { page-break-inside: avoid; }
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: var(--text);
            max-width: 960px;
            margin: 0 auto;
            padding: 40px 30px;
            background: #ffffff;
        }
        .header-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid var(--accent);
            padding-bottom: 12px;
            margin-bottom: 24px;
        }
        h1 {
            font-size: 24pt;
            color: var(--primary);
            margin: 0 0 6px 0;
            letter-spacing: -0.5px;
        }
        h2 {
            font-size: 15pt;
            color: var(--accent);
            margin-top: 36px;
            margin-bottom: 14px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 6px;
        }
        h3 {
            font-size: 12pt;
            color: var(--primary);
            margin-top: 22px;
            margin-bottom: 8px;
        }
        p { margin: 10px 0; }
        ul, ol { margin: 10px 0; padding-left: 24px; }
        li { margin-bottom: 6px; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 18px 0;
            font-size: 9.5pt;
        }
        th, td {
            padding: 9px 12px;
            text-align: left;
            border: 1px solid var(--border);
        }
        th {
            background-color: #f1f5f9;
            color: var(--primary);
            font-weight: 700;
        }
        tr:nth-child(even) { background-color: #f8fafc; }
        pre {
            background: #0f172a;
            color: #f8fafc;
            padding: 14px 18px;
            border-radius: 6px;
            overflow-x: auto;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 9pt;
            line-height: 1.45;
            margin: 16px 0;
        }
        code {
            background: #f1f5f9;
            color: #0f172a;
            padding: 2px 5px;
            border-radius: 4px;
            font-family: "Consolas", monospace;
            font-size: 0.9em;
        }
        pre code {
            background: transparent;
            color: inherit;
            padding: 0;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 700;
            background: #dcfce7;
            color: #15803d;
            border: 1px solid #86efac;
        }
        .print-btn {
            background: var(--accent);
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .print-btn:hover { background: #1e40af; }
        
        /* High-Reliability Native Math Box (Offline & Brave Shield Proof) */
        .math-box {
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-left: 4px solid var(--accent);
            padding: 18px 24px;
            margin: 18px 0;
            border-radius: 6px;
            text-align: center;
            font-size: 1.25em;
            color: var(--primary);
            overflow-x: auto;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.02);
            font-family: "Cambria Math", "Latin Modern Math", "STIX Two Math", "Georgia", "Times New Roman", serif;
            letter-spacing: 0.5px;
        }
        .math-var {
            font-style: italic;
            font-family: "Cambria Math", "Georgia", "Times New Roman", serif;
            font-weight: 600;
        }
        .math-text {
            font-style: normal;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            font-weight: 600;
        }
        .fraction {
            display: inline-flex;
            flex-direction: column;
            vertical-align: middle;
            text-align: center;
            padding: 0 6px;
            font-size: 0.88em;
            margin: 0 3px;
        }
        .numerator {
            border-bottom: 2px solid var(--primary);
            padding-bottom: 2px;
            line-height: 1.1;
        }
        .denominator {
            padding-top: 2px;
            line-height: 1.1;
        }
        .math-sub {
            font-size: 0.72em;
            vertical-align: sub;
            font-style: normal;
        }
    </style>
    """

    doc = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {css}
</head>
<body>
<div class="header-bar no-print">
    <span class="status-badge">INSTITUTIONAL QUANT REPORT • STAGE 4 VALIDATED</span>
    <button class="print-btn" onclick="window.print()">📥 Print / Save as PDF</button>
</div>
"""
    
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        
        if stripped.startswith('```'):
            if in_code:
                html_lines.append('</code></pre>')
                in_code = False
            else:
                html_lines.append('<pre><code>')
                in_code = True
            i += 1
            continue
            
        if in_code:
            clean_code = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_lines.append(clean_code)
            i += 1
            continue
            
        if stripped.startswith('|') and stripped.endswith('|'):
            if not in_table:
                html_lines.append('<table>')
                in_table = True
                cells = [clean_inline(c.strip()) for c in stripped.strip('|').split('|')]
                html_lines.append('<thead><tr>' + ''.join(f'<th>{c}</th>' for c in cells) + '</tr></thead><tbody>')
                i += 2  # skip separator row
                continue
            else:
                cells = [clean_inline(c.strip()) for c in stripped.strip('|').split('|')]
                html_lines.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
                i += 1
                continue
        else:
            if in_table:
                html_lines.append('</tbody></table>')
                in_table = False
        
        # Check for Math Block $$ ... $$
        if stripped.startswith('$$') and stripped.endswith('$$') and len(stripped) > 4:
            math_content = stripped[2:-2].strip()
            # Render semantic, bulletproof math box (immune to Brave shields, offline, and no JS)
            if 'Threshold' in math_content:
                display_html = """<div class="math-box">
                    <span class="math-text">Threshold</span> = <strong>max</strong>(&thinsp;<span class="math-text">MinSweepFloor</span>,&ensp;<span class="math-text">SweepVolumeRatio</span> &times; <span class="math-text">SMA</span><span class="math-sub">20</span>(<span class="math-text">Bar Volume</span>)&thinsp;)
                </div>"""
            elif 'Seuil' in math_content:
                display_html = """<div class="math-box">
                    <span class="math-text">Seuil</span> = <strong>max</strong>(&thinsp;<span class="math-text">MinSweepFloor</span>,&ensp;<span class="math-text">SweepVolumeRatio</span> &times; <span class="math-text">SMA</span><span class="math-sub">20</span>(<span class="math-text">Volume de Barre</span>)&thinsp;)
                </div>"""
            elif 'K' in math_content and 'W' in math_content:
                display_html = """<div class="math-box">
                    <span class="math-var">K%</span> = <span class="math-var">W</span> &minus; 
                    <span class="fraction">
                        <span class="numerator">1 &minus; <span class="math-var">W</span></span>
                        <span class="denominator"><span class="math-var">R</span></span>
                    </span>
                    = 0.6552 &minus; 
                    <span class="fraction">
                        <span class="numerator">0.3448</span>
                        <span class="denominator">1.85</span>
                    </span>
                    = <strong>46.84%</strong>
                </div>"""
            else:
                display_html = f"""<div class="math-box">{clean_inline(math_content)}</div>"""
            html_lines.append(display_html)
            i += 1
            continue
                
        if stripped.startswith('# '):
            html_lines.append(f'<h1>{clean_inline(stripped[2:])}</h1>')
        elif stripped.startswith('## '):
            html_lines.append(f'<h2>{clean_inline(stripped[3:])}</h2>')
        elif stripped.startswith('### '):
            html_lines.append(f'<h3>{clean_inline(stripped[4:])}</h3>')
        elif stripped.startswith('#### '):
            html_lines.append(f'<h4 style="margin: 16px 0 6px 0; color: var(--primary);">{clean_inline(stripped[5:])}</h4>')
        elif stripped.startswith('---'):
            html_lines.append('<hr style="border: none; border-top: 1px solid var(--border); margin: 24px 0;">')
        elif stripped.startswith('* ') or stripped.startswith('- '):
            item = clean_inline(stripped[2:])
            html_lines.append(f'<li>{item}</li>')
        elif stripped == '':
            pass
        else:
            formatted = clean_inline(line)
            html_lines.append(f'<p>{formatted}</p>')
        i += 1
        
    if in_table:
        html_lines.append('</tbody></table>')
    if in_code:
        html_lines.append('</code></pre>')
        
    doc += '\n'.join(html_lines) + '\n</body></html>'
    with open(html_path, 'w', encoding='utf-8') as out:
        out.write(doc)
    print(f"Generated: {html_path}")

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    render_md_to_html(
        os.path.join(base, "FLOWX_QUANTITATIVE_RESEARCH_REPORT_EN.md"),
        os.path.join(base, "FLOWX_QUANTITATIVE_RESEARCH_REPORT_EN.html"),
        "FlowX Quantitative Research Report (EN)",
        "en"
    )
    render_md_to_html(
        os.path.join(base, "FLOWX_RAPPORT_DE_RECHERCHE_QUANTITATIVE_FR.md"),
        os.path.join(base, "FLOWX_RAPPORT_DE_RECHERCHE_QUANTITATIVE_FR.html"),
        "Rapport de Recherche Quantitative FlowX (FR)",
        "fr"
    )

#!/usr/bin/env python3
"""Generate assets/languages.svg: bytes of code per language across your repos.

Env:
  GH_TOKEN      token (GITHUB_TOKEN works for public repos; a PAT with `repo`
                scope also counts private repos)
  GH_USER       username (default: RidhuanDEV)
  AFFILIATION   owner | owner,collaborator,organization_member (default: owner)
  INCLUDE_FORKS 1 to count forks (default: 0)
  EXCLUDE       comma list of languages to skip (default: HTML,CSS,Blade,Dockerfile)
  TOP_N         languages shown (default: 12)
"""
import json, os, sys, urllib.request
from collections import Counter

USER = os.getenv("GH_USER", "RidhuanDEV")
TOKEN = os.getenv("GH_TOKEN", "")
AFFIL = os.getenv("AFFILIATION", "owner")
FORKS = os.getenv("INCLUDE_FORKS", "0") == "1"
EXCLUDE = {x.strip() for x in os.getenv("EXCLUDE", "HTML,CSS,Blade,Dockerfile").split(",") if x.strip()}
TOP_N = int(os.getenv("TOP_N", "12"))
OUT = os.getenv("OUT", "assets/languages.svg")

COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Kotlin": "#A97BFF", "Dart": "#00B4AB",
    "PHP": "#4F5D95", "Java": "#b07219", "Python": "#3572A5", "Go": "#00ADD8", "C#": "#178600",
    "PowerShell": "#012456", "Shell": "#89e051", "Vue": "#41b883", "SCSS": "#c6538c",
    "Swift": "#F05138", "C++": "#f34b7d", "C": "#555555", "Ruby": "#701516", "Rust": "#dea584",
}

def api(url):
    h = {"User-Agent": "lang-stats", "Accept": "application/vnd.github+json"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
        return json.load(r)

def list_repos():
    repos, page = [], 1
    while True:
        if TOKEN and AFFIL != "owner":
            url = f"https://api.github.com/user/repos?per_page=100&page={page}&affiliation={AFFIL}"
        else:
            url = f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner"
        batch = api(url)
        if not batch:
            break
        repos += batch
        page += 1
    return repos

def main():
    totals = Counter()
    repos = list_repos()
    for r in repos:
        if r["fork"] and not FORKS:
            continue
        for lang, n in api(r["languages_url"]).items():
            if lang not in EXCLUDE:
                totals[lang] += n
    if not totals:
        sys.exit("no language data")
    top = totals.most_common(TOP_N)
    total = sum(n for _, n in top)

    w, pad = 495, 25
    bar_w = w - 2 * pad
    rows = (len(top) + 1) // 2
    h = 95 + rows * 24 + 20
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
           f'<rect width="{w}" height="{h}" rx="6" fill="#1a1b27" stroke="#2f3146"/>',
           f'<text x="{pad}" y="35" fill="#70a5fd" font-family="Segoe UI,Ubuntu,Sans-Serif" font-size="18" font-weight="600">Most Used Languages</text>',
           f'<clipPath id="c"><rect x="{pad}" y="55" width="{bar_w}" height="10" rx="5"/></clipPath><g clip-path="url(#c)">']
    x = pad
    for lang, n in top:
        seg = bar_w * n / total
        svg.append(f'<rect x="{x:.2f}" y="55" width="{seg:.2f}" height="10" fill="{COLORS.get(lang, "#8b949e")}"/>')
        x += seg
    svg.append("</g>")
    for i, (lang, n) in enumerate(top):
        cx = pad + (i % 2) * (bar_w // 2)
        cy = 95 + (i // 2) * 24
        pct = 100 * n / total
        svg.append(f'<circle cx="{cx + 5}" cy="{cy}" r="5" fill="{COLORS.get(lang, "#8b949e")}"/>')
        svg.append(f'<text x="{cx + 16}" y="{cy + 4}" fill="#38bdae" font-family="Segoe UI,Ubuntu,Sans-Serif" font-size="12">{lang} <tspan fill="#a9b1d6">{pct:.1f}%</tspan></text>')
    svg.append("</svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))
    print("wrote", OUT, [(l, round(100 * n / total, 1)) for l, n in top])

if __name__ == "__main__":
    main()

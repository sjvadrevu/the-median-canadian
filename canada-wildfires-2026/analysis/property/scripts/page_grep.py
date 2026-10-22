"""Fetch an official web page (saved under raw/pages/) and print sentences with damage counts and links matching a pattern.
usage: page_grep.py <url> <name> [link_regex]"""
import sys, re, html, requests, os
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
url, name = sys.argv[1], sys.argv[2]; lre = sys.argv[3] if len(sys.argv) > 3 else r"wildfire|damage|structure|bald|recover"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
print(r.status_code, r.url)
open(os.path.join(P, "raw", "pages", name + ".html"), "w", encoding="utf-8").write(r.text)
links = sorted(set(re.findall(r'href="([^"]+)"', r.text)))
for l in links:
    if re.search(lre, l, re.I): print("LINK", l)
t = re.sub(r"<script.*?</script>|<style.*?</style>", "", r.text, flags=re.S)
t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
for m in re.finditer(r"[^.]{0,250}\b\d[\d,]*\b[^.]{0,40}(structure|home|house|propert|building|dwelling|residence|destroy|damag|lost|loss)[^.]{0,200}\.", t, re.I):
    print(">>", m.group(0).strip()[:500])
for m in re.finditer(r"(Date modified|Last updated|Updated|Posted)[^A-Za-z]{0,5}[:]?\s*[A-Za-z]*\s*[\d\-/, A-Za-z]{4,25}", t):
    print("DATE", m.group(0)[:60])

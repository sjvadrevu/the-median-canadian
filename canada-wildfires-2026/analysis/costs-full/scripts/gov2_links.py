"""List links on a saved HTML page whose text or URL matches a regex (helper for finding official PDFs)."""
import re, sys, html
from urllib.parse import urljoin
path, base, pat = sys.argv[1], sys.argv[2], sys.argv[3]
t = open(path, encoding='utf-8', errors='ignore').read()
seen = set()
for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', t, flags=re.S | re.I):
    url = urljoin(base, html.unescape(m.group(1)))
    txt = html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip()
    if re.search(pat, txt + ' ' + url, re.I) and url not in seen:
        seen.add(url)
        print(txt[:100].replace('\n', ' '), '|', url)

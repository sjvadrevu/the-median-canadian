"""Fetch a web page with curl, save raw HTML and a plain-text version.
Usage: python3 -I east_02_fetch_text.py URL OUT_BASENAME [grep_regex]
Writes OUT_BASENAME.html and OUT_BASENAME.txt; prints matching sentences if regex given."""
import sys, subprocess, re, html
url, out = sys.argv[1], sys.argv[2]
rx = sys.argv[3] if len(sys.argv) > 3 else None
raw = subprocess.run(["curl", "-sSL", "-m", "60", "-A", "Mozilla/5.0", url], capture_output=True).stdout.decode("utf8", "ignore")
open(out + ".html", "w").write(raw)
t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S)
links = re.findall(r'href="([^"]+)"', raw)
t = html.unescape(re.sub(r"<[^>]+>", " ", t))
t = re.sub(r"\s+", " ", t)
open(out + ".txt", "w").write(t + "\n\nLINKS:\n" + "\n".join(links))
print(len(raw), "bytes")
if rx:
    for m in re.finditer(r"[^.]{0,300}(" + rx + r")[^.]{0,300}\.", t, re.I):
        print("-", m.group(0).strip())

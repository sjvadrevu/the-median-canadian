"""Download official pages/PDFs (raw/pages, raw/pdf) and print sentences that contain a number next to
structure/home/property/building words, for manual reading into the event table (events_official.csv).
usage: 03_official_docs.py name=url [name=url ...]"""
import sys, re, html, requests, os, subprocess
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAT = re.compile(r"[^.;]{0,220}\b\d[\d,]*\b[^.;]{0,50}(structure|home|house|propert|building|dwelling|residen|cabin|destroy|damag|lost|loss)[^.;]{0,220}[.;]?", re.I)
for arg in sys.argv[1:]:
    name, url = arg.split("=", 1)
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=90)
    except Exception as e:
        print("##", name, "FAIL", e); continue
    ct = r.headers.get("content-type", "")
    print("##", name, r.status_code, ct[:30], r.url)
    if "pdf" in ct or url.lower().split("?")[0].endswith(".pdf"):
        f = os.path.join(P, "raw", "pdf", name + ".pdf"); open(f, "wb").write(r.content)
        t = subprocess.run(["pdftotext", f, "-"], capture_output=True, text=True).stdout
    else:
        open(os.path.join(P, "raw", "pages", name + ".html"), "w", encoding="utf-8").write(r.text)
        t = re.sub(r"<script.*?</script>|<style.*?</style>", "", r.text, flags=re.S)
        t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    t = re.sub(r"\s+", " ", t)
    for m in re.finditer(r"(Date modified|Last updated|Published|Release date)[^0-9A-Za-z]{0,5}[:]?\s*[\w ,\-]{6,22}", t): print("  DATE", m.group(0)); break
    for m in PAT.finditer(t): print("  >>", m.group(0).strip()[:520])

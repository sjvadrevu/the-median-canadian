"""Convert a saved HTML page to plain text (tables as pipe rows). Usage: python3 -I html2txt.py in.html out.txt"""
import re,html,sys
t=open(sys.argv[1],encoding='utf-8',errors='replace').read()
t=re.sub(r'<(script|style)[^>]*>.*?</\1>','',t,flags=re.S)
t=re.sub(r'</(p|tr|h[1-6]|li|div|caption)>','\n',t); t=re.sub(r'<t[dh][^>]*>',' | ',t)
t=html.unescape(re.sub(r'<[^>]+>','',t)); t=re.sub(r'[ \t]+',' ',t); t=re.sub(r'\n\s*\n+','\n',t)
open(sys.argv[2],'w').write(t)

import json, re, sys, requests
H={"User-Agent":"Mozilla/5.0 (compatible; AgendaConciertosMadrid/1.0)"}
urls=[l.strip() for l in open("urls.txt") if l.strip()]
out={}
def probe(u):
    try:
        r=requests.get(u,headers=H,timeout=25,allow_redirects=True)
    except Exception as e:
        return {"error":str(e)[:120]}
    t=r.text
    import hashlib,os
    os.makedirs('raw',exist_ok=True)
    open('raw/'+re.sub(r'[^a-z0-9]+','_',u.lower())[8:90]+'.txt','w').write(t[:400000])
    info={"status":r.status_code,"final":r.url,"len":len(t),"ctype":r.headers.get("content-type","")}
    info["generator"]=re.findall(r'<meta name="generator" content="([^"]+)"',t)[:3]
    info["ldtypes"]=re.findall(r'"@type"\s*:\s*"(\w*Event)"',t)[:5]
    info["ldcount"]=len(re.findall(r'"@type"\s*:\s*"\w*Event"',t))
    info["feeds"]=re.findall(r'<link[^>]+type="application/(?:rss|atom)\+xml"[^>]+href="([^"]+)"',t)[:4]
    info["hints"]=sorted(set(re.findall(r'(tribe-events|wp-json|mec-|eventon|events-manager|wix|shopify|squarespace|webflow|mutick|entradium|wegow|dice\.fm|fever|ticketea|eventbrite|bandsintown|songkick|seetickets|tiketin|giglon|ticketmaster|elcorteingles|enterticket|proticketing|tickentradas|codetickets)',t,re.I)))[:20]
    if "json" in info["ctype"]:
        info["body"]=t[:600]
    else:
        txt=re.sub(r"<script.*?</script>|<style.*?</style>","",t,flags=re.S)
        txt=re.sub(r"<[^>]+>"," ",txt); txt=re.sub(r"\s+"," ",txt)
        info["text"]=txt[:1500]
    return info
for u in urls:
    out[u]=probe(u); print(u, out[u].get("status"), out[u].get("error",""), file=sys.stderr)
json.dump(out,open("sondeo.json","w"),ensure_ascii=False,indent=1)

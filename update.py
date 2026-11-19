#!/usr/bin/env python3
"""Hourly Bitcoin news collector. AI translation and Telegram delivery are optional secrets."""
import os,json,re,hashlib,time,html
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request,urlopen
import xml.etree.ElementTree as ET

FEEDS=[
("CoinDesk","https://www.coindesk.com/arc/outboundfeeds/rss/"),
("Cointelegraph","https://cointelegraph.com/rss"),
("Bitcoin Magazine","https://bitcoinmagazine.com/.rss/full/"),
("Decrypt","https://decrypt.co/feed"),
("The Block","https://www.theblock.co/rss.xml"),
("Blockworks","https://blockworks.co/feed"),
("Bitcoin.com","https://news.bitcoin.com/feed/"),
("Glassnode","https://insights.glassnode.com/rss/"),
("Bitwise","https://bitwiseinvestments.com/crypto-market-insights/feed")]
TRUST={"CoinDesk":10,"Cointelegraph":9,"Bitcoin Magazine":9,"Decrypt":8,"The Block":9,"Blockworks":9,"Bitcoin.com":7,"Glassnode":10,"Bitwise":9}
BTC=re.compile(r'\b(bitcoin|btc|satoshi|lightning network|bitcoin mining|bitcoin miners)\b',re.I)
NOISE=re.compile(r'giveaway|sponsored|casino|meme coin|presale',re.I)
def get(url):
 req=Request(url,headers={"User-Agent":"Mozilla/5.0 BitcoinIntelligence/1.0","Accept":"application/rss+xml, application/atom+xml, application/xml"})
 with urlopen(req,timeout=25) as r:return r.read()
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s or ''))).strip()
def dateval(s):
 try:
  d=parsedate_to_datetime(s)
  if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
  return d.astimezone(timezone.utc)
 except:return datetime.now(timezone.utc)
def parse(source,url):
 root=ET.fromstring(get(url));out=[]
 nodes=root.findall('.//item')+root.findall('.//{http://www.w3.org/2005/Atom}entry')
 for n in nodes:
  def val(*paths):
   for p in paths:
    e=n.find(p)
    if e is not None and e.text:return e.text
   return ''
  title=clean(val('title','{http://www.w3.org/2005/Atom}title'))
  desc=clean(val('description','{http://www.w3.org/2005/Atom}summary','{http://www.w3.org/2005/Atom}content'))
  link=val('link')
  if not link:
   e=n.find('{http://www.w3.org/2005/Atom}link')
   if e is not None:link=e.attrib.get('href','')
  published=val('pubDate','published','updated','{http://www.w3.org/2005/Atom}published','{http://www.w3.org/2005/Atom}updated')
  if title and link:out.append({"title":title,"description":desc[:1600],"url":link,"published":dateval(published),"source":source})
 return out
def rank(x):
 age=max(0,(datetime.now(timezone.utc)-x["published"]).total_seconds()/3600)
 body=x["title"]+" "+x["description"]
 relevance=5+min(5,len(BTC.findall(body))*1.5)
 freshness=max(0,12-age*1.1)
 impact=3 if re.search(r'ETF|SEC|Fed|CPI|inflation|rate|institution|reserve|whale|hack|regulation|mining|halving',body,re.I) else 0
 return round(relevance+TRUST.get(x["source"],6)*.8+freshness+impact,2)
def ai_enrich(items):
 key=os.getenv("OPENAI_API_KEY")
 if not key:return items
 prompt="""برای هر ورودی، یک شیء در آرایه items بساز با فیلدهای title_fa (تیتر دقیق فارسی)، summary_fa (خلاصه فارسی دو جمله‌ای فقط بر اساس متن)، why_fa (اهمیت در یک جمله)، category (یکی از ETF، آنچین، اقتصاد کلان، قانون‌گذاری، استخراج، تکنیکال، نهادی، امنیت، بازار)، kind (news یا analysis)، bias (bullish یا bearish یا neutral). جهت اثر را فقط وقتی شواهد کافی هست تعیین کن، در غیر این صورت neutral. خبر و تحلیل را تفکیک کن. واقعیت اضافه نکن. JSON معتبر برگردان."""
 data=[{"title":x["title"],"description":x["description"][:900],"source":x["source"]} for x in items]
 payload={"model":os.getenv("OPENAI_MODEL","gpt-4.1-mini"),"messages":[{"role":"system","content":"You are a rigorous Bitcoin market editor. Return valid JSON only."},{"role":"user","content":prompt+"\\n"+json.dumps(data,ensure_ascii=False)}],"response_format":{"type":"json_object"},"temperature":0.2}
 req=Request("https://api.openai.com/v1/chat/completions",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
 try:
  result=json.loads(urlopen(req,timeout=90).read());enriched=json.loads(result["choices"][0]["message"]["content"]).get("items",[])
  for x,e in zip(items,enriched):
   for k in ("title_fa","summary_fa","why_fa","category","kind","bias"):
    if e.get(k):x[k]=str(e[k])
 except Exception as e:print("AI enrichment failed:",e)
 return items
def telegram(items):
 token=os.getenv("TELEGRAM_BOT_TOKEN");chat=os.getenv("TELEGRAM_CHAT_ID")
 if not token or not chat:return
 stamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
 lines=["₿ Bitcoin Intelligence | "+stamp,"۱۰ خبر و تحلیل برتر"]
 for i,x in enumerate(items,1):
  lines.append(f"{i}. {x.get('title_fa',x['title'])}\\n{x.get('summary_fa',x['description'])[:250]}\\n{x['source']} | {x['url']}")
 text="\\n\\n".join(lines)
 for start in range(0,len(text),3900):
  body=json.dumps({"chat_id":chat,"text":text[start:start+3900],"disable_web_page_preview":True}).encode()
  req=Request(f"https://api.telegram.org/bot{token}/sendMessage",data=body,headers={"Content-Type":"application/json"})
  try:urlopen(req,timeout=20).read()
  except Exception as e:print("Telegram error:",e)
def main():
 all_items=[]
 for source,url in FEEDS:
  try:all_items.extend(parse(source,url));print("OK",source)
  except Exception as e:print("Feed failed",source,str(e))
 now=datetime.now(timezone.utc);filtered=[]
 for x in all_items:
  if not BTC.search(x["title"]+" "+x["description"]) or NOISE.search(x["title"]):continue
  if (now-x["published"]).total_seconds()>72*3600:continue
  x["score"]=rank(x);filtered.append(x)
 seen=set();unique=[]
 for x in sorted(filtered,key=lambda a:a["score"],reverse=True):
  key=re.sub(r'[^a-z0-9]','',x["title"].lower())[:70]
  if key in seen:continue
  seen.add(key);unique.append(x)
 chosen=ai_enrich(sorted(unique,key=lambda a:a["score"],reverse=True)[:10])
 for x in chosen:
  x["published_fa"]=x["published"].astimezone().strftime("%Y/%m/%d %H:%M")
  x["published"]=x["published"].isoformat()
  x.setdefault("bias","neutral");x.setdefault("kind","news")
 os.makedirs("public",exist_ok=True)
 with open("public/data.json","w",encoding="utf-8") as f:json.dump({"updated_at":now.isoformat(),"items":chosen},f,ensure_ascii=False,indent=2)
 telegram(chosen);print("Published",len(chosen),"stories")
if __name__=="__main__":main()

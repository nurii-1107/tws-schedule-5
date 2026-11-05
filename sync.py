import json,re,html,urllib.request,datetime,pathlib,os,xml.etree.ElementTree as ET
from html.parser import HTMLParser
URL='https://tws-official.jp/schedule'
class Parser(HTMLParser):
 def __init__(self): super().__init__();self.parts=[];self.link=None
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'): self.parts.append(('skip',tag));return
  if tag=='a': self.link=dict(attrs).get('href','')
  if tag in ('p','li','div','article','h2','h3','h4','br','time'): self.parts.append(('break',''))
 def handle_endtag(self,tag):
  if tag=='a': self.link=None
  if tag in ('p','li','div','article','h2','h3','h4'): self.parts.append(('break',''))
 def handle_data(self,data):
  if data.strip():self.parts.append(('text',data.strip(),self.link))

def main():
 req=urllib.request.Request(URL,headers={'User-Agent':'Mozilla/5.0 (compatible; TWS-Public-Schedule/5.0)','Accept-Language':'ja,en;q=0.8'})
 with urllib.request.urlopen(req,timeout=25) as response: page=response.read().decode('utf-8','replace')
 p=Parser();p.feed(page)
 # Extract visible text and dates, not invented event entries. Date/title/category appear in schedule listing.
 tokens=[]
 for item in p.parts:
  if item[0]=='break': tokens.append((' ',None))
  elif item[0]=='text':tokens.append((html.unescape(item[1]),item[2]))
 text=' '.join(t for t,_ in tokens)
 pattern=re.compile(r'(?<!\d)(20\d{2})[./年\-](\d{1,2})[./月\-](\d{1,2})(?:日)?\s*(?:\|\s*)?(EVENT\s*&\s*LIVE|RELEASE|TV|MAGAZINE|WEB|RADIO|OTHER)?\s*(?:NEW\s*)?(.{4,180}?)(?=20\d{2}[./年\-]\d{1,2}[./月\-]\d{1,2}|$)',re.I)
 items=[];seen=set()
 for m in pattern.finditer(text):
  date=f'{int(m[1]):04d}-{int(m[2]):02d}-{int(m[3]):02d}'
  try:datetime.date.fromisoformat(date)
  except ValueError:continue
  category=(m[4] or '公开活动').strip()
  title=re.sub(r'\s+',' ',m[5]).strip(' |·-')
  title=re.split(r'\b(?:ALL EVENT|SCHEDULE|MORE|NEWS)\b',title)[0].strip()
  if not (4<=len(title)<=140) or (date,title) in seen:continue
  seen.add((date,title));items.append({'id':'jp-'+date+'-'+__import__('hashlib').sha256((date+'|'+title).encode()).hexdigest()[:12],'date':date,'title':title,'category':category,'member':('李炅潣' if re.search(r'KYUNGMIN|경민|炅潣',title,re.I) else '申惟' if re.search(r'SHINYU|신유|申惟',title,re.I) else '金道勋' if re.search(r'DOHOON|도훈|道勋',title,re.I) else '崔英宰' if re.search(r'YOUNGJAE|영재|英宰',title,re.I) else '韩振' if re.search(r'HANJIN|한진|韩振',title,re.I) else '韩志薰' if re.search(r'JIHOON|지훈|志薰',title,re.I) else '团体'),'url':URL,'source':'TWS 日本官网'})
 if not items:raise RuntimeError('未能可靠识别官网行程，保留旧数据，不覆盖')
 path=pathlib.Path(__file__).parent/'schedule.json'
 path.write_text(json.dumps({'updatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':URL,'events':items},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Parsed',len(items),'entries')
def sync_feed():
 path=pathlib.Path(__file__).parent/'feed.json'
 existing={'updatedAt':None,'posts':[],'sources':{}}
 if path.exists():
  try:existing=json.loads(path.read_text(encoding='utf-8'))
  except Exception:pass
 posts=existing.get('posts',[])
 statuses={
  'x_kr':{'state':'not_connected','message':'X 官方韩国账号：尚无稳定的授权读取接口'},
  'x_jp':{'state':'not_connected','message':'X 官方日本账号：尚无稳定的授权读取接口'},
  'instagram':{'state':'not_connected','message':'Instagram 帖子和 Story：尚无稳定的授权读取接口；无法保证快拍提醒'},
  'weverse':{'state':'not_connected','message':'Weverse 公告：尚未接入可靠的自动解析'},
  'sbs':{'state':'not_connected','message':'SBS 人气歌谣 MC 公告：尚未接入可靠的自动解析'},
  'mbc':{'state':'not_connected','message':'MBC 音乐中心特别 MC 公告：尚未接入可靠的自动解析'}
 }
 channel=os.environ.get('YOUTUBE_CHANNEL_ID','').strip()
 if not re.fullmatch(r'UC[A-Za-z0-9_-]{22}',channel):
  statuses['youtube']={'state':'needs_config','message':'请在 GitHub Actions 变量 YOUTUBE_CHANNEL_ID 设置 TWS 官方 YouTube 频道 ID（UC 开头的 24 位字符串）'}
 else:
  try:
   url='https://www.youtube.com/feeds/videos.xml?channel_id='+channel
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
   with urllib.request.urlopen(req,timeout=25) as response: xml=response.read()
   root=ET.fromstring(xml)
   atom='{http://www.w3.org/2005/Atom}'
   yt='{http://www.youtube.com/xml/schemas/2015}'
   incoming=[]
   for entry in root.findall(atom+'entry'):
    vid=entry.findtext(yt+'videoId')
    title=entry.findtext(atom+'title','')
    published=entry.findtext(atom+'published','')
    if not vid or not published:continue
    incoming.append({'id':'youtube-'+vid,'platform':'YouTube','type':'视频 / Shorts（公开更新源无法可靠区分）','title':title,'publishedAt':published,'url':'https://www.youtube.com/watch?v='+vid})
   ids={x.get('id') for x in posts}
   posts=[*incoming,*[x for x in posts if x.get('id') not in {i['id'] for i in incoming}]]
   posts=sorted(posts,key=lambda x:x.get('publishedAt',''),reverse=True)[:150]
   statuses['youtube']={'state':'ok','message':f'成功读取 YouTube 官方更新源，本次获取 {len(incoming)} 条','checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  except Exception as e:
   statuses['youtube']={'state':'error','message':'YouTube 同步失败：'+str(e)[:140]}
 existing.update({'updatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'posts':posts,'sources':statuses})
 path.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Feed:',statuses['youtube']['state'])

if __name__=='__main__':
 try:main()
 finally:sync_feed()


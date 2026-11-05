import json,re,html,urllib.request,datetime,pathlib
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
  seen.add((date,title));items.append({'id':'jp-'+date+'-'+str(len(items)),'date':date,'title':title,'category':category,'member':'团体','url':URL,'source':'TWS 日本官网'})
 if not items:raise RuntimeError('未能可靠识别官网行程，保留旧数据，不覆盖')
 path=pathlib.Path(__file__).parent/'schedule.json'
 path.write_text(json.dumps({'updatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':URL,'events':items},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Parsed',len(items),'entries')
if __name__=='__main__':main()

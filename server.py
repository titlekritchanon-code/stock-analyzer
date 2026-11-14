import json, os, re, time, csv, io, urllib.request, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
CACHE={}
def fetch(url,sec=False):
    if url in CACHE and time.time()-CACHE[url][0]<900:return CACHE[url][1]
    email=os.environ.get('SEC_CONTACT_EMAIL','').strip()
    if sec and not email:raise ValueError('ตั้งค่า SEC_CONTACT_EMAIL เป็นอีเมลติดต่อจริงก่อนดึงงบ SEC (ไม่ใช่ API key)')
    headers={'User-Agent':('StockAnalyzer/1.0 '+email) if sec else 'StockAnalyzer/1.0','Accept':'application/json,text/csv,*/*'}
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=35) as r:data=r.read().decode('utf-8-sig')
    CACHE[url]=(time.time(),data)
    return data

def financials(symbol):
    tickers=json.loads(fetch('https://www.sec.gov/files/company_tickers.json',True))
    hit=next((v for v in tickers.values() if v['ticker'].upper()==symbol),None)
    if not hit:raise ValueError('ไม่พบ ticker ใน SEC')
    cik=str(hit['cik_str']).zfill(10)
    facts=json.loads(fetch('https://data.sec.gov/api/xbrl/companyfacts/CIK'+cik+'.json',True))['facts'].get('us-gaap',{})
    def select(tags,duration=True):
        for tag in tags:
            rows=facts.get(tag,{}).get('units',{}).get('USD',[])
            if duration:
                from datetime import date
                rows=[r for r in rows if r.get('form') in ('10-K','10-K/A','20-F','20-F/A') and 'start' in r and 330<=(date.fromisoformat(r['end'])-date.fromisoformat(r['start'])).days<=380]
            else:rows=[r for r in rows if r.get('form') in ('10-K','10-Q','20-F','10-K/A','10-Q/A')]
            unique={}
            for r in sorted(rows,key=lambda r:r.get('filed','')):unique[r['end']]=r
            if unique:return sorted(unique.values(),key=lambda r:r['end'],reverse=True)
        return []
    def first(tags,duration=True):
        a=select(tags,duration)
        return a[0] if a else None
    rev=select(['RevenueFromContractWithCustomerExcludingAssessedTax','Revenues','SalesRevenueNet'])
    metrics={'รายได้':rev[0] if rev else None,'กำไรสุทธิ':first(['NetIncomeLoss']),'เงินสดจากการดำเนินงาน':first(['NetCashProvidedByUsedInOperatingActivities']),'CapEx':first(['PaymentsToAcquirePropertyPlantAndEquipment']),'เงินสด':first(['CashAndCashEquivalentsAtCarryingValue'],False),'หนี้สินรวม (ไม่ใช่หนี้มีดอกเบี้ย)':first(['Liabilities'],False),'ส่วนของผู้ถือหุ้น':first(['StockholdersEquity','StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest'],False)}
    growth=None
    if len(rev)>1 and rev[1]['val']:growth=(rev[0]['val']/rev[1]['val']-1)*100
    return {'name':hit['title'],'metrics':metrics,'growth':growth,'source':'https://www.sec.gov/edgar/browse/?CIK='+cik}

def prices(symbol):
    csvtext=fetch('https://stooq.com/q/d/l/?'+urllib.parse.urlencode({'s':symbol.lower()+'.us','i':'d'}))
    rows=list(csv.DictReader(io.StringIO(csvtext)))
    rows=[{'date':r['Date'],'close':float(r['Close']),'low':float(r['Low']),'high':float(r['High'])} for r in rows if r.get('Close')]
    rows.sort(key=lambda r:r['date'])
    if not rows:raise ValueError('แหล่งราคาไม่มีข้อมูล ticker นี้')
    rows=rows[-756:];closes=[r['close'] for r in rows];last=closes[-1]
    sma=lambda n:sum(closes[-n:])/n if len(closes)>=n else None
    pivots=[rows[i]['low'] for i in range(2,len(rows)-2) if rows[i]['low']==min(r['low'] for r in rows[i-2:i+3]) and rows[i]['low']<last]
    levels=[]
    for v in sorted(pivots,reverse=True):
        if all(abs(v-x)/x>.025 for x in levels):levels.append(v)
        if len(levels)==5:break
    return {'rows':rows,'sma50':sma(50),'sma200':sma(200),'supports':levels,'source':'https://stooq.com/q/?s='+symbol.lower()+'.us'}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=urllib.parse.urlparse(self.path)
        if path.path=='/':
            body=Path(__file__).with_name('index.html').read_bytes();kind='text/html; charset=utf-8'
        elif path.path=='/api/analyze':
            symbol=urllib.parse.parse_qs(path.query).get('symbol',[''])[0].upper().strip()
            if not re.fullmatch(r'[A-Z][A-Z0-9.\-]{0,14}',symbol):
                self.send_error(400,'Invalid ticker');return
            result={'symbol':symbol,'retrieved':time.strftime('%Y-%m-%d %H:%M:%S %Z'),'errors':{}}
            for key,fn in [('prices',prices),('financials',financials)]:
                try:result[key]=fn(symbol)
                except Exception as e:result['errors'][key]=str(e)
            body=json.dumps(result,ensure_ascii=False).encode();kind='application/json; charset=utf-8'
        else:self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
if __name__=='__main__':
    print('Open http://localhost:8000 — Ctrl+C to stop')
    HTTPServer(('127.0.0.1',8000),Handler).serve_forever()

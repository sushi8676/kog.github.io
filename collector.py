"""Namu Wiki LoL item snapshot collector. Requires requests, beautifulsoup4.

Collects only values actually found in Namu Wiki tables. Unknown/unparsed
fields remain null. Never overwrites a previous snapshot on partial failure.
"""
import argparse, csv, datetime, json, re, sys, time
from pathlib import Path
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup

PAGES = ['시작', '기본', '서사', '전설', '장화']
ROOT = 'https://namu.wiki/w/'
PAGE_PREFIX = '리그 오브 레전드/아이템/'
OUT = Path(__file__).parent / 'data'
STATS = {'공격력':'공격력','주문력':'주문력','방어력':'방어력','마법 저항력':'마법 저항력','공격 속도':'공격 속도','이동 속도':'이동 속도','체력':'체력','마나':'마나','스킬 가속':'스킬 가속','치명타 확률':'치명타 확률','치명타 피해량':'치명타 피해량','생명력 흡수':'생명력 흡수','물리 관통력':'물리 관통력','마법 관통력':'마법 관통력','방어구 관통력':'방어구 관통력'}
ITEM_SKIP = re.compile(r'(수호자의 (검|보주|망치|뿔피리)|포션|물약|영약|와드|장신구)',re.I)
NUM = re.compile(r'(?<!\d)([+-]?\d[\d,]*(?:\.\d+)?)\s*(%)?')

def clean(s): return re.sub(r'\s+',' ',s).strip()
def make_url(group): return ROOT+quote(PAGE_PREFIX+group, safe='/')

def extract(group, html):
    """Conservative table parsing. Entries without full identification go to review."""
    soup=BeautifulSoup(html,'html.parser')
    for tag in soup(['script','style','nav','footer']):tag.decompose()
    items=[]; review=[]
    for table in soup.find_all('table'):
        # Namu wiki wiki-table cells are varied; collect the plain text and analyze.
        txt=clean(table.get_text(' ',strip=True))
        if len(txt)<30 or len(txt)>2800:continue
        pm=re.search(r'(?:가격|구매 가격|총 가격)\s*[:：]?\s*([\d,]+)\s*(?:골드|G|g)?',txt)
        if not pm:continue
        price=int(pm.group(1).replace(',',''))
        if not (100<=price<=6000):continue
        # Candidate title: table's first bold (often item name); do not guess if ambiguous.
        header=table.find(['strong','b'])
        name=clean(header.get_text(' ',strip=True)) if header else ''
        if not name or len(name)>35 or name.isdigit() or ITEM_SKIP.search(name):
            review.append({'section':group,'reason':'name unclear','excerpt':txt[:220]});continue
        stats={}
        for label in STATS:
            matches=re.findall(re.escape(label)+r'\s*[:：+]?\s*([+-]?\d+(?:\.\d+)?)\s*(%)?',txt)
            # If conflicting values within same table, require review.
            if len(matches)==1:
                val=float(matches[0][0]);stats[label]=int(val) if val.is_integer() else val
            elif len(matches)>1:
                stats[label]=None
        if not stats:
            review.append({'section':group,'reason':'no recognized stats','name':name,'excerpt':txt[:220]});continue
        items.append({'name':name,'price':price,'stats':stats,'section':group,'source':make_url(group),'review_required':any(v is None for v in stats.values())})
    return items,review

def run():
    ap=argparse.ArgumentParser();ap.add_argument('--snapshot',help='Snapshot name, e.g. 26.22',default='');args=ap.parse_args()
    OUT.mkdir(exist_ok=True)
    session=requests.Session();session.headers.update({'User-Agent':'Mozilla/5.0 (compatible; item-stat-checker/1.0)'})
    collected=[];review=[];errors=[]
    for group in PAGES:
        url=make_url(group)
        try:
            r=session.get(url,timeout=20);r.raise_for_status()
            if len(r.text)<1000:raise ValueError('empty or blocked page')
            items,issues=extract(group,r.text)
            if not items:raise ValueError('no confidently parsed item tables; HTML structure may have changed')
            collected+=items;review+=issues
            print(f'{group}: candidates {len(items)}, review {len(issues)}')
        except Exception as ex:errors.append(f'{group}: {type(ex).__name__}: {ex}')
        time.sleep(1)
    # Prevent silently overwriting with incomplete or suspicious data.
    if errors:
        (OUT/'last_errors.txt').write_text('\n'.join(errors),encoding='utf-8')
        print('ERROR: Not all Namu Wiki sections could be collected; no snapshots updated.',file=sys.stderr)
        print('\n'.join(errors),file=sys.stderr);return 1
    unique={};duplicates=[]
    for x in collected:
        key=re.sub(r'\s+','',x['name']).lower()
        if key in unique:
            duplicates.append({'original':unique[key], 'duplicate':x})
            continue
        unique[key]=x
    items=sorted(unique.values(),key=lambda i:(i['price'],i['name']))
    if len(items)<40:
        print(f'ERROR: only {len(items)} items parsed; inspect review before accepting.',file=sys.stderr)
        (OUT/'last_review.json').write_text(json.dumps({'items':items,'review':review,'duplicates':duplicates},ensure_ascii=False,indent=2),encoding='utf-8')
        return 2
    label=args.snapshot or datetime.datetime.now().strftime('%Y-%m-%d')
    label=re.sub(r'[^a-zA-Z0-9._-]','_',label)
    dst=OUT/f'items_{label}.json'
    if dst.exists():print('ERROR: snapshot exists; will not overwrite:',dst,file=sys.stderr);return 3
    previous=sorted(OUT.glob('items_*.json'))
    before=json.loads(previous[-1].read_text('utf-8'))['items'] if previous else []
    old={x['name']:x for x in before};new={x['name']:x for x in items}
    diff=[]
    for name in sorted(old.keys()|new.keys()):
        a=old.get(name);b=new.get(name)
        if a!=b:
            changes={}
            for k in ('price','stats'):
                va=a.get(k) if a else None;vb=b.get(k) if b else None
                if va!=vb:changes[k]={'before':va,'after':vb}
            if changes or not a or not b:diff.append({'name':name,'changes':changes,'new':not bool(a),'removed':not bool(b)})
    meta={'source':'namu.wiki','snapshot':label,'collected_at':datetime.datetime.now().isoformat(),'complete_validation':False,'note':'Automatic extraction is provisional; review individual items against pages','items':items}
    dst.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/f'changes_{label}.json').write_text(json.dumps(diff,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/f'review_{label}.json').write_text(json.dumps({'ambiguous':review,'duplicates':duplicates},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Created {dst.name}: {len(items)} provisional items, {len(diff)} change records, {len(review)} review issues')
    return 0

if __name__=='__main__':raise SystemExit(run())

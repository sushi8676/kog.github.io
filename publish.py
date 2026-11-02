"""Safely publish a new snapshot ONLY if it passes conservative checks.
No Riot Data Dragon fields are used. Never replaces site data on a failed fetch.
"""
import json, sys, pathlib, subprocess, re, datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
label=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
cmd=[sys.executable,str(ROOT/'scripts'/'collector.py'),'--snapshot',label]
result=subprocess.run(cmd,cwd=ROOT,check=False)
if result.returncode:
    print('Collector failed. Existing public data remains unchanged.');raise SystemExit(result.returncode)
path=ROOT/'scripts'/'data'/f'items_{label}.json'
data=json.loads(path.read_text(encoding='utf-8'))
items=data['items']
review=ROOT/'scripts'/'data'/f'review_{label}.json'
issues=json.loads(review.read_text(encoding='utf-8'))
# Safe fail-closed: do not overwrite the website when extraction is incomplete.
if len(items)<150 or issues['ambiguous'] or issues['duplicates'] or any(x.get('review_required') for x in items):
    print('NOT PUBLISHED: insufficient item coverage or ambiguous data',len(items));raise SystemExit(2)
# Important: even 150+ parsed rows cannot confirm correspondence to the live shop.
# Require explicit review approval from maintainers before changing public values.
if '--approve' not in sys.argv:
    print('NOT PUBLISHED: needs manual validation/approval. Existing site unchanged.');raise SystemExit(3)
old=ROOT/'site'/'data'/'items.json'
prev=json.loads(old.read_text(encoding='utf-8'))
stat_map={'공격력':'ad','주문력':'ap','방어력':'armor','마법 저항력':'mr','공격 속도':'as','이동 속도':'ms','체력':'hp','마나':'mana','스킬 가속':'ah','치명타 확률':'crit','치명타 피해량':'critdmg','생명력 흡수':'lifesteal','물리 관통력':'lethality','마법 관통력':'magicpen','방어구 관통력':'armorpen'}
out={'patch':'미확인', 'status':'partial','source':'namu.wiki / manual approval','items':[{'name':r['name'],'price':r['price'],'stats':{stat_map[k]:v for k,v in r['stats'].items() if k in stat_map},'kind':r['section']} for r in items]}
old.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Published',len(items))

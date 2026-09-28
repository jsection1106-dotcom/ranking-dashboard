# -*- coding: utf-8 -*-
"""各媒体の店舗ランキングを取得し、ranking_data.json / ranking_data.js を更新する。

使い方:
  python fetch_rankings.py                # 今週(月曜)分を取得して data/ 以下を更新
  python fetch_rankings.py --dry-run      # 取得結果を表示するだけ(保存しない)
  python fetch_rankings.py --week 2026-09-28 --data-dir <リポジトリのパス>
"""
import argparse, datetime as dt, html, json, os, re, sys, time, unicodedata
import urllib.error, urllib.request

AREAS = ['西船橋', '錦糸町', '沼津', '千葉', '木更津', '成田', '神栖', '水戸']
MY_STORES = {
    '西船橋': ['西船人妻花壇', '丸妻西船橋店'],
    '錦糸町': ['錦糸町人妻花壇', '丸妻錦糸町店'],
    '沼津': ['沼津人妻花壇'], '千葉': ['千葉人妻花壇'], '木更津': ['木更津人妻花壇'],
    '成田': ['成田人妻花壇'], '神栖': ['神栖人妻花壇'], '水戸': ['水戸人妻花壇'],
}
# ダッシュボード(ranking_dashboard_v8.html)の URLS と同じ
URLS = {
  '西船橋':{'シティヘブン':'https://www.cityheaven.net/chiba/shop-ranking-205418/','デリヘルタウン':'https://www.dto.jp/funabashi/shop-list/ranking?cat=2','風俗じゃぱん':'https://fuzoku.jp/chiba/a_2084/biz_4/ge_1/shopranking/','デリヘルじゃぱん':'https://deli-fuzoku.jp/chiba/nishifunabashi_area/ranking/','駅ちか人気！':'https://ranking-deli.jp/11/area63/genre6/','口コミ風俗情報局':'https://fujoho.jp/index.php?p=ranking_shop&s=181&k=16','ぴゅあらば':'https://purelovers.com/b1/p11/a81/ranking/shop/'},
  '錦糸町':{'シティヘブン':'https://www.cityheaven.net/tokyo/shop-ranking-203291/','デリヘルタウン':'https://www.dto.jp/kinshicho/shop-list/ranking?cat=2','風俗じゃぱん':'https://fuzoku.jp/tokyo/kinshicho_area/biz_4/ge_1/shopranking/','デリヘルじゃぱん':'https://deli-fuzoku.jp/tokyo/kinshicho_area/genre3/ranking/','駅ちか人気！':'https://ranking-deli.jp/8/area36/genre6/','口コミ風俗情報局':'https://fujoho.jp/index.php?p=ranking_shop&s=75&k=16','ぴゅあらば':'https://purelovers.com/b1/p8/a56/ranking/shop/'},
  '沼津':{'シティヘブン':'https://www.cityheaven.net/shizuoka/shop-ranking-205316/','デリヘルタウン':'https://www.dto.jp/numadu/shop-list/ranking?cat=2','風俗じゃぱん':'https://fuzoku.jp/shizuoka/a_3052/biz_4/ge_1/shopranking/','デリヘルじゃぱん':'https://deli-fuzoku.jp/shizuoka/numazu_area/genre3/ranking/','駅ちか人気！':'https://ranking-deli.jp/17/area97/genre6/','口コミ風俗情報局':'https://fujoho.jp/index.php?p=ranking_shop&s=989&k=16','ぴゅあらば':'https://purelovers.com/b1/p23/a138/ranking/shop/','バナナビ':'https://bananavi.jp/shizuoka/pc/ranking/shop.php?mode=search'},
  '千葉':{'シティヘブン':'https://www.cityheaven.net/chiba/shop-ranking-205415/','デリヘルタウン':'https://www.dto.jp/chibashi/shop-list/ranking?cat=2','風俗じゃぱん':'https://fuzoku.jp/chiba/a_2089/biz_4/ge_1/shopranking/','デリヘルじゃぱん':'https://deli-fuzoku.jp/chiba/sakaemachi_area/genre3/ranking/','駅ちか人気！':'https://ranking-deli.jp/11/area62/','口コミ風俗情報局':'https://fujoho.jp/index.php?p=ranking_shop&s=138&k=16','ぴゅあらば':'https://purelovers.com/b1/p11/a80/ranking/shop/'},
  '木更津':{'シティヘブン':'https://www.cityheaven.net/chiba/shop-ranking-200604/','デリヘルタウン':'https://www.dto.jp/kisaradu/shop-list/ranking?cat=2','風俗じゃぱん':'https://fuzoku.jp/chiba/a_2133/biz_4/ge_1/shopranking/','デリヘルじゃぱん':'https://deli-fuzoku.jp/chiba/kisarazu_area/genre3/ranking/','駅ちか人気！':'https://ranking-deli.jp/11/area70/genre6/','口コミ風俗情報局':'https://fujoho.jp/index.php?p=ranking_shop&s=630&k=16'},
  '成田':{'シティヘブン':'https://www.cityheaven.net/chiba/shop-ranking-200602/','デリヘルタウン':'https://www.dto.jp/narita/shop-list/ranking?cat=2','風俗じゃぱん':'https://fuzoku.jp/chiba/narita_area/biz_4/ge_1/shopranking/','デリヘルじゃぱん':'https://deli-fuzoku.jp/chiba/narita_area/genre3/ranking/','駅ちか人気！':'https://ranking-deli.jp/11/area67/genre6/','口コミ風俗情報局':'https://fujoho.jp/index.php?p=ranking_shop&s=342&k=16'},
  '神栖':{'シティヘブン':'https://www.cityheaven.net/ibaraki/shop-ranking-201279/','デリヘルタウン':'https://www.dto.jp/kamisu/shop-list/ranking','風俗じゃぱん':'https://fuzoku.jp/ibaraki/a_2119/biz_4/shopranking/','デリヘルじゃぱん':'https://deli-fuzoku.jp/ibaraki/kamisu_area/genre3/ranking/','駅ちか人気！':'https://ranking-deli.jp/13/area82/genre6/','口コミ風俗情報局':'https://fujoho.jp/index.php?p=ranking_shop&s=2685&k=16'},
  '水戸':{'シティヘブン':'https://www.cityheaven.net/ibaraki/shop-ranking-201277/','デリヘルタウン':'https://www.dto.jp/mito/shop-list/ranking?cat=2','風俗じゃぱん':'https://fuzoku.jp/ibaraki/a_2118/biz_4/shopranking/','デリヘルじゃぱん':'https://deli-fuzoku.jp/ibaraki/mito_area/genre3/ranking/','駅ちか人気！':'https://ranking-deli.jp/13/area79/genre6/','口コミ風俗情報局':'https://fujoho.jp/index.php?p=ranking_shop&s=718&k=16','ぴゅあらば':'https://purelovers.com/b1/p12/a90/ranking/shop/'},
}
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'ja,en;q=0.8',
                                               'Cookie': 'age=1; ageCheck=1; adult=1'})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        cs = r.headers.get_content_charset() or 'utf-8'
    return raw.decode(cs, errors='replace')


def clean(s):
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()


def jsonld_names(t):
    """schema.org ItemList の name を position 順に返す"""
    for block in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', t, re.S):
        try:
            data = json.loads(block)
        except Exception:
            continue
        for obj in (data if isinstance(data, list) else [data]):
            if isinstance(obj, dict) and obj.get('@type') == 'ItemList' and obj.get('itemListElement'):
                items = sorted(obj['itemListElement'], key=lambda x: x.get('position', 0))
                names = [(it.get('name') or (it.get('item') or {}).get('name') or '') for it in items]
                if any(names):
                    return [clean(n) for n in names]
    return []


def parse(media, t):
    if media == 'シティヘブン':
        return [clean(x) for x in re.findall(r'class="shop_title_shop"[^>]*>\s*<span itemprop="name">([^<]+)', t)]
    if media == 'デリヘルタウン':
        return [clean(x) for x in re.findall(r'<div class="shop_name"><span class="number[^"]*">[^<]*</span><a[^>]*>([^<]+)', t)]
    if media == '風俗じゃぱん':
        got = re.findall(r'headRanking--(\d+)">\s*\d+\s*</span>\s*<a[^>]*>\s*<h3[^>]*>([^<]+)', t)
        seen, out = set(), []
        for n, name in sorted(got, key=lambda x: int(x[0])):
            if n not in seen:
                seen.add(n); out.append(clean(name))
        return out
    if media == 'デリヘルじゃぱん':
        return [clean(x) for x in re.findall(r'<li class="shop-item[^"]*"[^>]*data-selectshopname="([^"]+)"', t)]
    if media in ('駅ちか人気！', 'ぴゅあらば'):
        return jsonld_names(t)
    if media == '口コミ風俗情報局':
        out = []
        for m in re.finditer(r'<section class="shop[ "]', t):
            seg = t[m.start():m.start() + 4000]
            n = re.search(r'class="(?:name|shop_header_info_shopname)"[^>]*>([^<]+)', seg)
            if n:
                out.append(clean(n.group(1)))
        return out
    if media == 'バナナビ':
        return [clean(x) for x in re.findall(r'<p class="shop"><a[^>]*>([^<]+)', t)]
    return []


# ---- 店名の表記ゆれ対策 ----
def loose_key(s):
    s = unicodedata.normalize('NFKC', s or '')
    s = re.sub(r'[\(（\[【][^\)）\]】]*[\)）\]】]', '', s)   # (カサブランカグループ) 等を無視
    s = re.sub(r'[\s★☆・\-‐－〜~～!！]', '', s)
    return s.upper()


def dash_norm(s):
    """ダッシュボードの normalizeShopName と同じ比較用正規化"""
    s = (s or '').strip()
    s = re.sub(r'[Ａ-Ｚａ-ｚ０-９]', lambda m: chr(ord(m.group()) - 0xFEE0), s)
    s = re.sub(r'\s+', ' ', s.replace('　', ' '))
    s = re.sub(r'[－ｰ‐‑‒–—―]', '-', s).replace('（', '(').replace('）', ')')
    return s.upper().strip()


def build_canon(data, area, media):
    """過去データで使われていた表記の一覧 (同じ媒体を優先、次に同エリアの他媒体)"""
    same, other = {}, {}
    for wk in sorted(k for k in data if re.match(r'\d{4}-\d{2}-\d{2}$', k)):
        for md, v in (((data[wk].get('rankings') or {}).get(area)) or {}).items():
            for name in (v or {}).get('ranks', []):
                if name and name != '-':
                    (same if md == media else other)[loose_key(name)] = name
    return same, other


def canonical(name, canon, stores):
    """スクレイプした店名を過去の表記(または自店の登録名)に寄せる。
    例: 「モアグループ水戸人妻花壇」→「水戸人妻花壇」、「千葉県No,1デリヘル 秘密倶楽部 凛 船橋本店」→「秘密倶楽部 凛 船橋本店」"""
    k = loose_key(name)
    for s in stores:
        if loose_key(s) in k:
            return s
    for table in canon:
        if k in table:
            return table[k]
    for table in canon[:1]:
        hits = [h for h in table if len(h) >= 4 and h in k]
        if hits:
            return table[max(hits, key=len)]
    return name


def is_my_store(name, store):
    return name == store or dash_norm(name) == dash_norm(store)


def scrape_all(data, log):
    result, problems = {}, []
    for area in AREAS:
        result[area] = {}
        for media, url in URLS[area].items():
            names = []
            for attempt in range(3):
                try:
                    names = parse(media, fetch(url))
                    break
                except urllib.error.HTTPError as e:
                    err = e
                    if e.code == 404:   # ランキングページ自体が無い(例: ぴゅあらば西船橋)
                        names = None
                        break
                    time.sleep(3)
                except Exception as e:
                    err = e
                    time.sleep(3)
            else:
                problems.append(f'{area}/{media}: 取得失敗 ({err})')
                continue
            if names is None:
                result[area][media] = {'ranks': ['-'] * 5, 'myRanks': {st: 'ランク外' for st in MY_STORES[area]}}
                log(f'  {area} / {media}: ランキングページなし(404) → 「-」「ランク外」で登録')
                continue
            if not names:
                problems.append(f'{area}/{media}: 店舗が読み取れませんでした')
                continue
            canon = build_canon(data, area, media)
            names = [canonical(n, canon, MY_STORES[area]) for n in names]
            top = names[:5]
            top += ['-'] * (5 - len(top))
            my = {}
            for store in MY_STORES[area]:
                pos = next((i + 1 for i, n in enumerate(names) if is_my_store(n, store)), None)
                my[store] = f'{pos}位' if pos else 'ランク外'
            result[area][media] = {'ranks': top, 'myRanks': my}
            log(f'  {area} / {media}: {" | ".join(top)}  →  ' + ', '.join(f'{k}:{v}' for k, v in my.items()))
            time.sleep(1)
    return result, problems


def monday_of(d):
    return d - dt.timedelta(days=d.weekday())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', help='集計週(月曜) YYYY-MM-DD。省略時は今週の月曜')
    ap.add_argument('--data-dir', default='.', help='ranking_data.json があるフォルダ')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--overwrite', action='store_true', help='その週に手入力済みの媒体も上書きする')
    a = ap.parse_args()

    jst = dt.timezone(dt.timedelta(hours=9))
    week = a.week or monday_of(dt.datetime.now(jst).date()).isoformat()
    jpath = os.path.join(a.data_dir, 'ranking_data.json')
    data = json.load(open(jpath, encoding='utf-8')) if os.path.exists(jpath) else {}

    print(f'集計週: {week}')
    scraped, problems = scrape_all(data, print)

    wd = data.setdefault(week, {'date': week, 'rankings': {}, 'google': {}})
    wd.setdefault('rankings', {}); wd.setdefault('google', {})
    for area, medias in scraped.items():
        cur = wd['rankings'].setdefault(area, {})
        for media, v in medias.items():
            existing = cur.get(media)
            if existing and any(x and x != '-' for x in existing.get('ranks', [])) and not a.overwrite:
                continue  # 手入力済みは残す
            cur[media] = v

    if problems:
        print('\n⚠ 要確認:'); [print('  - ' + p) for p in problems]
        if os.environ.get('GITHUB_ACTIONS'):
            [print(f'::warning::{p}') for p in problems]
    if a.dry_run:
        print('\n(dry-run のため保存していません)'); return 1 if problems else 0

    ordered = data  # 既存の並び順を維持(差分を最小にする)
    open(jpath, 'w', encoding='utf-8', newline='\n').write(json.dumps(ordered, ensure_ascii=False, indent=2))
    compact = json.dumps(ordered, ensure_ascii=False, separators=(',', ':'))
    open(os.path.join(a.data_dir, 'ranking_data.js'), 'w', encoding='utf-8', newline='\n').write('window.RANKING_DATA = ' + compact + ';')
    print(f'\n保存しました: {jpath}')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())

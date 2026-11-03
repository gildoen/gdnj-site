#!/usr/bin/env python3
"""길된교회 홈페이지 시안 빌드 스크립트.

_build/pages/*.html 의 본문에 공통 머리말(메뉴)·꼬리말을 붙여서
상위 폴더에 완성된 페이지를 만든다. 설교 목록은 유튜브 RSS에서 새로 받아온다.

    python3 _build/build.py
"""
import html, json, os, re, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.join(ROOT, "_build", "pages")
CHANNEL = "UC9ukAAK6FBx7aL60_y4Cd8w"
YT = "https://www.youtube.com/@gildoenpresbyterianchurch"
SQ = "https://gdnj.org"
# 시험 기간에는 검색엔진에 노출되지 않게 한다. gdnj.org로 정식 오픈할 때 False로 바꾼다.
NOINDEX = True

NAV = [
    ("about", "about.html", "교회소개"),
    ("worship", "worship.html", "예배안내"),
    ("sermon", "sermon.html", "설교"),
    ("nextgen", "nextgen.html", "다음세대"),
    ("growth", "growth.html", "양육·훈련"),
    ("serve", "serve.html", "섬김과 나눔"),
    ("news", "news.html", "소식·나눔"),
]

PLAYLISTS = {
    "acts": ("PLUlfTRUR0ID8bLiu5DGxMZzevg2T7thh9", "사도행전", "주일설교 강해"),
    "ezra": ("PLUlfTRUR0ID-xS2mMtXA4EhIqpHyg4np0", "에스라", "수요말씀 강해"),
    "ruth": ("PLUlfTRUR0ID9u3sStKqzhYlJZOVanLfY_", "룻기", "수요말씀 강해"),
    "life": ("PLUlfTRUR0ID9shp1vOGCir_5FGGhQCKcc", "성도의 신앙생활", "주일설교"),
    "special": ("PLUlfTRUR0ID_sLjcd1SNB4IVSEwv725ca", "특별설교", "주일설교"),
    "feast": ("PLUlfTRUR0ID9t413PAJhF1cQ7QFDK0UZC", "특별예배", "절기 · 특별예배"),
    "service": ("PLUlfTRUR0ID-DLi0O5fEOoOQq1-qlNTGq", "주일예배", "예배 전체 영상"),
}

# ------------------------------------------------------------------ YouTube
def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8")

def feed(kind, ident):
    q = "channel_id" if kind == "channel" else "playlist_id"
    try:
        xml = fetch(f"https://www.youtube.com/feeds/videos.xml?{q}={ident}")
    except Exception as e:  # RSS가 막혔으면(2026-10 유튜브 변경) 페이지에서 직접 읽는다
        print("  ! RSS 실패 → 페이지에서 직접 읽기:", ident)
        return scrape(kind, ident)
    out = []
    for vid, title, pub in re.findall(r"<yt:videoId>(.*?)</yt:videoId>.*?<title>(.*?)</title>.*?<published>(.*?)</published>", xml, re.S):
        out.append(parse(vid, html.unescape(title), pub[:10]))
    return out if out else scrape(kind, ident)

def scrape(kind, ident):
    """RSS 대신 유튜브 페이지에서 영상 ID와 제목을 직접 긁어온다 (2026-10 구조: lockupViewModel).
    날짜는 제목의 [YYYY-MM-DD]에서 얻으므로, 날짜 표기가 없는 영상은 건너뛴다."""
    if kind == "playlist":
        urls = [f"https://www.youtube.com/playlist?list={ident}"]
    else:
        urls = [f"https://www.youtube.com/channel/{ident}/videos",
                f"https://www.youtube.com/channel/{ident}/streams"]
    seen, out = set(), []
    for url in urls:
        try:
            page = fetch(url)
        except Exception as e:
            print("  ! 페이지 실패:", url, e)
            continue
        for chunk in page.split('"lockupViewModel":')[1:]:
            vm = re.search(r'"contentId":"([\w-]{11})"', chunk)
            tm = re.search(r'"lockupMetadataViewModel":\{"title":\{"content":"((?:[^"\\]|\\.)*)"', chunk)
            if not vm or not tm:
                continue
            vid = vm.group(1)
            if vid in seen:
                continue
            try:
                raw = json.loads('"' + tm.group(1) + '"')  # \uXXXX, \" 등을 원래 글자로
            except Exception:
                continue
            if not re.search(r"\[\d{4}-\d{2}-\d{2}\]", raw):
                continue  # 날짜 없는 영상(예고편 등)은 목록에서 제외
            seen.add(vid)
            out.append(parse(vid, raw, ""))
    out.sort(key=lambda v: v["date"], reverse=True)
    return out

def parse(vid, raw, pub):
    """'[2026-09-27] 뉴저지 길된교회 주일설교 (사도행전 6:8-15) “제목” 박승환 목사' 를 쪼갠다."""
    d = re.search(r"\[(\d{4}-\d{2}-\d{2})\]", raw)
    date = d.group(1) if d else pub
    passage = re.search(r"\(([^)]*\d[^)]*)\)", raw)
    title = re.search(r"[“\"]([^”\"]+)[”\"]", raw)
    after = raw[title.end():].strip() if title else ""
    kind = re.sub(r"^\[.*?\]\s*(뉴저지\s*)?길된교회\s*", "", raw.split("(")[0]).strip()
    return {
        "id": vid, "raw": raw, "date": date, "kind": kind,
        "passage": passage.group(1).strip() if passage else "",
        "title": title.group(1).strip() if title else raw,
        "preacher": after,
    }

def kdate(s):
    y, m, d = s.split("-")
    return f"{int(y)}. {int(m)}. {int(d)}"

PLAY = '<div class="play"><span><svg width="22" height="22" viewBox="0 0 24 24" fill="#000"><path d="M8 5v14l11-7z"/></svg></span></div>'

def watch(v):
    return f"https://www.youtube.com/watch?v={v['id']}"

def thumb(v, q="hqdefault"):
    return f"https://i.ytimg.com/vi/{v['id']}/{q}.jpg"

def yt_card(v, extra=""):
    t = html.escape(v["title"]); p = html.escape(v["passage"]); who = html.escape(v["preacher"])
    return (f'<a class="yt reveal" href="{watch(v)}" target="_blank" rel="noopener" title="{html.escape(v["raw"])}">'
            f'<div class="th"><img loading="lazy" src="{thumb(v)}" alt="{t}">{PLAY}</div>'
            f'<div><div class="meta"><span>{kdate(v["date"])}</span>{extra}</div>'
            f'<h3>{t}</h3><p>{p}{" · " + who if who else ""}</p></div></a>')

def yt_feature(v):
    t = html.escape(v["title"])
    return (f'<div class="yt-feature reveal"><a class="yt" href="{watch(v)}" target="_blank" rel="noopener">'
            f'<div class="th"><img src="{thumb(v, "maxresdefault")}" onerror="this.src=\'{thumb(v)}\'" alt="{t}">{PLAY}</div></a>'
            f'<div><span class="tag tag-dark">최신 설교</span><h3>{t}</h3>'
            f'<p class="sub">{html.escape(v["passage"])} · {html.escape(v["preacher"])}</p>'
            f'<p class="muted" style="margin-top:6px">{kdate(v["date"])} · {html.escape(v["kind"])}</p>'
            f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:28px">'
            f'<a class="btn btn-black btn-md" href="{watch(v)}" target="_blank" rel="noopener">'
            f'<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>유튜브에서 보기</a>'
            f'<a class="btn btn-line btn-md" href="{YT}" target="_blank" rel="noopener">채널 전체 보기</a></div></div></div>')

def pl_card(key, first):
    pid, name, desc = PLAYLISTS[key]
    img = thumb(first) if first else ""
    return (f'<a class="pl-card reveal" href="https://www.youtube.com/playlist?list={pid}" target="_blank" rel="noopener">'
            f'<img loading="lazy" src="{img}" alt=""><div class="tx"><small>PLAYLIST</small><b>{name}</b><span>{desc} →</span></div></a>')

def sermon_blocks():
    print("· 유튜브 RSS 받는 중…")
    ch = feed("channel", CHANNEL)
    pls = {k: feed("playlist", v[0]) for k, v in PLAYLISTS.items()}
    def merged(sources, key):
        seen, out = set(), []
        for v in sorted((v for s in sources for v in s), key=lambda v: v["date"], reverse=True):
            if key in v["kind"] and v["id"] not in seen:
                seen.add(v["id"]); out.append(v)
        return out
    sunday = merged([ch, pls["acts"], pls["special"], pls["life"]], "주일설교")
    wed = merged([ch, pls["ezra"], pls["ruth"]], "수요")
    # 안전장치: 유튜브 접속이 막혀 목록이 비면, 빈 목록으로 사이트를 덮어쓰지 않고 중단한다.
    if not sunday or not wed:
        raise SystemExit("! 설교 목록을 받아오지 못했습니다 (유튜브 접속 실패 가능성). 사이트를 바꾸지 않고 중단합니다.")
    latest = sunday[0] if sunday else (ch[0] if ch else None)
    blocks = {
        "SERMON_FEATURE": yt_feature(latest) if latest else "",
        "SERMON_SUNDAY": "".join(yt_card(v) for v in sunday[:12]),
        "SERMON_WED": "".join(yt_card(v) for v in wed[:12]),
        "SERMON_SPECIAL": "".join(yt_card(v, f'<span class="tag" style="padding:1px 8px;font-size:11.5px">{html.escape(v["kind"])}</span>') for v in pls["feast"][:4]),
        "SERMON_PLAYLISTS": "".join(pl_card(k, (pls[k] or [None])[0]) for k in ["acts", "ezra", "ruth", "life", "special", "service"]),
        "HOME_LATEST": yt_card(latest) if latest else "",
        "HOME_LATEST_WED": yt_card(wed[0]) if wed else "",
    }
    print(f"  주일설교 {len(sunday)}개 · 수요 {len(wed)}개 · 특별예배 {len(pls['feast'])}개")
    return blocks

# ------------------------------------------------------------------ layout
ICON = {
    "ig": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor"/></svg>',
    "yt": '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M23 7.2a3 3 0 00-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 001 7.2 31 31 0 00.5 12a31 31 0 00.5 4.8 3 3 0 002.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 002.1-2.1 31 31 0 00.5-4.8 31 31 0 00-.5-4.8zM9.7 15.1V8.9L15.2 12z"/></svg>',
    "kakao": '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 3C6.5 3 2 6.6 2 11c0 2.8 1.9 5.3 4.7 6.7l-1 3.6c-.1.3.3.6.6.4l4.2-2.8c.5.1 1 .1 1.5.1 5.5 0 10-3.6 10-8S17.5 3 12 3z"/></svg>',
}

def header(active):
    act = ' class="active"'
    items = "".join(f'<a href="{h}"{act if k == active else ""}>{n}</a>' for k, h, n in NAV)
    return f'''<header class="nav">
  <div class="wrap">
    <a href="index.html" class="logo" aria-label="길된교회 홈"><span class="logo-mark">길</span><span>길된교회<small>GIL DOEN PRESBYTERIAN</small></span></a>
    <nav class="menu" aria-label="주 메뉴">{items}</nav>
    <div class="nav-right">
      <a class="btn btn-black btn-sm" href="worship.html#live"><span class="live-dot"></span>생방송 예배</a>
      <button class="hamburger" aria-label="메뉴 열기" aria-expanded="false" id="hamburger"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
    </div>
  </div>
  <div class="mobile-menu" id="mobileMenu">{items}<a href="worship.html#live">생방송 예배</a></div>
</header>'''

FOOTER = f'''<footer>
  <div class="wrap">
    <div class="foot">
      <div>
        <a href="index.html" class="logo"><span class="logo-mark">길</span><span>길된교회<small>GIL DOEN PRESBYTERIAN</small></span></a>
        <div class="addr">12 W Central Ave, Bergenfield, NJ 07621<br><a href="mailto:gdpc.org@gmail.com">gdpc.org@gmail.com</a></div>
        <div class="social">
          <a href="https://www.instagram.com/gil.doen_official/" target="_blank" rel="noopener" aria-label="Instagram">{ICON["ig"]}</a>
          <a href="{YT}" target="_blank" rel="noopener" aria-label="YouTube">{ICON["yt"]}</a>
          <a href="https://pf.kakao.com/_xiVtQn" target="_blank" rel="noopener" aria-label="KakaoTalk">{ICON["kakao"]}</a>
        </div>
      </div>
      <div><h5>교회소개</h5><ul><li><a href="about.html#church">주님의 교회</a></li><li><a href="about.html#dna">길된교회 DNA</a></li><li><a href="about.html#staff">섬기는 이들</a></li><li><a href="about.html#directions">오시는 길</a></li></ul></div>
      <div><h5>예배 · 설교</h5><ul><li><a href="worship.html#times">예배 시간</a></li><li><a href="worship.html#live">생방송 예배</a></li><li><a href="sermon.html">설교</a></li><li><a href="worship.html#offering">온라인 헌금</a></li></ul></div>
      <div><h5>공동체</h5><ul><li><a href="nextgen.html">다음세대</a></li><li><a href="growth.html">양육 · 훈련</a></li><li><a href="serve.html">섬김과 나눔</a></li><li><a href="worship.html#newcomer">새가족 안내</a></li></ul></div>
      <div><h5>소식</h5><ul><li><a href="news.html#bulletin">주보</a></li><li><a href="news.html#gallery">갤러리</a></li><li><a href="news.html#board">온라인 게시판</a></li><li><a href="serve.html#apply">신청하기</a></li></ul></div>
    </div>
    <div class="copyright"><span>© 2026 Gil Doen Presbyterian Church. All rights reserved.</span><span>광야에 길을, 사막에 강을 — 이사야 43:19</span></div>
  </div>
</footer>'''

def subnav(title, items):
    links = "".join(f'<a href="#{i}">{n}</a>' for i, n in items)
    return f'<div class="subnav"><div class="wrap"><span class="title">{title}</span>{links}</div></div>'

def asset_version(rel):
    """파일 내용이 바뀌면 주소 뒤 버전 번호도 바뀌게 해서, 브라우저가 옛 파일을 쓰지 않게 한다."""
    import hashlib
    with open(os.path.join(ROOT, rel), "rb") as f:
        return f"{rel}?v={hashlib.md5(f.read()).hexdigest()[:8]}"

def page(meta, body):
    css, js = asset_version("assets/site.css"), asset_version("assets/site.js")
    sn = subnav(meta["title"], meta["subnav"]) if meta.get("subnav") else ""
    t = "길된교회 | Gil Doen Presbyterian Church" if meta["active"] == "home" else f'{meta["title"]} | 길된교회'
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t}</title>
<meta name="description" content="{html.escape(meta.get("desc", "뉴저지 버겐필드 길된교회 — 광야에 길을, 사막에 강을 내시는 주님을 찬송합니다."))}">
{'<meta name="robots" content="noindex, nofollow">' if NOINDEX else ''}
<meta name="site-version" content="__SITEVER__">
<script>document.documentElement.classList.add('js');
(function(){{var cur='__SITEVER__';fetch('version.json?t='+Date.now(),{{cache:'no-store'}}).then(function(r){{return r.json()}}).then(function(d){{
if(d.v&&d.v!==cur){{var u=new URL(location.href);if(u.searchParams.get('v')!==d.v){{u.searchParams.set('v',d.v);location.replace(u.toString())}}}}}}).catch(function(){{}})}})();</script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="{css}">
</head>
<body>
{header(meta["active"])}
<main>
{sn}
{body}
</main>
{FOOTER}
<script src="{js}"></script>
</body>
</html>
'''

def main():
    import hashlib
    blocks = sermon_blocks()
    out = {}
    for fn in sorted(os.listdir(PAGES)):
        if not fn.endswith(".html"):
            continue
        src = open(os.path.join(PAGES, fn), encoding="utf-8").read()
        m = re.match(r"\s*<!--META(.*?)-->", src, re.S)
        meta = json.loads(m.group(1)); body = src[m.end():]
        body = body.replace("{{SQ}}", SQ).replace("{{YT}}", YT)
        for k, v in blocks.items():
            body = body.replace("{{" + k + "}}", v)
        left = re.findall(r"\{\{[A-Z_]+\}\}", body)
        if left:
            print("  ! 남은 자리표시:", fn, left)
        out[fn] = page(meta, body)
    # 사이트 안 링크에 버전 번호를 붙인다. 내용이 바뀌면 번호도 바뀌어서,
    # 브라우저가 예전에 저장해 둔 페이지를 다시 쓰지 않는다.
    ver = hashlib.md5("".join(out[k] for k in sorted(out)).encode()).hexdigest()[:8]
    names = "|".join(re.escape(k) for k in out)
    link = re.compile(r'href="(' + names + r')(#[^"]*)?"')
    for fn, text in out.items():
        text = link.sub(lambda mm: f'href="{mm.group(1)}?v={ver}{mm.group(2) or ""}"', text)
        text = text.replace("__SITEVER__", ver)
        open(os.path.join(ROOT, fn), "w", encoding="utf-8").write(text)
        print("✓", fn)
    open(os.path.join(ROOT, "version.json"), "w").write(json.dumps({"v": ver}))
    print("  버전:", ver)

if __name__ == "__main__":
    main()

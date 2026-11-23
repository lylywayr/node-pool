#!/usr/bin/env python3
"""
sync.py — 汇总 Darlene-Alderson-FSOCIETY 三个 gist 的节点，
统一成标准分享链接 + Clash / sing-box / Surge 四种配置。

无第三方依赖，Python 3.9+。本地: python3 sync.py    CI: 由 workflow 调用。
"""
import os, re, json, base64, time, socket, datetime, urllib.request, urllib.parse as up

GISTS = [
    "86fa5f2ad8ff17c182f4009c87c0911b",
    "2b6bd8622af25a1da773d549937cf713",
    "81fc656cd0a8298a5aad99c7cfadcd97",
]
OWNER = "Darlene-Alderson-FSOCIETY"
OUT = "sub"
UA = {"User-Agent": "Mozilla/5.0 (compatible; node-pool-sync/1.0)", "Accept": "application/vnd.github+json"}
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

FLAG_CC = {
    "ZW": "🇿🇼", "NL": "🇳🇱", "DE": "🇩🇪", "RU": "🇷🇺", "US": "🇺🇸", "SG": "🇸🇬", "JP": "🇯🇵",
    "HK": "🇭🇰", "TW": "🇹🇼", "KR": "🇰🇷", "FR": "🇫🇷", "GB": "🇬🇧", "UK": "🇬🇧", "CA": "🇨🇦",
    "FI": "🇫🇮", "SE": "🇸🇪", "CH": "🇨🇭", "AT": "🇦🇹", "IT": "🇮🇹", "ES": "🇪🇸", "PL": "🇵🇱",
    "TR": "🇹🇷", "IR": "🇮🇷", "IN": "🇮🇳", "ID": "🇮🇩", "MY": "🇲🇾", "TH": "🇹🇭", "VN": "🇻🇳",
    "AU": "🇦🇺", "BR": "🇧🇷", "AR": "🇦🇷", "MX": "🇲🇽", "ZA": "🇿🇦", "AE": "🇦🇪", "IL": "🇮🇱",
    "UA": "🇺🇦", "CZ": "🇨🇿", "RO": "🇷🇴", "HU": "🇭🇺", "BG": "🇧🇬", "LT": "🇱🇹", "LV": "🇱🇻",
    "EE": "🇪🇪", "NO": "🇳🇴", "DK": "🇩🇰", "BE": "🇧🇪", "IE": "🇮🇪", "PT": "🇵🇹", "GR": "🇬🇷",
    "MD": "🇲🇩", "KZ": "🇰🇿", "BY": "🇧🇾", "AM": "🇦🇲", "GE": "🇬🇪", "AZ": "🇦🇿", "SA": "🇸🇦",
    "QA": "🇶🇦", "KW": "🇰🇼", "EG": "🇪🇬", "NG": "🇳🇬", "KE": "🇰🇪", "CL": "🇨🇱", "PE": "🇵🇪",
    "CO": "🇨🇴", "CR": "🇨🇷", "PA": "🇵🇦", "NZ": "🇳🇿", "PH": "🇵🇭", "PK": "🇵🇰", "BD": "🇧🇩",
    "LK": "🇱🇰", "NP": "🇳🇵", "MN": "🇲🇳", "HK ": "🇭🇰",
}
CITY_WORDS = {
    "amsterdam": "NL", "frankfurt": "DE", "moscow": "RU", "petersburg": "RU", "helsinki": "FI",
    "stockholm": "SE", "zurich": "CH", "vienna": "AT", "london": "GB", "paris": "FR",
    "warsaw": "PL", "istanbul": "TR", "tehran": "IR", "tokyo": "JP", "osaka": "JP",
    "seoul": "KR", "singapore": "SG", "hongkong": "HK", "hong kong": "HK", "taipei": "TW",
    "toronto": "CA", "miami": "US", "dallas": "US", "seattle": "US", "chicago": "US",
    "los angeles": "US", "new york": "US", "sydney": "AU", "melbourne": "AU",
}

# ---------- fetch ----------
def http(url, timeout=40, auth=False):
    hdr = dict(UA)
    if "api.github.com" not in url:
        # 网页端点必须用浏览器的 Accept，发 application/vnd.github+json 会被回 404
        hdr["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    req = urllib.request.Request(url, headers=hdr)
    # 只对 api.github.com 带 token；网页端点带 Bearer 会被 GitHub 回 404
    if auth and TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")

def gist_files(gid):
    """文件列表走网页解析，raw 走 gist.githubusercontent —— 全程不需要 API，避开限流/权限。"""
    out, seen = [], set()
    try:
        html = http(f"https://gist.github.com/{OWNER}/{gid}", timeout=40)
        for rev, fn in re.findall(r"raw/([0-9a-f]{40})/([A-Za-z0-9._%\-]+)", html):
            name = up.unquote(up.unquote(fn))
            if name in seen:
                continue
            seen.add(name)
            out.append((name, f"https://gist.githubusercontent.com/{OWNER}/{gid}/raw/{name}", None))
    except Exception as e:
        print("html scrape failed:", e)
    if not out:
        meta = json.loads(http(f"https://api.github.com/gists/{gid}", auth=True))
        out = [(n, f["raw_url"], f.get("size", 0)) for n, f in meta["files"].items()]
    return out

# ---------- geo (IP -> country) ----------
GEO_CACHE_FILE = ".geo-cache.json"
GEO_API = "http://ip-api.com/batch?fields=status,countryCode,query"
IS_IP = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")

def load_geo_cache():
    try:
        return json.load(open(GEO_CACHE_FILE, encoding="utf-8"))
    except Exception:
        return {}

def resolve_host(host):
    try:
        return socket.gethostbyname(host)
    except Exception:
        return ""

def geo_lookup(ips):
    """批量查 IP 归属国，结果落到 .geo-cache.json，避免每次全量重查。"""
    cache = load_geo_cache()
    todo = [ip for ip in ips if ip not in cache]
    for i in range(0, len(todo), 50):
        chunk = todo[i:i + 50]
        body = json.dumps([{"query": ip} for ip in chunk]).encode()
        rows = None
        for attempt in range(3):
            req = urllib.request.Request(GEO_API, data=body,
                                         headers={"Content-Type": "application/json", **UA})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    rows = json.loads(r.read().decode())
                break
            except Exception as e:
                print("geo lookup retry", attempt + 1, ":", e)
                time.sleep(8)
        if rows:
            for row in rows:
                q = row.get("query", "")
                if not q:
                    continue
                cache[q] = (row.get("countryCode") or "") if row.get("status") == "success" else ""
        time.sleep(4.5)  # 免费额度 15 次/分钟
    json.dump(cache, open(GEO_CACHE_FILE, "w", encoding="utf-8"), ensure_ascii=False, sort_keys=True)
    return cache

# ---------- helpers ----------
def b64d(s):
    s = re.sub(r"\s+", "", s)
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def b64e(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

def flag_cc(text):
    for ch in text:
        if 0x1F1E6 <= ord(ch) <= 0x1F1FF:
            pass
    m = re.findall(r"[\U0001F1E6-\U0001F1FF]{2}", text)
    if m:
        cc = "".join(chr(ord(c) - 0x1F1E6 + ord("A")) for c in m[0])
        return cc
    for w, cc in CITY_WORDS.items():
        if w in text.lower():
            return cc
    m = re.search(r"\b([A-Z]{2})\b", text)
    if m and m.group(1) in FLAG_CC:
        return m.group(1)
    return "XX"

EN_CODES = set("""HK MO TW JP KR SG US GB FR DE AU AE AF AL DZ AO AR AM AT AZ BH BD BY BE BZ BJ BT BO BA BW BR VG BN BG BF BI KH CM CA CV KY CF TD CL CO KM CG CD CR HR CY CZ DK DJ DO EC EG SV GQ ER EE ET FJ FI GA GM GE GH GR GL GT GN GY HT HN HU IS IN ID IR IQ IE IM IL IT CI JM JO KZ KE KW KG LA LV LB LS LR LY LT LU MK MG MW MY MV ML MT MR MU MX MD MC MN ME MA MZ MM NA NP NL NZ NI NE NG KP NO OM PK PA PY PE PH PT PR QA RO RU RW SM SA SN RS SL SK SI SO ZA ES LK SD SR SZ SE CH SY TJ TZ TH TG TO TT TN TR TM VI UG UA UY UZ VE VN YE ZM ZW AD RE PL GU VA LI CW SC AQ GI CU FO AX BM TL""".split())

STEM_CC = {
    "swed": "SE", "sver": "SE", "norw": "NO", "dan": "DK", "fin": "FI", "ger": "DE",
    "deut": "DE", "neth": "NL", "holl": "NL", "belg": "BE", "fran": "FR", "ital": "IT",
    "espa": "ES", "port": "PT", "pol": "PL", "czech": "CZ", "slov": "SK", "hung": "HU",
    "roma": "RO", "bulg": "BG", "gree": "GR", "turk": "TR", "ukr": "UA", "russ": "RU",
    "bela": "BY", "lith": "LT", "latv": "LV", "esto": "EE", "mold": "MD", "geor": "GE",
    "arme": "AM", "azer": "AZ", "kaza": "KZ", "uzbe": "UZ", "kirg": "KG", "taji": "TJ",
    "mong": "MN", "chin": "CN", "japa": "JP", "kore": "KR", "sing": "SG", "indi": "IN",
    "thai": "TH", "viet": "VN", "indo": "ID", "mala": "MY", "phil": "PH", "camb": "KH",
    "laos": "LA", "myan": "MM", "aust": "AU", "zea": "NZ", "braz": "BR", "arge": "AR",
    "chile": "CL", "peru": "PE", "colo": "CO", "mexi": "MX", "egyp": "EG", "sout": "ZA",
    "nige": "NG", "keny": "KE", "moro": "MA", "isra": "IL", "iran": "IR", "iraq": "IQ",
    "jord": "JO", "leba": "LB", "kuwa": "KW", "oman": "OM", "bahra": "BH", "qata": "QA",
    "cypr": "CY", "malt": "MT", "icel": "IS", "irel": "IE", "croa": "HR", "serb": "RS",
    "slove": "SI", "bosn": "BA", "mont": "ME", "alba": "AL", "mace": "MK", "luxe": "LU",
    "cana": "CA", "amer": "US",
}

CC_TLD = {k: v for k, v in {
    "hk": "HK", "tw": "TW", "mo": "MO", "jp": "JP", "kr": "KR", "sg": "SG", "cn": "CN",
    "ru": "RU", "ir": "IR", "de": "DE", "nl": "NL", "fr": "FR", "uk": "GB", "it": "IT",
    "es": "ES", "pl": "PL", "se": "SE", "fi": "FI", "no": "NO", "dk": "DK", "ch": "CH",
    "at": "AT", "be": "BE", "cz": "CZ", "ro": "RO", "ua": "UA", "kz": "KZ", "vn": "VN",
    "th": "TH", "id": "ID", "my": "MY", "ph": "PH", "in": "IN", "au": "AU", "nz": "NZ",
    "br": "BR", "mx": "MX", "ar": "AR", "tr": "TR", "ae": "AE", "sa": "SA", "il": "IL",
    "gr": "GR", "pt": "PT", "hu": "HU", "bg": "BG", "hr": "HR", "rs": "RS", "lt": "LT",
    "lv": "LV", "ee": "EE", "md": "MD", "by": "BY", "ge": "GE", "am": "AM", "az": "AZ",
    "uz": "UZ", "kg": "KG", "tj": "TJ", "tm": "TM", "mn": "MN", "pk": "PK", "bd": "BD",
    "lk": "LK", "np": "NP", "kh": "KH", "la": "LA", "mm": "MM", "za": "ZA", "eg": "EG",
    "ng": "NG", "ke": "KE", "ma": "MA", "cl": "CL", "pe": "PE", "ec": "EC", "uy": "UY",
    "py": "PY", "bo": "BO", "cr": "CR", "pa": "PA", "pr": "PR", "do": "DO", "gt": "GT",
}.items() if v in EN_CODES}

FAKE_IP = re.compile(r"^198\.(1[89])\.")  # Surge fake-ip 段，不能拿去查归属地

def host_cc(host):
    """从主机名推国家：cc 标签 / cc-城市 / 词干 / 城市 / ccTLD"""
    host = (host or "").strip().lower().rstrip(".")
    if not host or IS_IP.match(host):
        return ""
    labels = host.split(".")
    best = None
    for i, label in enumerate(labels):
        cc, score = "", 0
        if re.fullmatch(r"[a-z]{2}", label) and label.upper() in EN_CODES:
            cc, score = label.upper(), 3
        elif re.fullmatch(r"[a-z]{2}(?:\d{1,3}|[-_](?:\d{1,3}|[a-z]{2,12}(?:[-_]?\d{1,3})?))", label):
            cc, score = label[:2].upper(), 2
        elif label in STEM_CC:
            cc, score = STEM_CC[label], 2
        else:
            for w, code in CITY_WORDS.items():
                if len(w) >= 5 and w in label:
                    cc, score = code, 2
                    break
        if cc and (best is None or score > best[0] or (score == best[0] and i > best[1])):
            best = (score, i, cc)
    if best:
        return best[2]
    return CC_TLD.get(labels[-1], "")

def flag_of(cc):
    if not cc or cc == "XX" or len(cc) != 2:
        return "🏴"
    return "".join(chr(0x1F1E6 + ord(c) - 65) for c in cc.upper())

def clean(s):
    s = re.sub(r"[,\r\n\t]+", " ", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return s[:50]

# ---------- parse ----------
def parse(link):
    sch = link.split("://", 1)[0].lower()
    if sch == "vless": return parse_vless(link)
    if sch == "vmess": return parse_vmess(link)
    if sch == "trojan": return parse_trojan(link)
    if sch in ("hysteria2", "hy2"): return parse_hy2(link)
    if sch == "ss": return parse_ss(link)
    return None

def parse_vless(link):
    u = up.urlparse(link)
    q = dict(up.parse_qsl(u.query))
    n = {"proto": "vless", "host": u.hostname, "port": u.port,
         "uuid": up.unquote(u.username or ""), "name_raw": up.unquote(u.fragment or "")}
    if not n["host"] or not n["port"] or not n["uuid"]: return None
    sec = (q.get("security") or "none").lower()
    n.update({"security": sec, "sni": q.get("sni") or q.get("host") or "",
              "pbk": q.get("pbk", ""), "sid": q.get("sid", ""), "flow": q.get("flow", ""),
              "net": (q.get("type") or "tcp").lower(), "path": up.unquote(q.get("path", "") or ""),
              "hosthdr": q.get("host", ""), "svc": up.unquote(q.get("serviceName", "") or ""),
              "mode": q.get("mode", ""), "alpn": up.unquote(q.get("alpn", "") or ""),
              "fp": q.get("fp", ""), "insecure": str(q.get("insecure", q.get("allowInsecure", "0"))) in ("1", "true"),
              "enc": q.get("encryption", "")})
    if sec == "reality" and not n["pbk"]: return None
    if n["net"] not in ("tcp", "raw", "ws", "grpc", "xhttp", "httpupgrade", "kcp"): return None
    if n["net"] == "kcp": return None
    return n

def parse_vmess(link):
    try:
        j = json.loads(b64d(link.split("vmess://", 1)[1]).decode("utf-8", "ignore"))
    except Exception:
        return None
    if not j.get("add") or not j.get("port") or not j.get("id"): return None
    tls = str(j.get("tls", "")).lower()
    return {"proto": "vmess", "host": j["add"], "port": int(j["port"]), "uuid": j["id"],
            "name_raw": j.get("ps", ""), "security": "tls" if tls in ("tls", "reality") else "none",
            "sni": j.get("sni") or j.get("host") or "", "net": str(j.get("net", "tcp")).lower(),
            "path": j.get("path", "") or "", "hosthdr": j.get("host", ""), "svc": j.get("path", "") if str(j.get("net")) == "grpc" else "",
            "alpn": j.get("alpn", "") or "", "aid": j.get("aid", 0), "insecure": False, "fp": ""}

def parse_trojan(link):
    u = up.urlparse(link)
    q = dict(up.parse_qsl(u.query))
    if not u.hostname or not u.port or not u.username: return None
    return {"proto": "trojan", "host": u.hostname, "port": u.port, "password": up.unquote(u.username),
            "name_raw": up.unquote(u.fragment or ""), "security": "tls",
            "sni": q.get("sni", ""), "net": (q.get("type") or "tcp").lower(),
            "path": up.unquote(q.get("path", "") or ""), "hosthdr": q.get("host", ""),
            "svc": q.get("serviceName", ""), "alpn": q.get("alpn", "") or "",
            "insecure": str(q.get("allowInsecure", q.get("insecure", "0"))) in ("1", "true")}

def parse_hy2(link):
    u = up.urlparse(link)
    q = dict(up.parse_qsl(u.query))
    pwd = up.unquote(u.username or "") or q.get("auth", "")
    if not u.hostname or not u.port or not pwd: return None
    return {"proto": "hysteria2", "host": u.hostname, "port": u.port, "password": pwd,
            "name_raw": up.unquote(u.fragment or ""), "security": "tls", "sni": q.get("sni", ""),
            "insecure": str(q.get("insecure", "0")) in ("1", "true"),
            "obfs": q.get("obfs", ""), "obfs_pwd": q.get("obfs-password", ""), "alpn": q.get("alpn", "") or ""}

def parse_ss(link):
    body = link.split("ss://", 1)[1]
    frag = ""
    if "#" in body:
        body, frag = body.split("#", 1)
    body = body.split("?")[0]
    if "@" in body:
        userinfo, hostport = body.rsplit("@", 1)
        try:
            method, _, pwd = b64d(userinfo).decode().partition(":")
        except Exception:
            return None
    else:
        try:
            method, _, rest = b64d(body).decode().partition(":")
        except Exception:
            return None
        pwd, _, hostport = rest.rpartition("@")
    host, _, port = hostport.rpartition(":")
    if not host or not port.isdigit(): return None
    return {"proto": "ss", "host": host, "port": int(port), "method": method, "password": pwd,
            "name_raw": up.unquote(frag), "security": "plain", "net": "tcp"}

# ---------- canonical share link ----------
def to_link(n, name):
    p = n["proto"]
    frag = "#" + up.quote(name, safe="")
    if p == "vless":
        q = [("encryption", n.get("enc", "none") or "none"), ("security", n["security"])]
        if n["sni"]: q.append(("sni", n["sni"]))
        if n.get("fp"): q.append(("fp", n["fp"]))
        if n["security"] == "reality":
            q += [("pbk", n["pbk"]), ("sid", n.get("sid", ""))]
        if n.get("flow"): q.append(("flow", n["flow"]))
        q.append(("type", "tcp" if n["net"] == "raw" else n["net"]))
        if n.get("hosthdr"): q.append(("host", n["hosthdr"]))
        if n.get("path"): q.append(("path", n["path"]))
        if n.get("svc"): q.append(("serviceName", n["svc"]))
        if n.get("mode"): q.append(("mode", n["mode"]))
        if n.get("alpn"): q.append(("alpn", n["alpn"]))
        if n.get("insecure"): q.append(("allowInsecure", "1"))
        qs = "&".join(f"{k}={up.quote(str(v), safe='')}" for k, v in q if v != "" or k == "sid")
        return f"vless://{up.quote(n['uuid'], safe='')}@{n['host']}:{n['port']}?{qs}{frag}"
    if p == "vmess":
        j = {"v": "2", "ps": name, "add": n["host"], "port": str(n["port"]), "id": n["uuid"],
             "aid": str(n.get("aid", 0)), "scy": "auto", "net": n["net"],
             "type": "none", "host": n.get("hosthdr", ""), "path": n.get("path", "") or n.get("svc", ""),
             "tls": n["security"] if n["security"] != "none" else "",
             "sni": n.get("sni", ""), "alpn": n.get("alpn", "")}
        return "vmess://" + base64.b64encode(json.dumps(j, ensure_ascii=False).encode()).decode()
    if p == "trojan":
        q = [("security", "tls"), ("type", n["net"])]
        if n["sni"]: q.append(("sni", n["sni"]))
        if n.get("path"): q.append(("path", n["path"]))
        if n.get("hosthdr"): q.append(("host", n["hosthdr"]))
        if n.get("svc"): q.append(("serviceName", n["svc"]))
        if n.get("alpn"): q.append(("alpn", n["alpn"]))
        if n.get("insecure"): q.append(("allowInsecure", "1"))
        qs = "&".join(f"{k}={up.quote(str(v), safe='')}" for k, v in q if v)
        return f"trojan://{up.quote(n['password'], safe='')}@{n['host']}:{n['port']}?{qs}{frag}"
    if p == "hysteria2":
        q = []
        if n["sni"]: q.append(("sni", n["sni"]))
        if n.get("obfs"): q += [("obfs", n["obfs"]), ("obfs-password", n.get("obfs_pwd", ""))]
        if n.get("insecure"): q.append(("insecure", "1"))
        if n.get("alpn"): q.append(("alpn", n["alpn"]))
        qs = "&".join(f"{k}={up.quote(str(v), safe='')}" for k, v in q if v)
        return f"hysteria2://{up.quote(n['password'], safe='')}@{n['host']}:{n['port']}" + (f"?{qs}" if qs else "") + frag
    if p == "ss":
        userinfo = b64e(f"{n['method']}:{n['password']}".encode())
        return f"ss://{userinfo}@{n['host']}:{n['port']}{frag}"
    return ""

# ---------- clash ----------
def clash_proxy(n, name):
    d = {"name": name, "type": n["proto"], "server": n["host"], "port": n["port"], "udp": True}
    p = n["proto"]
    if p == "vless":
        d.update({"uuid": n["uuid"], "tls": n["security"] in ("tls", "reality"), "client-fingerprint": n.get("fp") or "chrome",
                  "servername": n["sni"] or n["host"], "skip-cert-verify": True, "flow": n.get("flow") or ""})
        if n["security"] == "reality":
            d["reality-opts"] = {"public-key": n["pbk"], "short-id": n.get("sid", "")}
        d["network"] = "tcp" if n["net"] == "raw" else n["net"]
    elif p == "vmess":
        d.update({"uuid": n["uuid"], "alterId": int(n.get("aid") or 0), "cipher": "auto",
                  "tls": n["security"] == "tls", "servername": n["sni"] or n["host"], "skip-cert-verify": True,
                  "network": n["net"]})
    elif p == "trojan":
        d.update({"password": n["password"], "sni": n["sni"] or n["host"], "skip-cert-verify": True,
                  "network": n["net"]})
    elif p == "hysteria2":
        d.update({"password": n["password"], "sni": n["sni"] or n["host"], "skip-cert-verify": True})
        if n.get("obfs"):
            d["obfs"] = n["obfs"]; d["obfs-password"] = n.get("obfs_pwd", "")
        d.pop("udp", None)
    elif p == "ss":
        d.update({"cipher": n["method"], "password": n["password"]})
    net = n.get("net", "tcp")
    if net == "ws":
        opts = {"path": n.get("path") or "/"}
        if n.get("hosthdr"): opts["headers"] = {"Host": n["hosthdr"]}
        d["ws-opts"] = opts
    elif net == "httpupgrade":
        d["network"] = "ws"
        opts = {"path": n.get("path") or "/", "v2ray-http-upgrade": True}
        if n.get("hosthdr"): opts["headers"] = {"Host": n["hosthdr"]}
        d["ws-opts"] = opts
    elif net == "grpc":
        d["grpc-opts"] = {"grpc-service-name": n.get("svc", "")}
    elif net == "xhttp":
        d["xhttp-opts"] = {"path": n.get("path") or "/"}
        if n.get("hosthdr"): d["xhttp-opts"]["host"] = n["hosthdr"]
    if p in ("vless", "vmess") and n.get("alpn"):
        d["alpn"] = [a for a in n["alpn"].split(",") if a]
    if not d.get("flow"): d.pop("flow", None)
    return d

# ---------- sing-box ----------
def sb_outbound(n, name, tag):
    o = {"type": n["proto"], "tag": tag, "server": n["host"], "server_port": n["port"]}
    if n["proto"] == "vless":
        o.update({"uuid": n["uuid"], "packet_encoding": "xudp"})
        if n.get("flow"): o["flow"] = n["flow"]
    elif n["proto"] == "vmess":
        o.update({"uuid": n["uuid"], "security": "auto", "alter_id": int(n.get("aid") or 0)})
    elif n["proto"] == "trojan":
        o["password"] = n["password"]
    elif n["proto"] == "hysteria2":
        o["password"] = n["password"]
        o["tls"] = {"enabled": True, "server_name": n["sni"] or n["host"], "insecure": True,
                    "alpn": [a for a in (n.get("alpn") or "h3").split(",") if a]}
        if n.get("obfs"):
            o["obfs"] = {"type": n["obfs"], "password": n.get("obfs_pwd", "")}
        return o
    elif n["proto"] == "ss":
        o.update({"method": n["method"], "password": n["password"]})
        return o
    if n["security"] == "reality":
        o["tls"] = {"enabled": True, "server_name": n["sni"], "insecure": True,
                    "utls": {"enabled": True, "fingerprint": n.get("fp") or "chrome"},
                    "reality": {"enabled": True, "public_key": n["pbk"],
                                "short_id": n.get("sid", "")}}
    elif n["security"] == "tls":
        o["tls"] = {"enabled": True, "server_name": n["sni"] or n["host"], "insecure": True,
                    "utls": {"enabled": True, "fingerprint": n.get("fp") or "chrome"}}
        if n.get("alpn"): o["tls"]["alpn"] = [a for a in n["alpn"].split(",") if a]
    if n["net"] == "ws":
        o["transport"] = {"type": "ws", "path": n.get("path") or "/"}
        if n.get("hosthdr"): o["transport"]["headers"] = {"Host": n["hosthdr"]}
    elif n["net"] == "httpupgrade":
        o["transport"] = {"type": "httpupgrade", "path": n.get("path") or "/"}
        if n.get("hosthdr"): o["transport"]["headers"] = {"Host": n["hosthdr"]}
    elif n["net"] == "grpc":
        o["transport"] = {"type": "grpc", "service_name": n.get("svc", "")}
    elif n["net"] == "xhttp":
        o["transport"] = {"type": "xhttp", "path": n.get("path") or "/"}
        if n.get("hosthdr"): o["transport"]["host"] = n["hosthdr"]
        if n.get("mode"): o["transport"]["mode"] = n["mode"]
    return o

# ---------- surge ----------
def surge_line(n, name):
    p = n["proto"]
    if p == "vless":
        a = [f"username={n['uuid']}"]
        if n.get("flow"): a.append(f"flow={n['flow']}")
        if n["sni"]: a.append(f"sni={n['sni']}")
        if n["security"] == "reality":
            a.append(f"reality-public-key={n['pbk']}")
            if n.get("sid"): a.append(f"reality-short-id={n['sid']}")
        elif n["security"] == "tls":
            a.append("tls=true")
        if n["net"] == "ws":
            a += ["ws=true", f"ws-path={n.get('path') or '/'}"]
            if n.get("hosthdr"): a.append(f"ws-headers=Host:{n['hosthdr']}")
        elif n["net"] == "httpupgrade":
            a += ["ws=true", "ws-http-upgrade=true", f"ws-path={n.get('path') or '/'}"]
            if n.get("hosthdr"): a.append(f"ws-headers=Host:{n['hosthdr']}")
        elif n["net"] == "grpc":
            a += ["grpc=true", f"grpc-service-name={n.get('svc','')}"]
        elif n["net"] == "xhttp":
            a.append("xhttp=true"); a.append(f"xhttp-path={n.get('path') or '/'}")
            if n.get("hosthdr"): a.append(f"xhttp-host={n['hosthdr']}")
            if n.get("mode"): a.append(f"xhttp-mode={n['mode']}")
        if n["security"] == "tls" and n.get("insecure"): a.append("skip-cert-verify=true")
        if n.get("alpn"): a.append(f"alpn={n['alpn']}")
        return f"{name} = vless, {n['host']}, {n['port']}, " + ", ".join(a)
    if p == "vmess":
        a = [f"username={n['uuid']}"]
        if n["security"] == "tls": a.append("tls=true")
        if n["sni"]: a.append(f"sni={n['sni']}")
        if n["net"] == "ws":
            a += ["ws=true", f"ws-path={n.get('path') or '/'}"]
            if n.get("hosthdr"): a.append(f"ws-headers=Host:{n['hosthdr']}")
        elif n["net"] == "grpc":
            a += ["grpc=true", f"grpc-service-name={n.get('svc','')}"]
        return f"{name} = vmess, {n['host']}, {n['port']}, " + ", ".join(a)
    if p == "trojan":
        a = [f"password={n['password']}"]
        if n["sni"]: a.append(f"sni={n['sni']}")
        if n.get("insecure"): a.append("skip-cert-verify=true")
        if n["net"] == "ws":
            a += ["ws=true", f"ws-path={n.get('path') or '/'}"]
            if n.get("hosthdr"): a.append(f"ws-headers=Host:{n['hosthdr']}")
        return f"{name} = trojan, {n['host']}, {n['port']}, " + ", ".join(a)
    if p == "hysteria2":
        a = [f"password={n['password']}"]
        if n["sni"]: a.append(f"sni={n['sni']}")
        if n.get("insecure"): a.append("skip-cert-verify=true")
        if n.get("obfs"):
            a += [f"obfs={n['obfs']}", f"obfs-password={n.get('obfs_pwd','')}"]
        return f"{name} = hysteria2, {n['host']}, {n['port']}, " + ", ".join(a)
    if p == "ss":
        return f"{name} = ss, {n['host']}, {n['port']}, encrypt-method={n['method']}, password={n['password']}"
    return ""

# ---------- main ----------
def main():
    os.makedirs(OUT, exist_ok=True)
    raw, src_stat = [], {}
    for gid in GISTS:
        for fname, url, size in gist_files(gid):
            if not fname.endswith(".txt"):
                continue
            provider = re.sub(r"_Telegram_RE_s_B\.txt$|\.txt$", "", fname).strip()
            txt = http(url)
            if len(txt) < 200:
                continue
            n_before = len(raw)
            for m in re.finditer(r"([a-zA-Z0-9]+)://([^\s<>\"']+)", txt):
                sch = m.group(1).lower()
                if sch not in ("vless", "vmess", "trojan", "hysteria2", "hy2", "ss"):
                    continue
                link = f"{sch}://{m.group(2)}"
                try:
                    n = parse(link)
                except Exception:
                    n = None
                if n:
                    n["provider"] = provider
                    n["src_gist"] = gid[:8]
                    raw.append(n)
            src_stat[provider] = src_stat.get(provider, 0) + (len(raw) - n_before)
    # 过滤占位/无效端点
    raw = [n for n in raw if n["host"] not in ("0.0.0.0", "127.0.0.1", "::", "::1", "localhost")]

    # dedupe
    seen, nodes = set(), []
    for n in raw:
        key = (n["proto"], n["host"].lower(), n["port"],
               n.get("uuid") or n.get("password") or "", n["security"], n.get("pbk", ""), n.get("net", ""))
        if key in seen: continue
        seen.add(key)
        nodes.append(n)
    # 地区：节点名 -> 主机名 -> IP 归属地，依次兜底
    for n in nodes:
        cc = flag_cc(n.get("name_raw", ""))
        n["cc"] = cc if cc != "XX" else (host_cc(n["host"]) or "XX")

    ip_hosts = sorted({n["host"] for n in nodes if n["cc"] == "XX" and IS_IP.match(n["host"])})
    if ip_hosts:
        geo = geo_lookup(ip_hosts)
        for n in nodes:
            if n["cc"] == "XX" and geo.get(n["host"]):
                n["cc"] = geo[n["host"]]

    # 域名兜底：解析 A 记录后再查归属地
    domain_hosts = sorted({n["host"] for n in nodes if n["cc"] == "XX" and not IS_IP.match(n["host"])})
    if domain_hosts:
        host_ip = {h: resolve_host(h) for h in domain_hosts}
        ips2 = sorted({ip for ip in host_ip.values() if ip and not FAKE_IP.match(ip)})
        geo2 = geo_lookup(ips2) if ips2 else {}
        for n in nodes:
            if n["cc"] == "XX":
                cc = geo2.get(host_ip.get(n["host"], ""), "")
                if cc:
                    n["cc"] = cc

    # 排序后按地区重新连续编号
    nodes.sort(key=lambda n: (n["cc"], n["proto"], n["host"], n["port"]))
    counter = {}
    for n in nodes:
        counter[n["cc"]] = counter.get(n["cc"], 0) + 1
        n["name"] = clean(f"{flag_of(n['cc'])} {n['cc']}-{counter[n['cc']]:03d}")
    links = [to_link(n, n["name"]) for n in nodes]
    links = [l for l in links if l]
    open(f"{OUT}/nodes.txt", "w").write("\n".join(links) + "\n")
    open(f"{OUT}/v2ray.txt", "w").write(base64.b64encode("\n".join(links).encode()).decode())
    # clash
    lines = ["# Darlene gist pool — auto generated", "# https://github.com/%s" % os.environ.get("GITHUB_REPOSITORY", ""),
             "mixed-port: 7890", "allow-lan: true", "mode: rule", "log-level: info", "", "proxies:"]
    for n in nodes:
        d = clash_proxy(n, n["name"])
        body = ", ".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" if isinstance(v, (dict, bool, list)) else f"{k}: {v}"
                         for k, v in d.items())
        lines.append(f"  - {{{body}}}")
    names_yaml = json.dumps([n["name"] for n in nodes], ensure_ascii=False)
    lines += ["", "proxy-groups:", "  - name: 手动选择", "    type: select", "    proxies: " + names_yaml,
              "  - name: 自动测速", "    type: url-test", "    url: http://www.gstatic.com/generate_204",
              "    interval: 300", "    proxies: " + names_yaml,
              "", "rules:", "  - GEOIP,CN,DIRECT", "  - MATCH,自动测速", ""]
    open(f"{OUT}/clash.yaml", "w").write("\n".join(lines))
    # sing-box
    outs = [sb_outbound(n, n["name"], n["name"]) for n in nodes]
    cfg = {"log": {"level": "info"}, "inbounds": [{"type": "mixed", "tag": "mixed", "listen": "127.0.0.1", "listen_port": 2080}],
           "outbounds": outs + [{"type": "selector", "tag": "手动选择", "outbounds": [o["tag"] for o in outs] + ["自动测速"]},
                                {"type": "urltest", "tag": "自动测速", "outbounds": [o["tag"] for o in outs],
                                 "url": "http://www.gstatic.com/generate_204", "interval": "5m"}]}
    json.dump(cfg, open(f"{OUT}/singbox.json", "w"), ensure_ascii=False, indent=1)
    # surge
    sg = ["# Darlene gist pool — Surge 6 (VLESS/REALITY 需 iOS 6.0+)", "# " + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "", "[Proxy]"]
    sg += [surge_line(n, n["name"]) for n in nodes]
    sg += ["", "[Proxy Group]", "手动选择 = select, " + ", ".join(n["name"] for n in nodes),
           "自动测速 = url-test, " + ", ".join(n["name"] for n in nodes) + ", url=http://www.gstatic.com/generate_204, interval=300",
           "", "[Rule]", "GEOIP,CN,DIRECT", "FINAL,自动测速", ""]
    open(f"{OUT}/surge.conf", "w").write("\n".join(sg))
    # README
    from collections import Counter
    pc = Counter(n["proto"] for n in nodes); cc = Counter(n["cc"] for n in nodes)
    sec = Counter(n["security"] for n in nodes)
    top = "\n".join(f"| {k} | {v} |" for k, v in cc.most_common(15))
    readme = f"""# node-pool

从 [@Darlene-Alderson-FSOCIETY](https://gist.github.com/{OWNER}) 的三个 gist 自动汇总，统一改写成标准分享链接，并生成 Clash / sing-box / Surge 配置。
由 GitHub Actions 每 6 小时同步一次。

- 更新时间：{datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
- 节点总数：**{len(nodes)}**（去重后，单源 {len(raw)} 条）
- 协议：{', '.join(f'{k} {v}' for k, v in pc.most_common())}
- 安全层：{', '.join(f'{k} {v}' for k, v in sec.most_common())}

## 文件

| 文件 | 用途 |
| --- | --- |
| `sub/nodes.txt` | 标准分享链接，一行一条 |
| `sub/v2ray.txt` | 上面那份的 Base64（v2rayN / Shadowrocket 订阅格式） |
| `sub/clash.yaml` | mihomo / Clash Meta（REALITY 用 `reality-opts`） |
| `sub/singbox.json` | sing-box 1.10+ |
| `sub/surge.conf` | Surge 6（VLESS/REALITY 需 iOS 6.0.0+） |

## 订阅地址

```
https://raw.githubusercontent.com/{os.environ.get('GITHUB_REPOSITORY','OWNER/REPO')}/main/sub/v2ray.txt
https://raw.githubusercontent.com/{os.environ.get('GITHUB_REPOSITORY','OWNER/REPO')}/main/sub/clash.yaml
https://raw.githubusercontent.com/{os.environ.get('GITHUB_REPOSITORY','OWNER/REPO')}/main/sub/singbox.json
```

## 地区分布

| 地区 | 数量 |
| --- | --- |
{top}

## 说明

节点来自公开 Telegram 频道 @RE_s_B 的镜像，属公共共享资源，随时可能失效；不要在上面登录重要账号。
配置为机器生成，`sync.py` 是唯一源文件。
"""
    open("README.md", "w").write(readme)
    print(f"nodes={len(nodes)} raw={len(raw)} links={len(links)}")
    print("provider:", src_stat)
    print("proto:", dict(pc))

if __name__ == "__main__":
    main()

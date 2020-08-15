import json
import datetime
import time
import requests
from xml.dom.minidom import parseString
request_settings = {
    "use_https": True,
    "proxies": None
}
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/79.0.3945.130 Safari/537.36",
    "Referer": "https://www.bilibili.com/"
}
MESSAGES = {
    "no_sess": "需要提供：SESSDATA（Cookies里头的`SESSDATA`键对应的值）",
    "no_csrf": "需要提供：csrf（Cookies里头的`bili_jct`键对应的值）"
}
class BilibiliApiException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg
class NoPermissionException(BilibiliApiException):
    def __init__(self, msg="无操作权限"):
        self.msg = msg
class BilibiliException(BilibiliApiException):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
    def __str__(self):
        return "错误代码：%s, 信息：%s" % (self.code, self.msg)
class NetworkException(BilibiliApiException):
    def __init__(self, code):
        self.code = code
    def __str__(self):
        return "网络错误。状态码：%s" % self.code
class NoIdException(BilibiliApiException):
    def __init__(self):
        self.msg = "aid和bvid请至少提供一个"
class LiveException(BilibiliApiException):
    def __init__(self, msg: str):
        super().__init__(msg)
class Color(object):
    def __init__(self, hex_: str = "FFFFFF"):
        self.__color = 0
        self.set_hex_color(hex_)
    def set_hex_color(self, hex_color: str):
        if len(hex_color) == 3:
            hex_color = "".join([x + "0" for x in hex_color])
        dec = int(hex_color, 16)
        self.__color = dec
    def set_rgb_color(self, r: int, g: int, b: int):
        if not all([0 <= r < 256, 0 <= g < 256, 0 <= b < 256]):
            raise ValueError("值范围0~255")
        self.__color = (r << 8*2) + (g << 8) + b
    def set_dec_color(self, color: int):
        if 0 <= int(color) <= 16777215:
            self.__color = color
        else:
            raise ValueError("范围0~16777215")
    def get_hex_color(self):
        h = hex(int(self.__color)).lstrip("0x")
        h = "0" * (6 - len(h)) + h
        return h
    def get_rgb_color(self):
        h = hex(int(self.__color)).lstrip("0x")
        h = "0" * (6 - len(h)) + h
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        return r, g, b
    def get_dec_color(self):
        return self.__color
    def __str__(self):
        return self.get_hex_color()
class Danmaku(object):
    FONT_SIZE_SMALL = 18
    FONT_SIZE_BIG = 36
    FONT_SIZE_NORMAL = 25
    MODE_FLY = 1
    MODE_TOP = 5
    MODE_BOTTOM = 4
    def __init__(self, text: str, dm_time: float = 0.0, send_time: float = time.time(), crc32_id: str = None
                 , color: Color = None,
                 mode: int = MODE_FLY, font_size: int = FONT_SIZE_NORMAL, is_sub: bool = False):
        self.dm_time = datetime.timedelta(seconds=dm_time)
        self.send_time = datetime.datetime.fromtimestamp(send_time)
        self.crc32_id = crc32_id
        self.uid = None
        self.color = color if color else Color()
        self.mode = mode
        self.font_size = font_size
        self.is_sub = is_sub
        self.text = text
    def __str__(self):
        ret = "%s, %s, %s" % (self.send_time, self.dm_time, self.text)
        return ret
    def __len__(self):
        return len(self.text)
class Verify(object):
    def __init__(self, sessdata: str = None, csrf: str = None):
        self.sessdata = sessdata
        self.csrf = csrf
    def get_cookies(self):
        cookies = {}
        if self.has_sess():
            cookies["SESSDATA"] = self.sessdata
        if self.has_csrf():
            cookies["bili_jct"] = self.csrf
        return cookies
    def has_sess(self):
        if self.sessdata is None:
            return False
        else:
            return True
    def has_csrf(self):
        if self.csrf is None:
            return False
        else:
            return True
    def check(self):
        ret = {
            "code": -2,
            "message": ""
        }
        if not self.has_sess():
            ret["code"] = -3
            ret["message"] = "未提供SESSDATA"
        else:
            api = "https://api.bilibili.com/x/web-interface/online?&;;jsonp=jsonp"
            req = requests.post(url=api, cookies=self.get_cookies())
            if req.ok:
                con = req.json()
                if con["code"] == -111:
                    ret["code"] = -1
                    ret["message"] = "csrf 校验失败"
                elif con["code"] == -101 or con["code"] == -400:
                    ret["code"] = -2
                    ret["message"] = "SESSDATA值有误"
                else:
                    ret["code"] = 0
                    ret["message"] = "0"
            else:
                raise NetworkException(req.status_code)
        return ret
def request(method: str, url: str, params=None, data=None, cookies=None, headers=None, **kwargs):
    st = {
        "url": url,
        "params": params,
        "cookies": cookies,
        "headers": DEFAULT_HEADERS if headers is None else headers,
        "verify": request_settings["use_https"],
        "data": data,
        "proxies": request_settings["proxies"]
    }
    st.update(kwargs)
    req = requests.request(method, **st)
    if req.ok:
        content = req.content.decode("utf8")
        if req.headers.get("content-length") == 0:
            return None
        con = json.loads(content)
        if con["code"] != 0:
            if "message" in con:
                msg = con["message"]
            elif "msg" in con:
                msg = con["msg"]
            else:
                msg = "请求失败，服务器未返回失败原因"
            raise BilibiliException(con["code"], msg)
        else:
            if 'data' in con.keys():
                return con['data']
            else:
                if 'result' in con.keys():
                    return con["result"]
                else:
                    return None
    else:
        raise NetworkException(req.status_code)
def get(url, params=None, cookies=None, headers=None, **kwargs):
    resp = request("GET", url=url, params=params, cookies=cookies, headers=headers, **kwargs)
    return resp
def post(url, cookies, data=None, headers=None, **kwargs):
    resp = request("POST", url=url, data=data, cookies=cookies, headers=headers, **kwargs)
    return resp
def get_video_info(bvid: str = None, aid: int = None, verify: Verify = None):
    if not (aid or bvid):
        raise NoIdException
    if verify is None:
        verify = Verify()
    api = {"url": "https://api.bilibili.com/x/web-interface/view", "method": "GET", "verify": False, "params": {"aid": "av号"}, "comment": "视频详细信息"}
    params = {
        "aid": aid,
        "bvid": bvid
    }
    info = get(url=api["url"], params=params, cookies=verify.get_cookies())
    return info
def get_danmaku(bvid: str = None, aid: int = None, page: int = 0,
                verify: Verify = None, date: datetime.date = None):
    if not (aid or bvid):
        raise NoIdException
    if verify is None:
        verify = Verify()
    if date is not None:
        if not verify.has_sess():
            raise NoPermissionException(MESSAGES["no_sess"])
    api = {"url": "https://api.bilibili.com/x/v1/dm/list.so", "method": "GET", "verify": False, "params": {"oid": "video_info中的cid，即分P的编号"}, "comment": "弹幕列表"} if date is None else {"url": "https://api.bilibili.com/x/v2/dm/history", "method": "GET", "verify": False, "params": {"oid": "分P的编号", "type": "1", "date": "日期 (yyyy-mm-dd)"}, "comment": "历史弹幕列表"}
    info = get_video_info(aid=aid, bvid=bvid, verify=verify)
    page_id = info["pages"][page]["cid"]
    params = {
        "oid": page_id
    }
    if date is not None:
        params["date"] = date.strftime("%Y-%m-%d")
        params["type"] = 1
    req = requests.get(api["url"], params=params, headers=DEFAULT_HEADERS, cookies=verify.get_cookies())
    if req.ok:
        con = req.content.decode("utf-8")
        try:
            xml = parseString(con)
        except Exception:
            j = json.loads(con)
            raise BilibiliException(j["code"], j["message"])
        danmaku = xml.getElementsByTagName("d")
        py_danmaku = []
        for d in danmaku:
            info = d.getAttribute("p").split(",")
            text = d.childNodes[0].data
            if info[5] == '0':
                is_sub = False
            else:
                is_sub = True
            dm = Danmaku(
                dm_time=float(info[0]),
                send_time=int(info[4]),
                crc32_id=info[6],
                color=Color(info[3]),
                mode=info[1],
                font_size=info[2],
                is_sub=is_sub,
                text=text
            )
            py_danmaku.append(dm)
        return py_danmaku
    else:
        raise NetworkException(req.status_code)
def get_history_danmaku_index(bvid: str = None, aid: int = None, page: int = 0,
                              date: datetime.date = None, verify: Verify = None):
    if not (aid or bvid):
        raise NoIdException
    if verify is None:
        verify = Verify()
    if date is None:
        date = datetime.date.fromtimestamp(time.time())
    if not verify.has_sess():
        raise NoPermissionException(MESSAGES["no_sess"])
    info = get_video_info(aid=aid, bvid=bvid, verify=verify)
    page_id = info["pages"][page]["cid"]
    api = {"url": "https://api.bilibili.com/x/v2/dm/history/index","method": "GET","verify": True,"params": {"oid": "分P的编号","type": "1","month": "年月 (yyyy-mm)"},"comment": "存在历史弹幕的日期"}
    params = {
        "oid": page_id,
        "month": date.strftime("%Y-%m"),
        "type": 1
    }
    gett = get(url=api["url"], params=params, cookies=verify.get_cookies())
    return gett
def get_pages(bvid: str = None, aid: int = None, verify: Verify = None):
    if not (aid or bvid):
        raise NoIdException
    if verify is None:
        verify = Verify()
    api = {"url": "https://api.bilibili.com/x/player/pagelist","method": "GET","verify": False,"params": {"aid": "av号"},"comment": "分P列表"}
    params = {
        "aid": aid,
        "bvid": bvid
    }
    gett = get(url=api["url"], params=params, cookies=verify.get_cookies())
    return gett
def send_danmaku(danmaku: Danmaku, page: int = 0, bvid: str = None, aid: int = None, verify: Verify = None):
    if not (aid or bvid):
        raise NoIdException
    if verify is None:
        verify = Verify()
    if not verify.has_sess():
        raise NoPermissionException(MESSAGES["no_sess"])
    if not verify.has_csrf():
        raise NoPermissionException(MESSAGES["no_csrf"])
    page_info = get_pages(bvid, aid, verify)
    oid = page_info[page]["cid"]
    api = {"url": "https://api.bilibili.com/x/v2/dm/post","method": "POST","verify": True,"data": {"type": "1","oid": "分P编号","msg": "弹幕内容","bvid": "bvid","progress": "发送时间（毫秒）","color": "颜色（十六进制转十进制）","fontsize": "字体大小（小18普通25大36）","pool": "字幕弹幕（1是0否）","mode": "模式（滚动1顶部5底部4）","plat": "1"},"comment": "发送弹幕"}
    if danmaku.is_sub:
        pool = 1
    else:
        pool = 0
    data = {
        "type": 1,
        "oid": oid,
        "msg": danmaku.text,
        "aid": aid,
        "bvid": bvid,
        "progress": int(danmaku.dm_time.seconds * 1000),
        "color": danmaku.color.get_dec_color(),
        "fontsize": danmaku.font_size,
        "pool": pool,
        "mode": danmaku.mode,
        "plat": 1,
        "csrf": verify.csrf
    }
    resp = post(url=api["url"], data=data, cookies=verify.get_cookies())
    return resp
sessdata = input("你的SESSDATA值：")
csrf = input("你的bili_jct值：")
verify = Verify(sessdata=sessdata, csrf=csrf)
target = input("目标视频的bv号：")
target_page = int(input("目标视频分P的值（没有则填零）："))
bvid = input("弹幕来源视频的bv号：")
page = int(input("弹幕来源分P的值（没有则填零）："))
time_list = get_history_danmaku_index(bvid=bvid, page=page, verify=verify)
print("选择一个要加载的弹幕日期：")
for i, t in enumerate(time_list):
    print("[" + str(i) + "]" + t)
d_list = get_danmaku(bvid=bvid, page=page, date=datetime.date(*map(int,time_list[int(input("输入目标时间之前的序号："))].split('-'))), verify=verify)
print("一共找到" + str(len(d_list)) + "条弹幕，开始发送...")
print("预计发送时间：" + str(15 * len(d_list)) + "秒")
for danmaku in d_list:
    result = send_danmaku(bvid=target, page=target_page, danmaku=danmaku, verify=verify)
    print("发送成功：", danmaku.dm_time, danmaku.color, danmaku.text)
    print("休眠15秒...")
    time.sleep(15)
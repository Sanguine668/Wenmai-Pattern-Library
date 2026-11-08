"""把英文馆藏标题按规则生成为中文文物名（预览 / 写库）。

命名规则：`[工艺] + [纹饰] + [器形/尺寸] + [器型]`，例如
`Bowl with Dragons and Phoenixes` → `龙凤纹碗`；
`Melon-Shaped Ewer with Floral Tendrils` → `花卉纹瓜形执壶`；
`Seated Guanyin` → `观音坐像`。

用法：
    python tools/localize_names.py --preview data/_name_preview.csv
    python tools/localize_names.py --apply
"""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DB = PROJECT / "data" / "wenmai.db"

# 器型（按后缀匹配，越具体越靠后写也不影响，匹配时优先最长后缀）
OBJECTS = {
    "brush washer": "笔洗",
    "brush holder": "笔筒",
    "brush pot": "笔筒",
    "brush rest": "笔架",
    "water coupe": "水盂",
    "water pot": "水盂",
    "water jar": "水盂",
    "water bucket": "水丞",
    "incense burner": "香炉",
    "censer": "香炉",
    "burner": "香炉",
    "sugar bowl": "糖罐",
    "punch bowl": "潘趣碗",
    "tea bowl": "茶碗",
    "soup bowl": "汤碗",
    "altar bowl": "供碗",
    "teacup": "茶盏",
    "tea cup": "茶盏",
    "stem cup": "高足杯",
    "wine cup": "酒杯",
    "wine vessel": "酒器",
    "wine container": "酒器",
    "wine pot": "酒壶",
    "sauceboat": "船形调味碟",
    "tureen": "汤盆",
    "teapot": "茶壶",
    "ewer": "执壶",
    "pitcher": "执壶",
    "flask": "扁壶",
    "vase": "瓶",
    "bottle": "瓶",
    "jar": "罐",
    "bowl": "碗",
    "dish": "盘",
    "plate": "碟",
    "cup": "杯",
    "box": "盒",
    "tray": "托盘",
    "basin": "盆",
    "stand": "座",
    "mirror": "镜",
    "belt": "带",
    "badge": "补子",
    "robe": "袍",
    "textile": "织物",
    "fragment": "残件",
    "inscription": "铭文",
    "rubbing": "拓片",
    "seal": "印",
    "pendant": "坠",
    "ring": "环",
    "hook": "钩",
    "plaque": "牌饰",
    "panel": "板",
    "vessel": "器",
    "container": "容器",
    "pot": "壶",
    "beaker": "杯",
    "cauldron": "鼎",
    "ding": "鼎",
    "gui": "簋",
    "jue": "爵",
    "zun": "尊",
    "hu": "壶",
    "you": "卣",
    "jia": "斝",
    "zhi": "觯",
    "gu": "觚",
    "pan": "盘",
    "dou": "豆",
    "lei": "罍",
    "yan": "甗",
    "fangding": "方鼎",
    "fangyi": "方彝",
    "gong": "觥",
    "yi": "匜",
    "he": "盉",
    "bi": "璧",
    "cong": "琮",
    "huang": "璜",
    "bell": "钟",
    "tazza": "高足盘",
    "amphora": "双耳瓶",
    "snuff bottle": "鼻烟壶",
    "thumb ring": "扳指",
    "belt hook": "带钩",
    "rank badge": "补子",
    "sutra cover": "经卷封皮",
    "book cover": "书封",
    "scroll cover": "卷轴封皮",
    "chair strip": "椅披",
    "cuirass": "甲胄",
    "headpiece": "头饰",
    "pillow": "枕",
    "meiping": "梅瓶",
    "sutra": "经卷",
    "book": "书",
}

OBJECTS.update(
    {
        "tea set": "茶具",
        "tea service": "茶具",
        "jade dragon": "玉龙",
        "brocade": "织锦",
        "mount": "装裱",
        "boot": "靴",
        "boots": "靴",
        "platter": "大盘",
        "charger": "大盘",
        "jug": "壶",
        "creamer": "奶壶",
        "milk jug": "奶壶",
        "shawl": "披肩",
        "buckle": "带扣",
        "cope": "法衣",
        "necklace": "项链",
        "mandarin necklace": "朝珠",
        "disk": "璧",
        "ceremonial disk": "玉璧",
        "scepter": "圭",
        "ceremonial scepter": "圭",
        "amulet": "护身符",
        "thangka": "唐卡",
        "canopy": "华盖",
        "axe": "钺",
        "ceremonial axe": "钺",
        "dagger-axe": "戈",
        "ceremonial dagger-axe": "戈",
        "knife": "刀",
        "ceremonial knife": "刀",
        "loom piece": "织机部件",
        "wrist rest": "腕枕",
        "waterpot": "水盂",
        "cushion cover": "靠垫套",
        "case": "盒",
        "mirror case": "镜盒",
        "cover": "盖",
        "border": "边饰",
        "album": "册页",
        "textile samples": "织物样本",
        "fabric": "织物",
        "silk": "丝织品",
        "headpiece": "头饰",
        "skirt tabard": "裙补",
        "dress tabard": "补褂",
        "coat": "外套",
        "garment": "衣",
        "sleeve": "袖",
        "lining": "衬里",
        "drum": "鼓",
        "jiangu drum": "建鼓",
        "mountain": "山子",
        "koro": "香炉",
        "dui": "敦",
        "yu": "盂",
        "huang": "璜",
        "huan": "环",
        "bi": "璧",
        "jue": "爵",
        "jifu": "吉服",
        "chuba": "楚巴袍",
        "erbei": "耳杯",
        "wan": "碗",
        "liuyeping": "柳叶瓶",
        "bianhu": "扁壶",
        "huangpei": "璜形佩",
        "seal paste": "印泥盒",
        "textile fragment": "织物残片",
        "sutra box": "经盒",
        "scroll box": "卷轴盒",
        "brushholder": "笔筒",
        "brushwasher": "笔洗",
        "pipe": "烟壶",
        "table screen": "插屏",
        "screen": "屏风",
        "drawer": "抽屉",
        "tapestry": "挂毯",
        "wrapper": "包首",
        "water cooler": "水罐",
        "standard weight": "权",
        "weight": "权",
        "blade": "刀",
        "ceremonial blade": "刀",
        "dao": "刀",
        "head": "兽首",
        "feline head": "兽首",
        "embroidery": "刺绣",
        "cloud collar": "云肩",
        "tihong": "剔红漆器",
        "bronze": "铜器",
    }
)

FIGURES = {
    "avalokiteshvara guanyin": "观音菩萨",
    "guanyin": "观音",
    "bodhisattva": "菩萨",
    "buddha": "佛",
    "garuda": "迦楼罗",
    "immortal": "仙人",
    "lady": "仕女",
    "scholar": "高士",
    "official": "官员",
    "warrior": "武士",
    "attendant": "侍从",
    "child": "童子",
    "boy": "童子",
    "horse": "马",
    "dog": "犬",
    "lion": "狮",
    "deer": "鹿",
    "elephant": "象",
    "tiger": "虎",
}

PROPER = {
    "cundi": "准提",
    "avalokiteshvara": "观音",
    "duke ling of jin": "晋灵公",
    "zhou dunyi": "周敦颐",
    "liu haichan": "刘海",
    "zhenwu": "真武",
    "lohan": "罗汉",
    "arhat": "罗汉",
}

SPECIAL_NAMES = {
    "liu haichan with a toad": "刘海戏蟾",
    "family gathering on new year's morning": "岁朝图",
    "a myriad of birds": "百鸟图",
    "reclining water buffalo": "卧牛图",
    "lohan (arhat) holding a peach": "罗汉献桃图",
    "orchid pavilion": "兰亭图",
    "the immortals": "群仙图",
    "two fragments mounted as one": "合装残片",
    "uncut sleeve turnbacks for manchu woman's coat": "满族女袍袖口料",
    "tihong": "剔红漆器",
    "tapestry": "挂毯",
    "dragons chasing flaming pearls": "双龙戏珠纹",
    "phoenix and tree peony": "凤穿牡丹纹",
    "peaches and bats": "桃蝠纹",
    "tigers chasing deer, with dragon": "龙虎鹿纹",
    "potter seated with double gourd vase": "陶工坐像",
    "gathering at lanting (orchid pavilion)": "兰亭雅集图",
    "music in the jade palace": "瑶台仙乐图",
    "achala, king of the wrathful ones": "不动明王像",
    "yutai peak (jade terrace peak)": "玉台峰",
    "mingling of clear and muddy water at the junction of the jing and wei rivers": "泾渭分明图",
    "ancient chinese bronzes": "中国古代铜器",
    "embroidery with birds": "花鸟刺绣",
    "embroidery from a cloud collar: ocean, rocks, and peonies": "云肩刺绣",
    "table screen: the peach blossom spring, land of the immortals": "桃花源插屏",
}

MODIFIERS = {
    "large": "大",
    "small": "小",
    "miniature": "微型",
    "shallow": "浅",
    "deep": "深",
    "flattened": "扁",
    "square": "方",
    "rectangular": "长方",
    "circular": "圆形",
    "round": "圆形",
    "hexagonal": "六方",
    "octagonal": "八方",
    "lobed": "瓜棱",
    "foliate": "花口",
    "foliated": "花口",
    "melon-shaped": "瓜形",
    "bottle-shaped": "瓶形",
    "gourd-shaped": "葫芦形",
    "garlic-head": "蒜头",
    "beehive-shaped": "蜂巢形",
    "arc-shaped": "拱形",
    "tripod": "三足",
    "covered": "带盖",
    "with cover": "带盖",
    "with lid": "带盖",
    "and cover": "带盖",
    "and lid": "带盖",
    "truncated neck": "短颈",
    "high-stemmed": "高足",
    "double-gourd": "葫芦",
    "cylindrical": "筒形",
    "pear-shaped": "梨形",
    "ovoid": "卵形",
    "globular": "圆腹",
}

DECOR = {
    "dragons chasing flaming pearls": "双龙戏珠纹",
    "dragons chasing a flaming pearl": "双龙戏珠纹",
    "dragon chasing a flaming pearl": "龙戏珠纹",
    "dragons chasing flaming pearl": "双龙戏珠纹",
    "dragon and phoenix": "龙凤纹",
    "dragons and phoenixes": "龙凤纹",
    "phoenix and dragon": "龙凤纹",
    "paired dragons": "双龙纹",
    "coiling dragon": "盘龙纹",
    "dragons amid stylized clouds": "祥云龙纹",
    "dragon amid clouds": "云龙纹",
    "dragons writhing amid floral scrolls": "缠枝花卉龙纹",
    "dragon among flowers": "穿花纹",
    "mythical bovine": "犀牛纹",
    "xiniu": "犀牛纹",
    "waves viewing the moon": "犀牛望月纹",
    "peony scrolls": "缠枝牡丹纹",
    "peonies and leaves": "牡丹枝叶纹",
    "peony sprays": "折枝牡丹纹",
    "lotus scrolls": "缠枝莲纹",
    "lotus flowers": "莲花纹",
    "lotus petals": "莲瓣纹",
    "overlapping petals": "重瓣纹",
    "floral scrolls": "缠枝花卉纹",
    "floral tendrils": "缠枝花卉纹",
    "leafy tendrils": "缠枝叶纹",
    "leaf scroll": "缠枝花叶纹",
    "floral spray": "折枝花卉纹",
    "simulated basket weave": "仿编织纹",
    "basket weave": "编织纹",
    "archaistic motifs": "仿古纹",
    "animal mask": "兽面纹",
    "animal masks": "兽面纹",
    "stylized clouds": "祥云纹",
    "chinese landscapes": "山水纹",
    "chinese landscape": "山水纹",
    "scholars in garden": "庭院高士纹",
    "scholars in a garden": "庭院高士纹",
    "boys at play": "婴戏纹",
    "children at play": "婴戏纹",
    "figural scenes": "人物故事纹",
    "figure scenes": "人物故事纹",
    "ducks in pearl medallions": "团花鸭纹",
    "ducks in lotus pond": "莲池鸭纹",
    "dragon medallions": "团龙纹",
    "osmanthus and moon": "桂花月纹",
    "encircled by birds fruits and flowers": "花鸟果纹",
    "birds by lotus flowers": "莲池飞鸟纹",
    "scholar and attendant": "高士侍从纹",
    "clouds": "云纹",
    "cloud": "云纹",
    "peonies": "牡丹纹",
    "peony": "牡丹纹",
    "lotuses": "莲纹",
    "lotus": "莲纹",
    "chrysanthemums": "菊纹",
    "chrysanthemum": "菊纹",
    "plum blossoms": "梅花纹",
    "plum": "梅纹",
    "pine branches": "松枝纹",
    "cherry": "樱纹",
    "bamboo": "竹纹",
    "orchid": "兰纹",
    "narcissus": "水仙纹",
    "osmanthus": "桂花纹",
    "flowers": "花卉纹",
    "floral": "花卉纹",
    "flower": "花卉纹",
    "birds": "花鸟纹",
    "bird": "飞鸟纹",
    "butterflies": "蝴蝶纹",
    "butterfly": "蝴蝶纹",
    "bats": "蝙蝠纹",
    "fish": "鱼纹",
    "waves": "海水纹",
    "wave": "水波纹",
    "landscapes": "山水纹",
    "landscape": "山水纹",
    "garden": "庭院纹",
    "figures": "人物纹",
    "boys": "婴戏纹",
    "children": "婴戏纹",
    "immortals": "仙人纹",
    "medallions": "团花纹",
    "medallion": "团花纹",
    "scrolls": "卷草纹",
    "scroll": "卷草纹",
    "antiquities": "博古纹",
    "lizards": "蜥蜴纹",
    "dragons": "龙纹",
    "dragon": "龙纹",
    "phoenixes": "凤纹",
    "phoenix": "凤纹",
    "hundred shou": "百寿纹",
    "shou": "寿字纹",
    "longevity": "寿纹",
    "endless knot": "盘长纹",
    "pomegranates": "石榴纹",
    "pomegranate": "石榴纹",
    "peaches": "桃纹",
    "peach": "桃纹",
    "lingzhi": "灵芝纹",
    "moon": "月纹",
    "constellations": "星辰纹",
    "stars": "星辰纹",
    "inscription": "铭文",
    "characters": "文字纹",
    "character": "文字纹",
    "poems": "诗文",
    "poem": "诗文",
    "scenes": "故事纹",
    "scene": "故事纹",
    "ducks": "鸭纹",
    "cranes": "鹤纹",
    "deer": "鹿纹",
    "tigers": "虎纹",
    "horses": "马纹",
    "elephants": "象纹",
    "turtles": "龟纹",
    "mandarin ducks": "鸳鸯纹",
    "rocks": "山石纹",
    "rock": "山石纹",
    "plants": "植物纹",
    "plant": "植物纹",
    "melons": "瓜纹",
    "vines": "藤蔓纹",
    "grapes": "葡萄纹",
    "tendrils": "卷草纹",
    "leaves": "叶纹",
    "petals": "花瓣纹",
    "branches": "枝叶纹",
    "band": "带状纹",
    "thunderbolt": "金刚杵纹",
    "vajra": "金刚杵",
    "flaming pearls": "火珠纹",
    "flaming pearl": "火珠纹",
    "pearls": "珠纹",
    "pearl": "珠纹",
    "garuda": "迦楼罗纹",
    "auspicious": "吉祥纹",
    "stylized": "写意",
    "overlapping": "重",
}

TECH = {
    "blue-and-white": "青花",
    "blue and white": "青花",
    "underglaze blue": "青花",
    "underglaze red": "釉里红",
    "overglaze enamels": "釉上彩",
    "overglaze enamel": "釉上彩",
    "doucai": "斗彩",
    "wucai": "五彩",
    "famille rose": "粉彩",
    "qingbai": "青白釉",
    "celadon": "青釉",
    "gilt": "鎏金",
    "gilded": "鎏金",
    "lacquer": "漆",
    "carved": "雕",
    "painted": "彩绘",
    "embroidered": "绣",
    "tihong": "剔红",
}

WORD_MAP = {
    "dragon": "龙", "dragons": "龙", "phoenix": "凤", "phoenixes": "凤",
    "flower": "花", "flowers": "花", "floral": "花卉", "lotus": "莲",
    "lotuses": "莲", "peony": "牡丹", "peonies": "牡丹",
    "chrysanthemum": "菊", "chrysanthemums": "菊", "plum": "梅",
    "blossom": "花", "blossoms": "花", "branch": "枝", "branches": "枝",
    "leaf": "叶", "leaves": "叶", "cloud": "云", "clouds": "云",
    "wave": "波", "waves": "波", "bird": "鸟", "birds": "鸟",
    "butterfly": "蝶", "butterflies": "蝶", "bat": "蝠", "bats": "蝠",
    "fish": "鱼", "deer": "鹿", "horse": "马", "horses": "马",
    "lion": "狮", "tiger": "虎", "elephant": "象", "turtle": "龟",
    "crane": "鹤", "duck": "鸭", "ducks": "鸭", "mandarin": "鸳鸯",
    "garden": "庭院", "landscape": "山水", "landscapes": "山水",
    "mountain": "山", "mountains": "山", "water": "水", "river": "河",
    "sea": "海", "moon": "月", "sun": "日", "star": "星", "stars": "星",
    "constellation": "星辰", "constellations": "星辰", "immortal": "仙",
    "immortals": "仙", "boy": "童子", "boys": "童子", "child": "童子",
    "children": "童子", "lady": "仕女", "scholar": "高士",
    "scholars": "高士", "attendant": "侍从", "warrior": "武士",
    "official": "官员", "guanyin": "观音", "bodhisattva": "菩萨",
    "buddha": "佛", "dog": "犬", "inscription": "铭文",
    "character": "文字", "characters": "文字", "poem": "诗",
    "poems": "诗", "scenes": "景", "scene": "景", "figures": "人物",
    "figure": "人物", "medallion": "团花", "medallions": "团花",
    "scroll": "卷草", "scrolls": "卷草", "tendril": "卷草",
    "tendrils": "卷草", "petal": "瓣", "petals": "瓣", "rock": "石",
    "rocks": "石", "plant": "植物", "plants": "植物", "melon": "瓜",
    "melons": "瓜", "vine": "藤", "vines": "藤", "grape": "葡萄",
    "grapes": "葡萄", "pomegranate": "石榴", "pomegranates": "石榴",
    "peach": "桃", "peaches": "桃", "lingzhi": "灵芝", "osmanthus": "桂花",
    "narcissus": "水仙", "bamboo": "竹", "orchid": "兰", "pine": "松",
    "cherry": "樱", "willow": "柳", "endless": "盘长", "knot": "结",
    "shou": "寿", "longevity": "寿", "thunderbolt": "金刚杵",
    "vajra": "金刚杵", "pearl": "珠", "pearls": "珠", "flaming": "火",
    "auspicious": "吉祥", "archaic": "仿古", "archaistic": "仿古",
    "antique": "古", "mythical": "神兽", "beast": "兽", "beasts": "兽",
    "qilin": "麒麟", "bovine": "牛", "xiniu": "犀牛", "birds": "鸟",
    "fruits": "果", "fruit": "果", "encircled": "环绕",
}

STOPWORDS = {
    "a", "an", "the", "of", "with", "and", "in", "on", "from", "for", "to",
    "by", "at", "as", "or", "is", "are", "this", "that", "its", "possibly",
    "probably", "perhaps", "early", "late", "style", "type", "form", "shape",
    "design", "decoration", "decorated", "motif", "motifs", "pattern",
    "patterns", "interior", "exterior", "pair", "two", "four", "one", "set",
    "chinese", "china", "porcelain", "ware", "dynasty", "period", "reign",
    "emperor", "province", "museum", "gallery", "collection", "art",
    "institute", "institution", "foundation", "trust", "bequest", "fund",
    "purchase", "gift", "accession", "number", "cat", "no", "b", "c",
}

SUFFIXES = (
    "纹", "像", "图", "景", "文", "字", "款", "诗", "书", "记", "印",
    "璧", "琮", "圭", "璋", "璜", "纹样",
)

CONNECTOR_SPLIT = re.compile(
    r"\s*(?:,|;|\band\b|\bamid\b|\bamong\b|\bwith\b|\bof\b|\bby\b|\bin\b|\bon\b)\s*",
    re.I,
)

GENERIC_OBJECTS = {"vessel", "container", "pot", "object", "piece", "item", "ware", "form"}


def clean_title(raw: str) -> str:
    title = re.sub(r"\.(?:jpe?g|png|tiff?|gif|webp)$", "", (raw or "").strip(), flags=re.I)
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"\s*\((?:\d{5,})\)\s*$", "", title)
    title = re.sub(r"\s+(?:MET\s+)?DP\s*\d+.*$", "", title, flags=re.I)
    title = re.sub(r"\s+DSC\s*\d+.*$", "", title, flags=re.I)
    title = re.sub(r"\s+Px\s*\d+.*$", "", title, flags=re.I)
    split = re.split(r"\s+-\s+", title)
    if len(split) > 1:
        tail = split[-1].lower()
        if any(
            word in tail
            for word in (
                "museum", "gallery", "collection", "institute", "foundation",
                "san francisco", "peabody", "portland", "berlin", "tokyo",
                "ontario", "walters", "lacma", "cleveland",
            )
        ):
            title = split[0]
    title = re.split(
        r",\s*(?:China|Chinese|Jingdezhen|Jiangxi|Qing dynasty|Ming dynasty|"
        r"Song dynasty|Yuan dynasty|Tang dynasty|Han dynasty|Warring States|"
        r"Northern Song|Southern Song|Jin dynasty|Liao dynasty|Sui dynasty|"
        r"Qin dynasty|Zhou dynasty|Shang dynasty|Neolithic)\b",
        title,
        maxsplit=1,
        flags=re.I,
    )[0]
    return title.strip(" ,;.")


def replace_phrases(text: str, table: dict[str, str]) -> str:
    result = text
    for phrase in sorted(table, key=len, reverse=True):
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.I)
        result = pattern.sub(f"<{table[phrase]}>", result)
    return result


def translate_decoration(text: str, unknown: list[str]) -> str:
    text = re.sub(
        r"\b(?:design|decoration|decorated|pattern|motif|motifs|symbol)\b",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(r"\([^()]*\)", " ", text)
    marked = replace_phrases(text.lower(), DECOR)
    pieces: list[str] = []
    for raw_part in CONNECTOR_SPLIT.split(marked):
        part = raw_part.strip()
        if not part:
            continue
        inner = re.findall(r"<([^<>]+)>", part)
        if inner:
            pieces.extend(inner)
            remainder = re.sub(r"<[^<>]+>", " ", part)
            if re.search(r"[a-z]{3,}", remainder):
                leftover = replace_phrases(remainder, WORD_MAP)
                pieces.extend(re.findall(r"<([^<>]+)>", leftover))
                for word in re.findall(r"[a-z][a-z'-]{2,}", re.sub(r"<[^<>]+>", " ", leftover)):
                    if word not in STOPWORDS:
                        unknown.append(word)
            continue
        mapped = replace_phrases(part, WORD_MAP)
        pieces.extend(re.findall(r"<([^<>]+)>", mapped))
        for word in re.findall(r"[a-z][a-z'-]{2,}", re.sub(r"<[^<>]+>", " ", mapped)):
            if word not in STOPWORDS:
                unknown.append(word)

    cleaned: list[str] = []
    for piece in pieces:
        piece = re.sub(r"\s+", "", piece).strip("、，")
        if not piece or piece in cleaned:
            continue
        if piece.endswith(SUFFIXES):
            cleaned.append(piece)
        else:
            cleaned.append(piece + "纹")
    if not cleaned:
        return ""
    if len(cleaned) > 3:
        return "、".join(cleaned[:3]) + "等"
    return "、".join(cleaned)


def split_shape(title: str) -> tuple[str, str]:
    match = re.search(r"\b(?:in the shape of|in the form of|shaped like|shaped as)\b(.*)$", title, re.I)
    if match:
        return title[: match.start()].strip(), match.group(1).strip()
    return title, ""


def split_decoration(title: str) -> tuple[str, str]:
    match = re.search(r"\bwith\b(.*)$", title, re.I)
    if match:
        before = title[: match.start()].strip()
        after = match.group(1).strip()
        # “with cover / with lid” 属于器型修饰
        if re.fullmatch(r"(?:a\s+)?(?:cover|lid)", after, re.I):
            return f"{before} with {after}", ""
        return before, after
    return title, ""


def find_object(phrase: str) -> tuple[str, str]:
    lower = re.sub(r"[^a-z0-9' -]", " ", phrase.lower())
    lower = re.sub(r"\s+", " ", lower).strip()
    candidates: list[tuple[tuple[int, int, int], str, str]] = []
    for key, cn in OBJECTS.items():
        variants = {key}
        if key.endswith("y"):
            variants.add(key[:-1] + "ies")
        elif key.endswith(("s", "x", "ch", "sh")):
            variants.add(key + "es")
        else:
            variants.add(key + "s")
        for variant in variants:
            for match in re.finditer(rf"\b{re.escape(variant)}\b", lower):
                score = (
                    0 if key in GENERIC_OBJECTS else 1,
                    -match.start(),
                    len(key),
                )
                candidates.append((score, key, cn))
    if not candidates:
        return "", ""
    best = max(candidates, key=lambda item: item[0])
    return best[1], best[2]


def normalize_head(head: str) -> list[str]:
    variants = [head]
    trimmed = re.sub(
        r"^(?:a\s+)?(?:pair|set|group|series)\s+(?:of\s+)?", "", head, flags=re.I
    )
    variants.append(trimmed)
    variants.append(re.sub(r"^(?:two|three|four|five|six|seven|eight)\s+", "", trimmed, flags=re.I))
    variants.append(re.split(r"\s+(?:from|for)\s+", variants[-1], maxsplit=1, flags=re.I)[0])
    return [v.strip() for v in variants if v and v.strip()]


def translate_shape(shape: str) -> str:
    lower = shape.lower()
    parts: list[str] = []
    if "archaic" in lower:
        parts.append("仿古")
    if "bronze" in lower:
        parts.append("铜")
    alias = ""
    parentheses = re.findall(r"\(([^()]*)\)", shape)
    if parentheses:
        alias_key, alias_cn = find_object(parentheses[-1])
        if alias_cn:
            alias = alias_cn
    if alias:
        parts.append(alias)
    else:
        _, object_cn = find_object(shape)
        if object_cn:
            parts.append(object_cn)
    if not parts:
        for key, value in sorted(MODIFIERS.items(), key=lambda item: len(item[0]), reverse=True):
            if key in lower:
                parts.append(value)
                break
    return "".join(parts)


def translate_title(raw: str) -> tuple[str, str]:
    title = clean_title(raw)
    if re.search(r"[\u4e00-\u9fff]", title):
        return title, "chinese"

    lower = title.lower()
    if lower in SPECIAL_NAMES:
        return SPECIAL_NAMES[lower], "high"

    unknown: list[str] = []
    technique = ""
    for key, value in TECH.items():
        if re.search(rf"\b{re.escape(key)}\b", lower):
            technique = value
            break

    # 人物 / 神像
    if " with " not in lower:
        for name in sorted(FIGURES, key=len, reverse=True):
            if re.search(rf"\b{name}\b", lower):
                proper = ""
                for key, value in PROPER.items():
                    if re.search(rf"\b{key}\b", lower):
                        proper = value
                        break
                posture = ""
                if re.search(r"\bseated\b", lower):
                    posture = "坐"
                elif re.search(r"\bstanding\b", lower):
                    posture = "立"
                extra = ""
                if "stylized clouds" in lower:
                    extra = "祥云"
                return f"{extra}{proper}{FIGURES[name]}{posture}像", "high"

    title_without_shape, shape_text = split_shape(title)
    head, deco_text = split_decoration(title_without_shape)
    shape_head, shape_deco = split_decoration(shape_text) if shape_text else ("", "")
    if shape_deco:
        deco_text = f"{shape_deco} {deco_text}".strip()

    object_key, object_cn = "", ""
    for variant in normalize_head(head):
        object_key, object_cn = find_object(variant)
        if object_cn:
            break
    if not object_cn:
        parentheses = re.findall(r"\(([^()]*)\)", head)
        if parentheses:
            object_key, object_cn = find_object(parentheses[-1])
    if not object_cn:
        fallback = translate_decoration(f"{head} {deco_text}", unknown)
        if fallback:
            return f"{technique}{fallback}", "medium" if unknown else "high"
        if technique:
            return f"{technique}器", "medium"
        return title, "low"

    modifiers: list[str] = []
    if shape_text:
        shape_cn = translate_shape(shape_head or shape_text)
        if shape_cn:
            modifiers.append(shape_cn if shape_cn.endswith(("形", "式")) else shape_cn + "形")

    head_lower = head.lower()
    for key, value in sorted(MODIFIERS.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b{re.escape(key)}\b", head_lower):
            if value not in modifiers:
                modifiers.append(value)

    if re.search(r"\bhandles?\b", lower):
        handle = ""
        for key, value in MODIFIERS.items():
            if "handle" in key and key in lower:
                handle = value
        modifiers.append((handle + "耳") if handle and not handle.endswith("耳") else "带耳")

    decoration = translate_decoration(deco_text, unknown) if deco_text else ""

    name = f"{technique}{decoration}{''.join(dict.fromkeys(modifiers))}{object_cn}"
    name = re.sub(r"纹纹+", "纹", name)
    name = name.replace("器器", "器")
    name = re.sub(r"\s+", "", name)
    if unknown:
        confidence = "medium"
    else:
        confidence = "high"
    return name or title, confidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", default="")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    rows = [
        dict(r)
        for r in connection.execute(
            "select id, name, original_title, motif_type, carrier from patterns order by id"
        )
    ]

    results = []
    for row in rows:
        name, confidence = translate_title(row["original_title"])
        results.append(
            {
                "id": row["id"],
                "old_name": row["name"],
                "original_title": row["original_title"],
                "new_name": name,
                "motif": row["motif_type"],
                "carrier": row["carrier"],
                "confidence": confidence,
            }
        )

    counts: dict[str, int] = {}
    for item in results:
        counts[item["confidence"]] = counts.get(item["confidence"], 0) + 1
    print("confidence", counts)

    if args.preview:
        path = Path(args.preview)
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)
        print("preview", path)

    if args.apply:
        with connection:
            for item in results:
                connection.execute(
                    "update patterns set name = ? where id = ?",
                    (item["new_name"], item["id"]),
                )
        print("applied", len(results))
    connection.close()


if __name__ == "__main__":
    main()

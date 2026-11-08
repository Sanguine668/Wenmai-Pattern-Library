#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按课程模板生成《数据库设计》Word 文档（含 ER 图与多库元数据表）。"""

import pathlib

import docx
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

PROJECT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = PROJECT / "docs" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)
ER_PNG = ASSETS / "er_wenmai.png"
OUT_DOCX = PROJECT / "数据库设计_学号1欧阳宇康_学号2罗云祥_学号3马军.docx"

CJK_BODY, CJK_HEAD, WEST = "宋体", "黑体", "Times New Roman"


def set_run(run, size=10.5, bold=False, cjk=CJK_BODY, west=WEST, color=None):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = west
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), west)
    rfonts.set(qn("w:hAnsi"), west)
    rfonts.set(qn("w:eastAsia"), cjk)


def para(doc, text="", size=10.5, bold=False, align=None, before=0, after=4,
         cjk=CJK_BODY, line=1.3):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    if text:
        set_run(p.add_run(text), size=size, bold=bold, cjk=cjk)
    return p


def heading(doc, text, level=1):
    conf = {1: (15, 12, 6), 2: (12.5, 10, 4), 3: (11, 8, 3)}[level]
    p = doc.add_paragraph(style=f"Heading {level}")
    pf = p.paragraph_format
    pf.space_before = Pt(conf[1])
    pf.space_after = Pt(conf[2])
    pf.line_spacing = 1.2
    set_run(p.add_run(text), size=conf[0], bold=True, cjk=CJK_HEAD)
    return p


def caption(doc, text):
    return para(doc, text, size=10, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
                before=4, after=3, cjk=CJK_HEAD)


def shade(cell, hex_fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_fill)
    tc_pr.append(shd)


def add_table(doc, headers, rows, widths, font_size=9.5):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        set_run(p.add_run(h), size=font_size, bold=True, cjk=CJK_HEAD)
        shade(hdr[i], "EDF2F8")
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.15
            set_run(p.add_run(str(value)), size=font_size)
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            cell.width = Cm(widths[i])
            cell.vertical_alignment = docx.enum.table.WD_ALIGN_VERTICAL.CENTER
    table.columns  # noqa: B018
    return table


def metadata_block(doc, number, name, intro, fields, widths=(3.0, 3.4, 3.6, 6.6)):
    heading(doc, f"（{number}）{name}", level=2)
    para(doc, intro)
    caption(doc, f"表{number}  {name}（{name.replace('表','')} Table）")
    add_table(doc, ["字段名称", "数据类型", "约束", "字段说明"], fields, widths)
    para(doc, "", after=2)


# ----------------------------- ER 图 -----------------------------

def build_er_diagram():
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(12, 7.6), dpi=200)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7.6)
    ax.axis("off")

    def box(x, y, w, h, title, attrs, fill="#EAF1F8", edge="#2E5C8A"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                    linewidth=1.2, edgecolor=edge, facecolor=fill))
        ax.text(x + w / 2, y + h - 0.26, title, ha="center", va="top",
                fontsize=11, fontweight="bold", color="#17324D")
        for i, a in enumerate(attrs):
            ax.text(x + 0.16, y + h - 0.62 - i * 0.30, a, ha="left", va="top", fontsize=8.2)

    def link(x1, y1, x2, y2, label="", style="-", color="#8A6D3B"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=color, lw=1.1,
                                    linestyle=style, shrinkA=2, shrinkB=2))
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.08, label, fontsize=8,
                    color="#7A5A00", ha="center")

    box(0.25, 5.55, 2.6, 1.7, "USER 用户", ["PK id", "username", "password_hash", "role"])
    box(0.25, 3.55, 2.6, 1.7, "FAVORITE 收藏", ["PK id", "FK user_id", "FK pattern_id", "created_at"])
    box(0.25, 1.55, 2.6, 1.7, "BROWSE_LOG 行为", ["PK id", "FK user_id", "FK pattern_id", "action / weight"])
    box(0.25, 0.05, 2.6, 1.2, "USER_UPLOAD 上传识别", ["PK id", "FK user_id", "predict_type_id", "status"])

    box(4.55, 4.85, 2.9, 2.4, "PATTERN 纹样", ["PK id", "name", "FK main_motif_id", "description", "source / license", "view_count"])
    box(4.55, 2.85, 2.9, 1.75, "PATTERN_IMAGE 图片", ["PK id", "FK pattern_id", "image_path", "width / height"])
    box(4.55, 1.15, 2.9, 1.45, "PATTERN_TAG 标签关联", ["PK id", "FK pattern_id", "FK tag_id", "is_primary"])

    box(8.85, 5.35, 2.9, 1.9, "TAG 标签字典", ["PK id", "parent_id", "dimension", "name"])
    box(8.85, 3.35, 2.9, 1.7, "PATTERN_COLOR 配色", ["PK id", "FK pattern_id", "hex / name_cn", "rank / ratio"])
    box(8.85, 1.65, 2.9, 1.45, "TRADITIONAL_COLOR", ["PK id", "name_cn", "hex", "source"])
    box(8.85, 0.05, 2.9, 1.35, "KNOWLEDGE_CHUNK", ["PK id", "related_pattern_id", "section", "chunk_text"])

    link(2.85, 6.3, 4.55, 6.05, "1:N")
    link(2.85, 4.3, 4.55, 5.6, "N:M")
    link(2.85, 2.3, 4.55, 5.0, "记录")
    link(5.95, 4.85, 5.95, 4.6)
    link(5.95, 2.85, 5.95, 2.6)
    link(7.45, 5.9, 8.85, 6.1, "N:1")
    link(7.45, 1.8, 8.85, 5.6, "N:M")
    link(7.45, 4.9, 8.85, 4.2)
    link(10.3, 5.35, 10.3, 5.1)
    link(10.3, 3.35, 10.3, 3.1)
    link(7.45, 4.6, 8.85, 0.9)

    ax.text(6.0, 7.42, "中华纹脉 · 关系型数据库 ER 图（MySQL 主库）",
            ha="center", fontsize=13, fontweight="bold", color="#17324D")
    ax.text(0.25, 7.32, "说明：RAW_RESOURCE 暂存爬取原始数据，经清洗后进入 PATTERN；\n"
                        "GENERATION_TASK 记录生成任务；虚线框外的 MongoDB / Neo4j 承担文档与图数据。",
            fontsize=8.5, color="#555555", va="top")
    fig.tight_layout()
    fig.savefig(ER_PNG, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ER_PNG


# ----------------------------- 内容数据 -----------------------------

SOURCE_ROWS = [
    ("Met Open Access", "https://collectionapi.metmuseum.org",
     "允许（官方开放 API，CC0）", "JSON：名称、年代、朝代、材质、分类、标签、图片 URL", "合并后 595 条"),
    ("Cleveland Open Access", "https://openaccess-api.clevelandart.org",
     "允许（官方开放 API，CC0）", "JSON：名称、年代、文化、类型、工艺、描述、图片 URL", "合并后 359 条"),
    ("Art Institute of Chicago", "https://api.artic.edu/api/v1/artworks/search",
     "允许（官方开放 API，公有领域）", "JSON + IIIF 图片；部分网络图片返回 403", "100 条（图片待补）"),
    ("Wikimedia Commons", "https://commons.wikimedia.org/w/api.php",
     "允许（MediaWiki API，逐文件 CC 授权）", "JSON + 图片，含作者与许可证", "计划补充"),
    ("数字敦煌开放素材库", "https://www.e-dunhuang.com",
     "授权下载（注册、实名、按用途授权）", "壁画、藻井、边饰图文素材", "计划 100～150"),
]

DATA_FIELD_ROWS = [
    ("source / source_id", "来源与来源主键", "唯一标识一条采集记录，便于溯源与去重"),
    ("title", "文物名称", "如“Dish with floral pattern”"),
    ("date_text / century", "年代与世纪", "原始年代描述与换算世纪"),
    ("dynasty", "所属朝代", "如唐、宋、明、清；未知则标注"),
    ("carrier", "实物载体", "瓷器/织物/漆器/金属器/玉器/拓片等"),
    ("motif_type", "纹样类型标签", "8 类标签，人工复核后写入"),
    ("description", "文物介绍", "来源描述或依据可见信息自撰"),
    ("image_urls / local_images", "原图与本地图片", "每条至少一图"),
    ("license / source_url", "许可证与来源页", "CC0 或官方授权，随数据保存"),
]

PROGRESS_ROWS = [
    ("唯一记录总数", "1054 条（Met 595、Cleveland 359、ArtIC 100）"),
    ("有本地图片", "879 条"),
    ("已人工确认标签", "319 条"),
    ("已舍弃（无纹样载体）", "98 条"),
    ("待人工复核", "536 条"),
    ("暂无本地图片", "101 条（ArtIC 100 条、Met 1 条）"),
]

SAMPLE_ROWS = [
    ("Met", "Jar with carp in lotus pond", "明", "瓷器", "花卉纹"),
    ("Met", "Bowl with dragons amid waves", "明", "瓷器", "龙纹"),
    ("Cleveland", "Meiping Vase with Cloud Collars and Peony Sprays", "元", "瓷器", "花卉纹/缠枝卷草纹"),
]

MODULE_ROWS = [
    ("资源管理", "纹样资源、图片、来源与许可证的增删改查", "pattern / pattern_image / raw_resource"),
    ("标签与检索", "纹样类型、朝代、文物类型多标签组合筛选", "tag / pattern_tag"),
    ("用户与行为", "注册登录、收藏、浏览、上传记录", "user / favorite / browse_log / user_upload"),
    ("智能推荐", "基于收藏与浏览行为的混合推荐（首页模块）", "favorite / browse_log / pattern_tag"),
    ("图像识别", "本地上传、拖拽、粘贴图片并识别纹样类型", "user_upload / tag"),
    ("RAG 问答", "数字人浮窗基于知识卡检索并给出引用", "knowledge_chunk / pattern"),
    ("创作生成", "基础纹样、AI 壁纸、产品应用三种生成模式", "generation_task / pattern_color"),
    ("配色系统", "主色提取、传统色命名、生成时自主选色", "traditional_color / pattern_color"),
    ("后台管理", "标签字典、上传审核、行为与热度统计", "tag / user_upload / browse_log"),
    ("多库协同", "文档库存原始 JSON，图库存关系图谱，向量库存检索向量", "MongoDB / Neo4j / Chroma"),
]

MULTIDB_ROWS = [
    ("MySQL 8", "用户、纹样主数据、标签、行为、任务等强关系数据", "事务、增删改查、组合筛选与统计", "唯一可写业务主库"),
    ("MongoDB", "爬虫原始 JSON、异构来源文档、标注进度", "字段灵活、嵌套数组、无需改表", "只读派生视图，可重建"),
    ("Neo4j", "纹样、标签、朝代、载体、寓意及相互关系", "多跳关系查询与图谱可视化", "关系图谱层，服务推荐解释"),
    ("Chroma", "知识片段向量", "向量相似度检索", "RAG 检索专用"),
]

MYSQL_TABLES = [
    ("user表", "该数据表用于记录系统用户信息，包括登录、角色与状态等。",
     [("id", "BIGINT", "PK, AUTO_INCREMENT", "用户ID"),
      ("username", "VARCHAR(50)", "UNIQUE, NOT NULL", "登录名"),
      ("password_hash", "VARCHAR(255)", "NOT NULL", "密码哈希（bcrypt）"),
      ("nickname", "VARCHAR(50)", "", "昵称"),
      ("avatar", "VARCHAR(255)", "", "头像路径"),
      ("role", "VARCHAR(20)", "DEFAULT 'user'", "角色：user / admin"),
      ("status", "TINYINT", "DEFAULT 1", "状态：1 正常，0 禁用"),
      ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "注册时间")]),
    ("tag表", "该数据表用于记录纹样标签字典，支撑纹样类型、朝代、文物类型等多维标签体系。",
     [("id", "INT", "PK, AUTO_INCREMENT", "标签ID"),
      ("parent_id", "INT", "FK→tag.id, NULL", "父标签，支持两级"),
      ("dimension", "VARCHAR(20)", "NOT NULL", "维度：motif_type/dynasty/artifact_type/style"),
      ("name", "VARCHAR(50)", "NOT NULL", "标签名，如“花卉纹”“清”“瓷器”"),
      ("description", "VARCHAR(255)", "", "标签说明"),
      ("sort_no", "INT", "DEFAULT 0", "排序号"),
      ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "创建时间")]),
    ("pattern表", "该数据表用于记录纹样资源主数据，是系统的核心资源表。",
     [("id", "BIGINT", "PK, AUTO_INCREMENT", "纹样ID"),
      ("name", "VARCHAR(100)", "NOT NULL", "纹样名称"),
      ("main_motif_id", "INT", "FK→tag.id", "主纹样类型标签"),
      ("summary", "VARCHAR(500)", "", "纹样摘要"),
      ("description", "TEXT", "", "造型与构图描述"),
      ("cultural_meaning", "TEXT", "", "文化寓意"),
      ("source", "VARCHAR(255)", "", "来源与出处"),
      ("license", "VARCHAR(100)", "", "许可证信息"),
      ("cover_image", "VARCHAR(255)", "", "封面图片路径"),
      ("status", "VARCHAR(20)", "DEFAULT 'published'", "状态：draft/published/discarded"),
      ("view_count", "INT", "DEFAULT 0", "浏览次数（冗余计数）"),
      ("favorite_count", "INT", "DEFAULT 0", "收藏次数（冗余计数）"),
      ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "创建时间"),
      ("updated_at", "DATETIME", "ON UPDATE CURRENT_TIMESTAMP", "更新时间")]),
    ("pattern_tag表", "该数据表用于记录纹样与标签的多对多关联，实现多维标签组合筛选。",
     [("id", "BIGINT", "PK, AUTO_INCREMENT", "关联ID"),
      ("pattern_id", "BIGINT", "FK→pattern.id, NOT NULL", "纹样ID"),
      ("tag_id", "INT", "FK→tag.id, NOT NULL", "标签ID"),
      ("is_primary", "TINYINT", "DEFAULT 0", "是否主分类标签"),
      ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "创建时间")]),
    ("pattern_image表", "该数据表用于记录纹样图片，支持一个纹样多张图片与多角度展示。",
     [("id", "BIGINT", "PK, AUTO_INCREMENT", "图片ID"),
      ("pattern_id", "BIGINT", "FK→pattern.id, NOT NULL", "所属纹样"),
      ("image_path", "VARCHAR(255)", "NOT NULL", "图片路径"),
      ("caption", "VARCHAR(255)", "", "图注"),
      ("width", "INT", "", "图片宽度"),
      ("height", "INT", "", "图片高度"),
      ("is_cover", "TINYINT", "DEFAULT 0", "是否封面图"),
      ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "上传时间")]),
    ("favorite表", "该数据表用于记录用户收藏行为，是推荐系统的重要数据来源。",
     [("id", "BIGINT", "PK, AUTO_INCREMENT", "收藏ID"),
      ("user_id", "BIGINT", "FK→user.id, NOT NULL", "用户ID"),
      ("pattern_id", "BIGINT", "FK→pattern.id, NOT NULL", "纹样ID"),
      ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "收藏时间"),
      ("", "", "UNIQUE(user_id, pattern_id)", "同一用户不可重复收藏")]),
    ("browse_log表", "该数据表用于记录用户浏览、搜索、下载等行为流水，为推荐与统计提供依据。",
     [("id", "BIGINT", "PK, AUTO_INCREMENT", "行为ID"),
      ("user_id", "BIGINT", "FK→user.id, NULL", "用户ID（游客可空）"),
      ("pattern_id", "BIGINT", "FK→pattern.id", "纹样ID"),
      ("action", "VARCHAR(20)", "NOT NULL", "view/favorite/search/download"),
      ("weight", "FLOAT", "DEFAULT 1", "行为权重，收藏高于浏览"),
      ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "行为时间")]),
    ("user_upload表", "该数据表用于记录用户上传识别的图片、预测标签与人工确认结果。",
     [("id", "BIGINT", "PK, AUTO_INCREMENT", "上传ID"),
      ("user_id", "BIGINT", "FK→user.id", "用户ID"),
      ("image_path", "VARCHAR(255)", "NOT NULL", "上传图片路径"),
      ("predict_type_id", "INT", "FK→tag.id", "模型预测主类型标签"),
      ("top3_json", "JSON", "", "预测 top3 标签与置信度"),
      ("model_version", "VARCHAR(50)", "", "模型版本"),
      ("admin_status", "VARCHAR(20)", "DEFAULT 'pending'", "pending/approved/rejected"),
      ("correct_type_id", "INT", "FK→tag.id, NULL", "人工确认的正确标签"),
      ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "上传时间")]),
    ("generation_task表", "该数据表用于记录纹样生成任务与结果，支持基础纹样、壁纸与产品应用三种模式。",
     [("id", "BIGINT", "PK, AUTO_INCREMENT", "任务ID"),
      ("user_id", "BIGINT", "FK→user.id", "用户ID"),
      ("mode", "VARCHAR(20)", "NOT NULL", "basic/wallpaper/product"),
      ("prompt", "TEXT", "", "最终提示词"),
      ("params_json", "JSON", "", "主题、配色、尺寸、风格等参数"),
      ("result_path", "VARCHAR(255)", "", "生成结果路径"),
      ("self_check_json", "JSON", "", "分类自检结果"),
      ("model", "VARCHAR(50)", "", "使用的模型/供应商"),
      ("status", "VARCHAR(20)", "DEFAULT 'queued'", "queued/running/done/failed"),
      ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "创建时间")]),
    ("raw_resource表", "该数据表用于暂存爬虫采集的原始资源，清洗后写入正式业务表。",
     [("id", "BIGINT", "PK, AUTO_INCREMENT", "暂存ID"),
      ("source_site", "VARCHAR(50)", "NOT NULL", "来源站标识"),
      ("source_id", "VARCHAR(100)", "NOT NULL", "来源方主键"),
      ("source_url", "VARCHAR(500)", "UNIQUE", "来源页面地址"),
      ("title", "VARCHAR(255)", "", "原文名称"),
      ("raw_json", "JSON", "", "原始 JSON 快照"),
      ("image_url", "VARCHAR(500)", "", "原始图片地址"),
      ("image_local_path", "VARCHAR(255)", "", "本地图片路径"),
      ("sha256", "VARCHAR(64)", "", "图片哈希（去重）"),
      ("license_note", "VARCHAR(255)", "", "许可证说明"),
      ("pattern_id", "BIGINT", "FK→pattern.id, NULL", "清洗后对应的纹样"),
      ("fetched_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "采集时间"),
      ("status", "VARCHAR(20)", "DEFAULT 'pending'", "pending/imported/discarded")]),
    ("knowledge_chunk表", "该数据表用于保存 RAG 问答的知识片段，向量写入 Chroma 并以 vector_id 关联。",
     [("id", "BIGINT", "PK, AUTO_INCREMENT", "片段ID"),
      ("source_type", "VARCHAR(20)", "NOT NULL", "pattern_card/article"),
      ("source_title", "VARCHAR(255)", "", "知识卡或文章标题"),
      ("related_pattern_id", "BIGINT", "FK→pattern.id, NULL", "关联纹样"),
      ("section", "VARCHAR(100)", "", "段落标识，如“文化寓意”"),
      ("chunk_text", "TEXT", "NOT NULL", "切片文本"),
      ("vector_id", "VARCHAR(64)", "", "Chroma 向量ID"),
      ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "创建时间")]),
    ("traditional_color表", "该数据表用于记录中国传统色字典，是配色系统的基础。",
     [("id", "INT", "PK, AUTO_INCREMENT", "颜色ID"),
      ("name_cn", "VARCHAR(50)", "UNIQUE, NOT NULL", "色名，如朱砂、黛蓝"),
      ("hex", "VARCHAR(7)", "NOT NULL", "十六进制色值"),
      ("rgb_json", "JSON", "", "RGB 值"),
      ("description", "VARCHAR(255)", "", "文化意象说明"),
      ("source", "VARCHAR(255)", "", "参考来源")]),
    ("pattern_color表", "该数据表用于记录纹样主色与人工确认结果，支撑配色筛选与生成取色。",
     [("id", "BIGINT", "PK, AUTO_INCREMENT", "配色ID"),
      ("pattern_id", "BIGINT", "FK→pattern.id, NOT NULL", "纹样ID"),
      ("hex", "VARCHAR(7)", "NOT NULL", "提取主色"),
      ("color_ref_id", "INT", "FK→traditional_color.id, NULL", "匹配的传统色"),
      ("name_cn", "VARCHAR(50)", "", "展示色名"),
      ("rank", "TINYINT", "NOT NULL", "主色排序"),
      ("ratio", "FLOAT", "", "颜色占比"),
      ("method", "VARCHAR(20)", "DEFAULT 'model'", "model/manual/source"),
      ("created_at", "DATETIME", "DEFAULT CURRENT_TIMESTAMP", "创建时间")]),
]

MONGO_ROWS = [
    ("_id", "ObjectId", "MongoDB 主键"),
    ("source", "string", "来源：met/cleveland/commons"),
    ("source_id", "string", "来源方主键"),
    ("title / culture / period", "string", "名称、地域、时期"),
    ("dynasty / medium / classification", "string", "朝代、材质、分类"),
    ("description", "string", "来源方描述"),
    ("tags", "array<string>", "主题标签数组"),
    ("image_urls", "array<string>", "原图地址数组"),
    ("raw", "object", "完整原始 JSON 快照"),
    ("license / source_url", "string", "许可证与来源页"),
    ("pattern_id", "string|null", "清洗后对应纹样ID"),
    ("fetched_at", "date", "采集时间"),
]

MONGO_ANN_ROWS = [
    ("_id", "ObjectId", "MongoDB 主键"),
    ("source / source_id", "string", "标注对象的来源与主键"),
    ("status", "string", "pending/confirmed/discarded"),
    ("motif_type", "string", "最终纹样类型标签"),
    ("motif_type_secondary", "string", "次标签（可选）"),
    ("annotator / note", "string", "标注人与备注"),
    ("updated_at", "date", "更新时间"),
]

NEO_NODE_ROWS = [
    ("Pattern", "pattern_id, name, source", "纹样实体"),
    ("Tag", "name, dimension", "标签（纹样类型/风格）"),
    ("Dynasty", "name", "朝代节点"),
    ("ArtifactType", "name", "载体类型，如瓷器、织物"),
    ("Meaning", "name", "文化寓意"),
    ("Source", "site, url", "数据来源"),
]

NEO_REL_ROWS = [
    ("HAS_TAG", "(Pattern)→(Tag)", "纹样拥有的标签"),
    ("FROM_DYNASTY", "(Pattern)→(Dynasty)", "纹样所属朝代"),
    ("APPEARS_ON", "(Pattern)→(ArtifactType)", "纹样出现的载体"),
    ("SYMBOLIZES", "(Pattern)→(Meaning)", "纹样寓意"),
    ("RELATED_TO", "(Pattern)→(Pattern)", "score, reason：相关纹样"),
    ("SIMILAR_TO", "(Pattern)→(Pattern)", "score：视觉相似"),
    ("SOURCED_FROM", "(Pattern)→(Source)", "数据来源"),
]

TEAM_ROWS = [
    ("（待填写）", "欧阳宇康", "Met 423 条数据采集与图片整理、标注系统开发、数据库总体设计、ER 图与文档整合"),
    ("（待填写）", "罗云祥", "Cleveland/ArtIC 数据采集与初步分类、图片路径修复、质量复核"),
    ("（待填写）", "马军", "Commons/数字敦煌及国内素材、MongoDB/Neo4j 安装与图数据设计、传统色数据整理"),
]


def main() -> None:
    doc = Document()

    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(1.8)
    sec.top_margin = sec.bottom_margin = Cm(2.2)

    normal = doc.styles["Normal"]
    normal.font.name = WEST
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), CJK_BODY)
    normal.paragraph_format.line_spacing = 1.3
    normal.paragraph_format.space_after = Pt(4)

    para(doc, "中华纹脉", size=20, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
         after=2, cjk=CJK_HEAD)
    para(doc, "中华传统纹样资源数据管理系统  数据库设计", size=14, bold=True,
         align=WD_ALIGN_PARAGRAPH.CENTER, after=6, cjk=CJK_HEAD)
    para(doc, "小组：欧阳宇康、罗云祥、马军", size=10.5,
         align=WD_ALIGN_PARAGRAPH.CENTER, after=10)

    heading(doc, "一、资源对象：小组采集的资源数据", 1)
    para(doc, "本小组确定的资源对象为“中华传统纹样图案”，即附着在瓷器、织物、漆器、金属器、"
              "玉器、建筑构件与拓片等实物载体上的装饰纹样。系统面向纹样资源的数字化归档、"
              "检索、推荐、识别、知识问答与辅助创作。")
    para(doc, "目前小组已完成多源采集与初步标注：合并去重后共 1054 条唯一文物记录、879 条有本地图片，"
              "其中 Met 595 条、Cleveland 359 条、ArtIC 100 条；319 条已人工确认纹样类型，98 条被判定为"
              "无纹样载体并舍弃，536 条待人工复核，101 条暂无本地图片。数据全部来自开放馆藏或授权平台，"
              "保留来源链接与许可证信息。")
    caption(doc, "表1  资源数据来源（含爬取许可说明）")
    add_table(doc, ["来源", "网址", "是否允许获取", "数据结构", "数据量"],
              SOURCE_ROWS, (2.5, 4.5, 3.7, 4.5, 2.2), 9)
    para(doc, "", after=2)
    caption(doc, "表2  资源数据字段说明")
    add_table(doc, ["字段", "含义", "说明"], DATA_FIELD_ROWS, (4.0, 3.2, 10.2), 9.5)
    para(doc, "", after=2)
    caption(doc, "表3  数据采集与标注进度")
    add_table(doc, ["指标", "数量"], PROGRESS_ROWS, (6.0, 11.4), 9.5)
    para(doc, "", after=2)
    caption(doc, "表4  资源数据样例")
    add_table(doc, ["来源", "名称", "朝代", "载体", "纹样类型"],
              SAMPLE_ROWS, (2.6, 7.4, 1.8, 2.4, 3.2), 9.5)
    para(doc, "数据存在的问题也已记录：多数为整器照片，需要裁出纹样区域；部分器物本身无纹饰，"
              "已在标注阶段舍弃；ArtIC 图片因服务器限制暂未下载；后续将补充花卉、云纹、几何、文字等类别，"
              "保证类别均衡。")

    heading(doc, "二、系统名称与系统功能", 1)
    para(doc, "系统名称：中华纹脉——中华传统纹样资源数据管理与智能处理系统。")
    para(doc, "系统以“资源数据管理”为基础，以“智能处理”为特色，功能模块如下表所示。")
    caption(doc, "表5  系统功能模块")
    add_table(doc, ["功能模块", "功能说明", "涉及数据表"],
              MODULE_ROWS, (3.0, 9.4, 5.0), 9)
    para(doc, "", after=2)

    heading(doc, "三、数据库总体设计：多库协同", 1)
    para(doc, "采集数据同时包含强关系业务数据、异构原始 JSON 与纹样关系网络，因此采用多数据库协同："
              "MySQL 作为唯一可写的业务主库；MongoDB 保存爬虫原始文档；Neo4j 保存纹样关系图谱；"
              "Chroma 保存 RAG 知识片段向量。MySQL 是事实源，其余三库均可由 MySQL 与原始文件重建。")
    caption(doc, "表6  多数据库分工")
    add_table(doc, ["数据库", "存储内容", "优势", "定位"],
              MULTIDB_ROWS, (2.8, 7.2, 4.6, 2.8), 9)
    para(doc, "", after=2)

    heading(doc, "四、ER 图", 1)
    para(doc, "（此处插入小组使用 draw.io / ProcessOn / Visio 绘制的 ER 图）",
         bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, before=4, after=6)
    para(doc, "实体：USER（用户）、TAG（标签）、PATTERN（纹样）、PATTERN_IMAGE（图片）、"
              "PATTERN_TAG（纹样-标签）、FAVORITE（收藏）、BROWSE_LOG（行为）、USER_UPLOAD（上传识别）、"
              "GENERATION_TASK（生成任务）、RAW_RESOURCE（原始资源）、KNOWLEDGE_CHUNK（知识片段）、"
              "TRADITIONAL_COLOR（传统色）、PATTERN_COLOR（纹样配色）。")
    para(doc, "主要联系：USER 与 PATTERN 通过 FAVORITE 构成 M:N 收藏联系，通过 BROWSE_LOG 记录行为；"
              "USER 1:N USER_UPLOAD、USER 1:N GENERATION_TASK；PATTERN 1:N PATTERN_IMAGE、"
              "PATTERN 1:N PATTERN_COLOR、PATTERN 1:N KNOWLEDGE_CHUNK；PATTERN 与 TAG 通过 PATTERN_TAG "
              "构成 M:N 标签联系，并以 main_motif_id 关联主纹样类型；TAG 通过 parent_id 自关联形成两级标签；"
              "TRADITIONAL_COLOR 1:N PATTERN_COLOR；RAW_RESOURCE 以可空外键 N:1 关联 PATTERN，用于溯源。")
    para(doc, "基数与参与约束的文字说明见项目文档 docs/ER图文字描述.md，可按该描述绘制。")

    heading(doc, "五、元数据设计", 1)
    heading(doc, "（一）MySQL 数据表元数据", 2)
    for i, (name, intro, fields) in enumerate(MYSQL_TABLES, 7):
        metadata_block(doc, i, name, intro, fields)

    heading(doc, "（二）MongoDB 文档集合元数据", 2)
    para(doc, "MongoDB 仅保存爬虫原始数据与标注进度，不重复维护业务表，可随时从 MySQL 重建。")
    caption(doc, "表20  raw_artifacts 集合（爬虫原始数据）")
    add_table(doc, ["字段名称", "数据类型", "字段说明"], MONGO_ROWS, (5.0, 4.0, 8.4), 9.5)
    para(doc, "", after=2)
    caption(doc, "表21  annotations 集合（标注进度）")
    add_table(doc, ["字段名称", "数据类型", "字段说明"], MONGO_ANN_ROWS, (5.0, 4.0, 8.4), 9.5)
    para(doc, "", after=2)

    heading(doc, "（三）Neo4j 图元数据", 2)
    caption(doc, "表22  图节点类型")
    add_table(doc, ["节点标签", "主要属性", "说明"], NEO_NODE_ROWS, (4.2, 6.6, 6.6), 9.5)
    para(doc, "", after=2)
    caption(doc, "表23  图关系类型")
    add_table(doc, ["关系类型", "方向", "属性", "说明"],
              [(r[0], r[1], r[2].split("：")[0], r[2]) if "：" in r[2] else (r[0], r[1], "", r[2])
               for r in NEO_REL_ROWS], (3.6, 5.0, 3.6, 5.2), 9)
    para(doc, "", after=2)

    heading(doc, "六、规范性与创新点", 1)
    para(doc, "规范性：MySQL 表均满足第三范式，主键、外键、唯一约束、非空约束与索引明确；"
              "字符集采用 utf8mb4，支持中文与特殊字符；图片只保存路径，避免大字段拖慢查询；"
              "行为流水表按用户与时间建立索引，支撑推荐与统计。")
    para(doc, "创新点：一是用统一的 tag / pattern_tag 体系承载纹样类型、朝代、文物类型多维标签，"
              "既支持组合筛选又便于扩展；二是多数据库分工明确，MySQL 管业务、MongoDB 管原始异构数据、"
              "Neo4j 管关系图谱与推荐解释、Chroma 管向量检索；三是设计传统色与纹样配色表，"
              "把“主色提取—色名映射—生成选色”贯通为完整链路。")

    heading(doc, "七、每人分工情况", 1)
    caption(doc, "表24  小组分工")
    add_table(doc, ["学号", "姓名", "负责任务"], TEAM_ROWS, (3.4, 3.2, 10.8), 9.5)

    doc.save(OUT_DOCX)
    print("saved", OUT_DOCX)
    print("ER", ER_PNG)


if __name__ == "__main__":
    main()

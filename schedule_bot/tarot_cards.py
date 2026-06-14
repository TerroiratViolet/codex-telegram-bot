from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from random import Random

CARD_ASSET_DIR = Path(__file__).parent / "assets" / "cards"


@dataclass(frozen=True)
class TarotCard:
    number: int
    name_zh: str
    name_en: str
    image_filename: str
    visual_symbols: tuple[str, ...]
    archetype: str
    light: str
    shadow: str
    projection_focus: str

    @property
    def display_name(self) -> str:
        return f"{self.number:02d} · {self.name_zh}（{self.name_en}）"

    @property
    def image_path(self) -> Path:
        return CARD_ASSET_DIR / self.image_filename


def _image_filename(source_path: str, filename: str) -> str:
    # Keep the original Wikimedia path beside each card for source traceability.
    del source_path
    return filename


MAJOR_ARCANA: tuple[TarotCard, ...] = (
    TarotCard(
        0,
        "愚者",
        "The Fool",
        _image_filename("9/90", "RWS_Tarot_00_Fool.jpg"),
        ("悬崖", "白玫瑰", "小狗", "远山", "仰望天空的旅人"),
        "离开已知世界、带着本能开始旅程的人",
        "信任、开放、勇气、新的可能",
        "鲁莽、逃避现实、拒绝承担后果",
        "面对未知时，来访者如何理解自由、风险与责任",
    ),
    TarotCard(
        1,
        "魔术师",
        "The Magician",
        _image_filename("d/de", "RWS_Tarot_01_Magician.jpg"),
        ("高举的权杖", "四元素器具", "无限符号", "红白花园"),
        "把意念带入现实的创造者",
        "主动、专注、资源整合、表达",
        "操控、夸大能力、只停留在表演",
        "来访者如何看待自己的能力、影响力与掌控欲",
    ),
    TarotCard(
        2,
        "女祭司",
        "The High Priestess",
        _image_filename("8/88", "RWS_Tarot_02_High_Priestess.jpg"),
        ("黑白双柱", "帷幕", "月冠", "卷轴", "石榴"),
        "守护无意识与秘密知识的内在知者",
        "直觉、沉静、容纳矛盾、等待",
        "封闭、暧昧、压抑、以神秘逃避沟通",
        "来访者如何处理未知、秘密、直觉和未说出口的感受",
    ),
    TarotCard(
        3,
        "皇后",
        "The Empress",
        _image_filename("d/d2", "RWS_Tarot_03_Empress.jpg"),
        ("麦田", "森林", "流水", "星冠", "柔软坐垫"),
        "滋养生命、让事物生长的母性原型",
        "丰盛、照料、创造、感官与身体连接",
        "过度照顾、占有、依赖舒适、边界模糊",
        "来访者如何理解被爱、照顾别人、身体与丰盛",
    ),
    TarotCard(
        4,
        "皇帝",
        "The Emperor",
        _image_filename("c/c3", "RWS_Tarot_04_Emperor.jpg"),
        ("石座", "公羊头", "铠甲", "荒山", "权杖"),
        "建立秩序、规则与边界的父性原型",
        "结构、责任、保护、稳定领导",
        "僵化、控制、权威焦虑、情感隔离",
        "来访者如何看待权力、规则、安全感和父性权威",
    ),
    TarotCard(
        5,
        "教皇",
        "The Hierophant",
        _image_filename("8/8d", "RWS_Tarot_05_Hierophant.jpg"),
        ("双钥匙", "祝福手势", "两名信徒", "宗教冠冕"),
        "传递传统、信念与群体规范的导师",
        "学习、传承、共同价值、精神秩序",
        "教条、盲从、道德压力、把权威当真理",
        "来访者如何处理传统、归属、规范与个人信念",
    ),
    TarotCard(
        6,
        "恋人",
        "The Lovers",
        _image_filename("d/db", "RWS_Tarot_06_Lovers.jpg"),
        ("两个人", "天使", "生命树", "知识树", "远山"),
        "在关系与价值之间作出真实选择的人",
        "连接、坦诚、价值一致、自主选择",
        "依附、理想化、三角关系、逃避选择",
        "来访者如何理解亲密、欲望、价值冲突与承诺",
    ),
    TarotCard(
        7,
        "战车",
        "The Chariot",
        _image_filename("9/9b", "RWS_Tarot_07_Chariot.jpg"),
        ("黑白斯芬克斯", "星幕", "城堡", "铠甲", "战车"),
        "驾驭相反力量、朝目标前进的英雄",
        "意志、方向、自律、克服阻力",
        "强行推进、压抑矛盾、胜负执念、失控",
        "来访者如何处理目标、竞争、冲突与控制方向",
    ),
    TarotCard(
        8,
        "力量",
        "Strength",
        _image_filename("f/f5", "RWS_Tarot_08_Strength.jpg"),
        ("女性", "狮子", "花环", "无限符号", "白袍"),
        "以温柔意识容纳本能力量的人",
        "耐心、勇气、自我接纳、柔性的力量",
        "压抑愤怒、羞耻、讨好、以温柔掩盖恐惧",
        "来访者如何面对欲望、愤怒、脆弱与自我控制",
    ),
    TarotCard(
        9,
        "隐者",
        "The Hermit",
        _image_filename("4/4d", "RWS_Tarot_09_Hermit.jpg"),
        ("雪山", "提灯", "六芒星", "手杖", "独行老人"),
        "离开喧嚣、寻找内在真理的智者",
        "独处、辨别、内省、成熟指引",
        "孤立、退缩、优越感、拒绝被看见",
        "来访者如何理解独处、距离、智慧与求助",
    ),
    TarotCard(
        10,
        "命运之轮",
        "Wheel of Fortune",
        _image_filename("3/3c", "RWS_Tarot_10_Wheel_of_Fortune.jpg"),
        ("巨轮", "斯芬克斯", "蛇", "四个有翼生物", "云"),
        "提醒人处于周期与更大系统中的命运原型",
        "转机、周期、适应、看见更大格局",
        "宿命感、失去控制、重复模式、把责任交给运气",
        "来访者如何解释变化、偶然、重复与个人能动性",
    ),
    TarotCard(
        11,
        "正义",
        "Justice",
        _image_filename("e/e0", "RWS_Tarot_11_Justice.jpg"),
        ("天平", "宝剑", "红袍", "双柱", "方形冠饰"),
        "衡量事实、后果与责任的裁决者",
        "诚实、公平、边界、承担后果",
        "苛责、非黑即白、自我审判、报复",
        "来访者如何理解公平、责任、愧疚和应得之物",
    ),
    TarotCard(
        12,
        "倒吊人",
        "The Hanged Man",
        _image_filename("2/2b", "RWS_Tarot_12_Hanged_Man.jpg"),
        ("倒悬的人", "发光头冠", "活木架", "平静表情"),
        "通过暂停与倒转视角获得洞见的人",
        "放下、等待、新视角、自愿牺牲",
        "停滞、受害者认同、拖延、无边界牺牲",
        "来访者如何理解等待、牺牲、无力与视角转换",
    ),
    TarotCard(
        13,
        "死神",
        "Death",
        _image_filename("d/d7", "RWS_Tarot_13_Death.jpg"),
        ("白马", "骷髅骑士", "白玫瑰旗", "落日", "不同身份的人"),
        "终结旧形态、推动不可逆转变化的转化者",
        "结束、更新、脱离旧身份、接受变化",
        "抗拒告别、灾难化、执着、情感麻木",
        "来访者如何面对失去、结束、身份变化与重生",
    ),
    TarotCard(
        14,
        "节制",
        "Temperance",
        _image_filename("f/f8", "RWS_Tarot_14_Temperance.jpg"),
        ("天使", "两只杯子", "水与陆地", "远方道路", "日轮"),
        "调和对立、让心理能量流动的炼金术士",
        "整合、适度、耐心、疗愈性的平衡",
        "回避冲突、过度折中、失衡、麻醉感受",
        "来访者如何调节极端、矛盾、节奏与自我照顾",
    ),
    TarotCard(
        15,
        "恶魔",
        "The Devil",
        _image_filename("5/55", "RWS_Tarot_15_Devil.jpg"),
        ("有角形象", "松动的锁链", "裸露男女", "倒五芒星", "火炬"),
        "被否认的欲望、依附与阴影",
        "承认欲望、看见束缚、夺回选择",
        "成瘾、羞耻、操控、把锁链视为不可挣脱",
        "来访者如何处理欲望、禁忌、依赖、羞耻和自由",
    ),
    TarotCard(
        16,
        "高塔",
        "The Tower",
        _image_filename("5/53", "RWS_Tarot_16_Tower.jpg"),
        ("雷击", "坠落王冠", "燃烧高塔", "跌落的人", "黑夜"),
        "击碎虚假稳定、迫使真相显现的突变",
        "觉醒、真相、释放、重新建立",
        "崩溃恐惧、羞辱、灾难化、失去安全结构",
        "来访者如何理解危机、失控、真相与重建",
    ),
    TarotCard(
        17,
        "星星",
        "The Star",
        _image_filename("d/db", "RWS_Tarot_17_Star.jpg"),
        ("八芒星", "裸身女性", "双壶流水", "鸟", "平静水面"),
        "在破碎之后重新连接希望与本真的疗愈者",
        "希望、真诚、复原、灵感",
        "脆弱暴露、空想、等待拯救、失望恐惧",
        "来访者如何理解希望、真实自我、脆弱与未来",
    ),
    TarotCard(
        18,
        "月亮",
        "The Moon",
        _image_filename("7/7f", "RWS_Tarot_18_Moon.jpg"),
        ("月亮", "双塔", "狗与狼", "水中龙虾", "蜿蜒道路"),
        "穿行梦、恐惧与无意识迷雾的夜行者",
        "想象、梦、直觉、容纳不确定",
        "投射、焦虑、欺骗、把感受当事实",
        "来访者如何处理模糊、恐惧、幻想和不可信感",
    ),
    TarotCard(
        19,
        "太阳",
        "The Sun",
        _image_filename("1/17", "RWS_Tarot_19_Sun.jpg"),
        ("太阳", "孩子", "白马", "向日葵", "红旗"),
        "恢复生命力、清晰与自发表达的神圣儿童",
        "喜悦、清晰、活力、被看见",
        "过度乐观、自我中心、必须快乐、忽略阴影",
        "来访者如何理解成功、快乐、认可与真实表达",
    ),
    TarotCard(
        20,
        "审判",
        "Judgement",
        _image_filename("d/dd", "RWS_Tarot_20_Judgement.jpg"),
        ("号角天使", "复起的人", "棺木", "群山", "十字旗"),
        "回应内在召唤、重新评价一生的觉醒者",
        "召唤、宽恕、复盘、重新选择",
        "自我定罪、悔恨、害怕评价、等待外部裁决",
        "来访者如何面对过去、评价、责任与第二次机会",
    ),
    TarotCard(
        21,
        "世界",
        "The World",
        _image_filename("f/ff", "RWS_Tarot_21_World.jpg"),
        ("桂冠", "舞者", "两根权杖", "四个有翼生物"),
        "完成循环并把不同部分整合为整体的完整自性",
        "完成、整合、归属、进入下一阶段",
        "迟迟不结束、完美主义、空虚、害怕新的循环",
        "来访者如何理解完成、归属、完整与下一步",
    ),
)


def draw_major_arcana(random: Random | None = None) -> TarotCard:
    chooser = random or Random()
    return chooser.choice(MAJOR_ARCANA)

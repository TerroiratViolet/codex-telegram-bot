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
        if 0 <= self.number <= 21:
            return f"{self.number:02d} · {self.name_zh}（{self.name_en}）"
        return f"{self.name_zh}（{self.name_en}）"

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


_SUITS = {
    "Wands": {
        "name_zh": "权杖",
        "name_en": "Wands",
        "domain": "行动、意志、热情、创造力和外在推进",
        "symbols": ("木杖", "火元素", "行动姿态", "远方目标"),
        "archetype": "把内在火焰带向世界的行动者",
        "light": "热情、勇气、主动、开创",
        "shadow": "急躁、好胜、耗竭、把冲动误认为使命",
    },
    "Cups": {
        "name_zh": "圣杯",
        "name_en": "Cups",
        "domain": "情感、关系、依恋、想象和内在滋养",
        "symbols": ("圣杯", "水元素", "情感流动", "关系场景"),
        "archetype": "倾听感受并寻找情感容器的人",
        "light": "共情、温柔、连接、情绪觉察",
        "shadow": "沉溺、理想化、逃避现实、情绪依附",
    },
    "Swords": {
        "name_zh": "宝剑",
        "name_en": "Swords",
        "domain": "思想、语言、判断、冲突和清晰边界",
        "symbols": ("宝剑", "风元素", "天空", "紧张的姿态"),
        "archetype": "用意识切开混沌并承担真相的人",
        "light": "清晰、诚实、辨别、决断",
        "shadow": "过度分析、攻击、防御、把想法当作全部事实",
    },
    "Pentacles": {
        "name_zh": "星币",
        "name_en": "Pentacles",
        "domain": "身体、资源、工作、金钱和现实安全感",
        "symbols": ("星币", "土元素", "身体姿态", "现实环境"),
        "archetype": "在现实中种植、照料并收获价值的人",
        "light": "稳定、耐心、积累、照顾现实",
        "shadow": "匮乏焦虑、固着、物化自我、害怕改变",
    },
}

_RANKS = {
    1: {
        "name_zh": "一",
        "name_en": "Ace",
        "image_part": "01",
        "symbols": ("一只伸出的手", "新出现的元素", "尚未展开的潜能"),
        "archetype": "种子、开端与尚未成形的可能",
        "light": "新的机会、纯粹动机、开始尝试",
        "shadow": "只停留在幻想、害怕迈出第一步",
        "focus": "来访者如何面对一个刚出现的可能性",
    },
    2: {
        "name_zh": "二",
        "name_en": "Two",
        "image_part": "02",
        "symbols": ("两个核心元素", "选择或对照", "需要维持的平衡"),
        "archetype": "二元关系、选择与初步协调",
        "light": "合作、平衡、比较后的选择",
        "shadow": "犹豫、拉扯、把矛盾冻结不动",
        "focus": "来访者如何在两个方向、两个人或两种需要之间摆动",
    },
    3: {
        "name_zh": "三",
        "name_en": "Three",
        "image_part": "03",
        "symbols": ("三个元素", "扩展的关系", "初步成果"),
        "archetype": "表达、协作与第一个外化成果",
        "light": "成长、分享、看见雏形",
        "shadow": "分心、比较、害怕被评价",
        "focus": "来访者如何看待成长后的可见性和他人的参与",
    },
    4: {
        "name_zh": "四",
        "name_en": "Four",
        "image_part": "04",
        "symbols": ("四个元素", "边界", "停顿或结构"),
        "archetype": "稳定、边界与暂时成形的秩序",
        "light": "安全感、休整、建立结构",
        "shadow": "停滞、封闭、把稳定变成牢笼",
        "focus": "来访者如何理解安全、暂停和边界",
    },
    5: {
        "name_zh": "五",
        "name_en": "Five",
        "image_part": "05",
        "symbols": ("不稳定的人物关系", "损失或竞争", "被扰动的秩序"),
        "archetype": "冲突、匮乏与秩序被打破后的反应",
        "light": "看见问题、重新调整、从挫折中醒来",
        "shadow": "受害感、争斗、把暂时困难绝对化",
        "focus": "来访者如何解释挫败、竞争、失去或不公平",
    },
    6: {
        "name_zh": "六",
        "name_en": "Six",
        "image_part": "06",
        "symbols": ("交换或过渡", "他者在场", "重新流动的秩序"),
        "archetype": "恢复、互惠与从失衡中重新移动",
        "light": "修复、支持、过渡、重新分配",
        "shadow": "依赖、怀旧、权力不对等",
        "focus": "来访者如何接受帮助、给予帮助或离开旧处境",
    },
    7: {
        "name_zh": "七",
        "name_en": "Seven",
        "image_part": "07",
        "symbols": ("复杂选择", "防守姿态", "多重可能"),
        "archetype": "考验、辨别与面对诱惑或阻力",
        "light": "坚持、策略、辨别真实需要",
        "shadow": "防御过度、迷失、把幻想当选择",
        "focus": "来访者如何在压力、诱惑或多重选项中保护自己",
    },
    8: {
        "name_zh": "八",
        "name_en": "Eight",
        "image_part": "08",
        "symbols": ("重复排列", "速度或限制", "正在成形的模式"),
        "archetype": "模式、练习、速度与自我限制",
        "light": "专注、效率、看见规律、持续练习",
        "shadow": "被困、机械重复、急于完成",
        "focus": "来访者如何看待重复、限制、速度和熟练",
    },
    9: {
        "name_zh": "九",
        "name_en": "Nine",
        "image_part": "09",
        "symbols": ("接近完成", "个人姿态", "成果或压力集中"),
        "archetype": "接近完成时的个人承受与自我确认",
        "light": "成熟、自足、收获、韧性",
        "shadow": "孤军奋战、焦虑、害怕失去成果",
        "focus": "来访者如何体验接近完成时的满足、压力或孤独",
    },
    10: {
        "name_zh": "十",
        "name_en": "Ten",
        "image_part": "10",
        "symbols": ("完整排列", "家庭或负担", "周期抵达终点"),
        "archetype": "完成、累积后果与进入下一轮之前的重量",
        "light": "完成、传承、承担、整体图景",
        "shadow": "过载、僵化、被责任压住",
        "focus": "来访者如何面对结果、责任、家族或长期后果",
    },
    11: {
        "name_zh": "侍从",
        "name_en": "Page",
        "image_part": "11_Page",
        "symbols": ("年轻信使", "手持元素", "好奇观察"),
        "archetype": "学习者、信使与第一次认真凝视某种能量",
        "light": "好奇、学习、敏感、愿意探索",
        "shadow": "幼稚、试探、只收集信号不行动",
        "focus": "来访者如何以新手姿态面对这个议题",
    },
    12: {
        "name_zh": "骑士",
        "name_en": "Knight",
        "image_part": "12_Knight",
        "symbols": ("骑士", "马", "朝某处移动的能量"),
        "archetype": "执行者、追寻者与带着欲望前进的人",
        "light": "行动、追求、投入、把感受化为方向",
        "shadow": "冲动、单线推进、忽略他人的节奏",
        "focus": "来访者如何推进、追逐或逃离这个议题",
    },
    13: {
        "name_zh": "王后",
        "name_en": "Queen",
        "image_part": "13_Queen",
        "symbols": ("王后", "王座", "成熟的内在容器"),
        "archetype": "内在容器、滋养者与成熟的接纳能力",
        "light": "接纳、滋养、洞察、内在稳定",
        "shadow": "过度包容、情绪控制、以照顾换取安全",
        "focus": "来访者如何容纳、照料或控制这个议题",
    },
    14: {
        "name_zh": "国王",
        "name_en": "King",
        "image_part": "14_King",
        "symbols": ("国王", "王座", "外在秩序和掌控"),
        "archetype": "掌权者、整合者与把能量带入秩序的人",
        "light": "成熟掌控、承担、保护、清晰领导",
        "shadow": "控制、僵硬、权威焦虑、拒绝脆弱",
        "focus": "来访者如何掌控、定义或承担这个议题",
    },
}


def _minor_arcana() -> tuple[TarotCard, ...]:
    cards: list[TarotCard] = []
    for suit_index, suit_key in enumerate(("Wands", "Cups", "Swords", "Pentacles"), start=1):
        suit = _SUITS[suit_key]
        for rank_number, rank in _RANKS.items():
            name_zh = f"{suit['name_zh']}{rank['name_zh']}"
            name_en = (
                f"{rank['name_en']} of {suit['name_en']}"
                if rank_number <= 10
                else f"{rank['name_en']} of {suit['name_en']}"
            )
            cards.append(
                TarotCard(
                    100 * suit_index + rank_number,
                    name_zh,
                    name_en,
                    f"{suit_key}{rank['image_part']}.jpg",
                    tuple(suit["symbols"]) + tuple(rank["symbols"]),
                    f"{rank['archetype']}，发生在{suit['domain']}之中；{suit['archetype']}。",
                    f"{rank['light']}；{suit['light']}。",
                    f"{rank['shadow']}；{suit['shadow']}。",
                    f"{rank['focus']}；尤其观察来访者如何投射{suit['domain']}。",
                )
            )
    return tuple(cards)


MINOR_ARCANA: tuple[TarotCard, ...] = _minor_arcana()
TAROT_DECK: tuple[TarotCard, ...] = MAJOR_ARCANA + MINOR_ARCANA


def draw_major_arcana(random: Random | None = None) -> TarotCard:
    chooser = random or Random()
    return chooser.choice(MAJOR_ARCANA)


def draw_tarot_card(random: Random | None = None) -> TarotCard:
    chooser = random or Random()
    return chooser.choice(TAROT_DECK)

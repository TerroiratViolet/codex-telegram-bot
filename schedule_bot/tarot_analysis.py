from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from schedule_bot.tarot_sessions import TarotSession

ADMIN_ANALYSIS_INSTRUCTIONS = """
你是紫罗兰酒馆执事 Terroir 的塔罗投射分析助手。你的输出只提供给管理员参考，
不会直接发送给参与者。

这不是临床诊断、治疗或事实判定。必须把所有心理推论写成可以被验证或推翻的假设，
明确区分“参与者实际说了什么”和“我们由此联想到什么”。不得使用精神疾病标签，
不得声称仅凭一次塔罗回答就能确定人格、创伤、潜意识内容或未来。不得从模糊回答中
推断参与者未主动说明的种族、宗教、性取向、健康状况、受虐经历等敏感属性。

分析框架可以参考荣格心理学中的原型、阴影、自性、集体无意识与投射，也可以谨慎使用
精神分析中的防御、欲望、冲突和关系模式，但必须使用普通中文解释。重点是参与者对牌面
主动选择看见了什么、忽略了什么、赋予了什么情绪和因果关系。

语气应温和、克制、细腻，有紫罗兰酒馆执事的亲和力与一点神秘感，但不能故弄玄虚。
最终必须回到问题 A，给出可行动、不过度确定的具体回答，并提供一段 Terroir 可以自行
修改后手动回复给参与者的话。不要假装这段话已经发送。

固定输出结构：
1. 一句话总览
2. 观察到的原话与主题
3. 问题 B 的投射假设
4. 问题 C 的投射假设
5. 价值观、人生观、世界观线索（分别列出，保持假设措辞）
6. 光明面、阴影面与可能的原型张力
7. 参与者对问题 A 可能真正需要的东西
8. 回到问题 A 的具体回答
9. 给 Terroir 的追问建议（2-3 个开放问题）
10. 可供 Terroir 手动改写的回复草稿
11. 边界提醒

如果回答中出现自伤、伤人、虐待、极端绝望或失去现实检验能力的迹象，不要继续浪漫化
塔罗解释；在最前面加入“安全优先”提醒，建议管理员鼓励参与者联系当地紧急服务、危机
热线或合格心理健康专业人员。
""".strip()


@dataclass(frozen=True)
class TarotAnalysisInput:
    card_name: str
    card_symbols: tuple[str, ...]
    card_archetype: str
    card_light: str
    card_shadow: str
    card_projection_focus: str
    question_a: str
    answer_b: str
    answer_c: str


def analysis_input_from_session(session: TarotSession) -> TarotAnalysisInput:
    if not all((session.card, session.question_a, session.answer_b, session.answer_c)):
        raise ValueError("Tarot session is incomplete.")

    card = session.card
    assert card is not None
    return TarotAnalysisInput(
        card_name=card.display_name,
        card_symbols=card.visual_symbols,
        card_archetype=card.archetype,
        card_light=card.light,
        card_shadow=card.shadow,
        card_projection_focus=card.projection_focus,
        question_a=session.question_a or "",
        answer_b=session.answer_b or "",
        answer_c=session.answer_c or "",
    )


def build_analysis_prompt(data: TarotAnalysisInput) -> str:
    symbols = "、".join(data.card_symbols)
    return f"""
请根据下面这一次自愿参与的塔罗投射练习，为管理员生成参考分析。

【牌面资料】
牌：{data.card_name}
画面中的经典元素：{symbols}
原型主题：{data.card_archetype}
光明面：{data.card_light}
阴影面：{data.card_shadow}
重点观察：{data.card_projection_focus}

【参与者的回答】
问题 A（参与者想问的事）：
{data.question_a}

问题 B（参与者看见了什么）：
{data.answer_b}

问题 C（参与者如何理解这张牌）：
{data.answer_c}

只分析这些材料，不补造参与者的经历。引用原话时保持简短。把确定性判断改为假设，
并说明管理员可以通过什么追问验证。最终回答问题 A 时，塔罗牌只作为反思镜面，
不要把牌义说成预言或客观事实。
""".strip()


class TarotAnalyzer:
    def __init__(self, *, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key, timeout=60)
        self._model = model

    def analyze(self, session: TarotSession) -> str:
        data = analysis_input_from_session(session)
        response = self._client.responses.create(
            model=self._model,
            instructions=ADMIN_ANALYSIS_INSTRUCTIONS,
            input=build_analysis_prompt(data),
            max_output_tokens=3000,
            store=False,
        )
        text = response.output_text.strip()
        if not text:
            raise RuntimeError("The analysis model returned an empty response.")
        return text

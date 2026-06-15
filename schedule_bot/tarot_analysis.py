from __future__ import annotations

import time
from contextlib import suppress
from dataclasses import dataclass
from typing import Protocol

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAI,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)

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

TRANSIENT_RETRY_DELAYS_SECONDS = (1.0, 3.0, 8.0)


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


@dataclass(frozen=True)
class LLMHealthCheck:
    ok: bool
    model: str | None
    message: str


class TarotAnalysisError(RuntimeError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.safe_message = message


class TarotAnalysisProvider(Protocol):
    provider_name: str

    def analyze(self, session: TarotSession) -> str: ...

    def check_connection(self) -> LLMHealthCheck: ...


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


class GeminiTarotAnalyzer:
    provider_name = "Gemini"

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gemini-2.5-flash",
        fallback_model: str = "",
    ) -> None:
        from google import genai
        from google.genai import types

        self._client = genai.Client(api_key=api_key)
        self._types = types
        self._model = model
        self._fallback_model = fallback_model
        self._retry_delays = TRANSIENT_RETRY_DELAYS_SECONDS
        self._sleep = time.sleep

    @property
    def models(self) -> tuple[str, ...]:
        models = [self._model]
        if self._fallback_model and self._fallback_model not in models:
            models.append(self._fallback_model)
        return tuple(models)

    def analyze(self, session: TarotSession) -> str:
        data = analysis_input_from_session(session)
        return self._create_with_fallback(
            instructions=ADMIN_ANALYSIS_INSTRUCTIONS,
            input_text=build_analysis_prompt(data),
            max_output_tokens=3000,
        )

    def check_connection(self) -> LLMHealthCheck:
        try:
            model = self._create_with_fallback(
                instructions="你只需要回复 OK。",
                input_text="请回复 OK，确认 Gemini API、模型与项目权限可用。",
                max_output_tokens=200,
                return_model=True,
            )
        except TarotAnalysisError as error:
            return LLMHealthCheck(
                ok=False,
                model=None,
                message=error.safe_message,
            )
        return LLMHealthCheck(
            ok=True,
            model=model,
            message=f"Gemini 连接正常，模型 {model} 可用。",
        )

    def _create_with_fallback(
        self,
        *,
        instructions: str,
        input_text: str,
        max_output_tokens: int,
        return_model: bool = False,
    ) -> str:
        first_error: Exception | None = None
        for index, model in enumerate(self.models):
            try:
                response = self._generate_content_with_retries(
                    model=model,
                    input_text=input_text,
                    instructions=instructions,
                    max_output_tokens=max_output_tokens,
                )
            except Exception as error:
                if index == 0 and _can_try_gemini_fallback(error) and len(self.models) > 1:
                    first_error = error
                    continue
                raise TarotAnalysisError(_safe_gemini_error_message(error)) from error

            text = _gemini_response_text(response)
            if not text:
                raise TarotAnalysisError(_empty_gemini_response_message(response))
            if return_model:
                return model
            if first_error is not None:
                return (
                    f"【系统提示】主模型 {self._model} 暂时不可用，"
                    f"本次已自动改用备用模型 {model}。\n\n{text}"
                )
            return text

        raise TarotAnalysisError("Gemini 分析暂时失败，请稍后重试。")

    def _generate_content_with_retries(
        self,
        *,
        model: str,
        input_text: str,
        instructions: str,
        max_output_tokens: int,
    ) -> object:
        retry_delays = getattr(self, "_retry_delays", ())
        sleep = getattr(self, "_sleep", time.sleep)
        for attempt in range(len(retry_delays) + 1):
            try:
                return self._client.models.generate_content(
                    model=model,
                    contents=input_text,
                    config=_gemini_generate_config(
                        self._types,
                        instructions=instructions,
                        max_output_tokens=max_output_tokens,
                    ),
                )
            except Exception as error:
                if attempt >= len(retry_delays) or not _is_transient_gemini_error(
                    error
                ):
                    raise
                sleep(retry_delays[attempt])

        raise RuntimeError("unreachable")


class OpenAITarotAnalyzer:
    provider_name = "OpenAI"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        fallback_model: str = "gpt-5.4-mini",
    ) -> None:
        self._client = OpenAI(api_key=api_key, timeout=60)
        self._model = model
        self._fallback_model = fallback_model
        self._retry_delays = TRANSIENT_RETRY_DELAYS_SECONDS
        self._sleep = time.sleep

    @property
    def models(self) -> tuple[str, ...]:
        models = [self._model]
        if self._fallback_model and self._fallback_model not in models:
            models.append(self._fallback_model)
        return tuple(models)

    def analyze(self, session: TarotSession) -> str:
        data = analysis_input_from_session(session)
        return self._create_with_fallback(
            instructions=ADMIN_ANALYSIS_INSTRUCTIONS,
            input_text=build_analysis_prompt(data),
            max_output_tokens=3000,
        )

    def check_connection(self) -> LLMHealthCheck:
        try:
            model = self._create_with_fallback(
                instructions="你只需要回复 OK。",
                input_text="请回复 OK，确认 API、模型与项目权限可用。",
                max_output_tokens=20,
                return_model=True,
            )
        except TarotAnalysisError as error:
            return LLMHealthCheck(
                ok=False,
                model=None,
                message=error.safe_message,
            )
        return LLMHealthCheck(
            ok=True,
            model=model,
            message=f"OpenAI 连接正常，模型 {model} 可用。",
        )

    def _create_with_fallback(
        self,
        *,
        instructions: str,
        input_text: str,
        max_output_tokens: int,
        return_model: bool = False,
    ) -> str:
        first_error: OpenAIError | Exception | None = None
        for index, model in enumerate(self.models):
            try:
                response = self._create_response_with_retries(
                    model=model,
                    instructions=instructions,
                    input_text=input_text,
                    max_output_tokens=max_output_tokens,
                )
            except OpenAIError as error:
                if index == 0 and _can_try_fallback(error) and len(self.models) > 1:
                    first_error = error
                    continue
                raise TarotAnalysisError(_safe_openai_error_message(error)) from error

            text = response.output_text.strip()
            if not text:
                raise TarotAnalysisError("OpenAI 返回了空回复，请稍后重试。")
            if return_model:
                return model
            if first_error is not None:
                return (
                    f"【系统提示】主模型 {self._model} 暂时不可用，"
                    f"本次已自动改用备用模型 {model}。\n\n{text}"
                )
            return text

        raise TarotAnalysisError("OpenAI 分析暂时失败，请稍后重试。")

    def _create_response_with_retries(
        self,
        *,
        model: str,
        instructions: str,
        input_text: str,
        max_output_tokens: int,
    ) -> object:
        retry_delays = getattr(self, "_retry_delays", ())
        sleep = getattr(self, "_sleep", time.sleep)
        for attempt in range(len(retry_delays) + 1):
            try:
                return self._client.responses.create(
                    model=model,
                    instructions=instructions,
                    input=input_text,
                    max_output_tokens=max_output_tokens,
                    store=False,
                )
            except OpenAIError as error:
                if attempt >= len(retry_delays) or not _is_transient_openai_error(
                    error
                ):
                    raise
                sleep(retry_delays[attempt])

        raise RuntimeError("unreachable")


TarotAnalyzer = OpenAITarotAnalyzer


def _can_try_gemini_fallback(error: Exception) -> bool:
    code = _gemini_error_code(error)
    if code in {400, 403, 404}:
        return True
    message = str(error).lower()
    return "model" in message or "permission" in message or "not found" in message


def _is_transient_gemini_error(error: Exception) -> bool:
    code = _gemini_error_code(error)
    if code in {408, 500, 502, 503, 504}:
        return True
    message = str(error).lower()
    return (
        "timeout" in message
        or "temporarily unavailable" in message
        or "service unavailable" in message
        or "try again" in message
    )


def _gemini_generate_config(
    types: object,
    *,
    instructions: str,
    max_output_tokens: int,
) -> object:
    kwargs: dict[str, object] = {
        "system_instruction": instructions,
        "max_output_tokens": max_output_tokens,
    }
    thinking_config_type = getattr(types, "ThinkingConfig", None)
    if thinking_config_type is not None:
        with suppress(TypeError):
            kwargs["thinking_config"] = thinking_config_type(thinking_budget=64)
    return types.GenerateContentConfig(**kwargs)


def _gemini_response_text(response: object) -> str:
    direct_text = getattr(response, "text", "") or ""
    if direct_text.strip():
        return direct_text.strip()

    parts_text: list[str] = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            text = getattr(part, "text", "") or ""
            if text.strip():
                parts_text.append(text.strip())
    return "\n".join(parts_text).strip()


def _empty_gemini_response_message(response: object) -> str:
    finish_reasons = []
    for candidate in getattr(response, "candidates", []) or []:
        finish_reason = getattr(candidate, "finish_reason", None)
        if finish_reason is not None:
            finish_reasons.append(str(finish_reason))
    if finish_reasons:
        return (
            "Gemini 返回了空回复。"
            f"finish_reason={', '.join(finish_reasons)}。"
            "请稍后重试，或把 GEMINI_MODEL 改为当前账号可用的 Flash 模型。"
        )
    return (
        "Gemini 返回了空回复。请稍后重试，或把 GEMINI_MODEL 改为当前账号可用的 Flash 模型。"
    )


def _gemini_error_code(error: Exception) -> int | None:
    code = getattr(error, "code", None)
    if isinstance(code, int):
        return code
    status_code = getattr(error, "status_code", None)
    if isinstance(status_code, int):
        return status_code
    response = getattr(error, "response", None)
    response_status = getattr(response, "status_code", None)
    if isinstance(response_status, int):
        return response_status
    return None


def _safe_gemini_error_message(error: Exception) -> str:
    code = _gemini_error_code(error)
    if code in {401, 403}:
        return "Gemini API Key 无效，或当前 Google AI 项目没有权限使用配置的模型。"
    if code == 404:
        return "配置的 Gemini 模型在当前账号、区域或 API 版本中不可用。"
    if code == 429:
        return "Gemini 免费额度、速率限制或配额已经达到上限。"
    if code == 400:
        return "Gemini 拒绝了本次请求参数，请检查模型配置或 SDK 兼容性。"
    if code and code >= 500:
        return f"Gemini 服务返回错误状态码 {code}，请稍后重试。"
    message = str(error).lower()
    if "api key" in message:
        return "Gemini API Key 无效、缺失或未被当前服务读取。"
    if "quota" in message or "rate" in message:
        return "Gemini 免费额度、速率限制或配额已经达到上限。"
    return "Gemini 分析暂时失败，请检查 API Key、模型名称、免费额度和项目权限。"


def _can_try_fallback(error: OpenAIError) -> bool:
    if isinstance(error, (NotFoundError, PermissionDeniedError)):
        return True
    if isinstance(error, BadRequestError):
        message = str(error).lower()
        return "model" in message
    return False


def _is_transient_openai_error(error: OpenAIError) -> bool:
    if isinstance(error, (APIConnectionError, APITimeoutError)):
        return True
    if isinstance(error, APIStatusError):
        return error.status_code in {408, 500, 502, 503, 504}
    return False


def _safe_openai_error_message(error: OpenAIError) -> str:
    if isinstance(error, AuthenticationError):
        return "OpenAI API Key 无效、已撤销，或不属于当前 Railway 项目。"
    if isinstance(error, PermissionDeniedError):
        return "当前 OpenAI 项目或 API Key 没有权限使用配置的模型。"
    if isinstance(error, NotFoundError):
        return "配置的 OpenAI 模型在当前账号或项目中不可用。"
    if isinstance(error, RateLimitError):
        return "OpenAI 调用达到额度、余额或速率限制。"
    if isinstance(error, (APIConnectionError, APITimeoutError)):
        return "连接 OpenAI 超时或网络暂时不可用。"
    if isinstance(error, BadRequestError):
        return "OpenAI 拒绝了本次请求参数，请检查模型配置或 SDK 兼容性。"
    if isinstance(error, APIStatusError):
        return f"OpenAI 服务返回错误状态码 {error.status_code}，请稍后重试。"
    return "OpenAI 分析暂时失败，请检查 API Key、模型权限、余额和项目配置。"

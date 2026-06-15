from datetime import UTC, datetime

import httpx
import pytest
from openai import AuthenticationError, NotFoundError

from schedule_bot.tarot_analysis import (
    ADMIN_ANALYSIS_INSTRUCTIONS,
    GeminiTarotAnalyzer,
    OpenAITarotAnalyzer,
    TarotAnalysisError,
    analysis_input_from_session,
    build_analysis_prompt,
)
from schedule_bot.tarot_cards import MAJOR_ARCANA
from schedule_bot.tarot_sessions import TarotSession, TarotStage


def _complete_session() -> TarotSession:
    return TarotSession(
        session_id="safe-session",
        group_chat_id=-100,
        admin_user_id=1,
        target_user_id=2,
        target_display_name="参与者",
        target_username=None,
        stage=TarotStage.ANALYZING,
        created_at=datetime.now(UTC),
        question_a="我是否应该离开现在的工作？",
        answer_b="我先看到悬崖，也看到远处的山。",
        answer_c="我觉得他既自由又可能跌下去。",
        card=MAJOR_ARCANA[0],
    )


def test_analysis_prompt_contains_answers_and_defined_card_meaning() -> None:
    prompt = build_analysis_prompt(analysis_input_from_session(_complete_session()))

    assert "我是否应该离开现在的工作" in prompt
    assert "悬崖" in prompt
    assert "自由又可能跌下去" in prompt
    assert MAJOR_ARCANA[0].archetype in prompt
    assert MAJOR_ARCANA[0].shadow in prompt


def test_analysis_prompt_prioritizes_user_description_over_card_meaning() -> None:
    prompt = build_analysis_prompt(analysis_input_from_session(_complete_session()))

    assert prompt.index("【参与者的回答】") < prompt.index("【牌面资料】")
    assert "参与者自己的 A/B/C 描述为先" in prompt
    assert "以参与者描述为主" in prompt
    assert "牌面资料只作为辅助镜面" in prompt


def test_analysis_instructions_are_admin_only_and_non_diagnostic() -> None:
    assert "只提供给管理员" in ADMIN_ANALYSIS_INSTRUCTIONS
    assert "不是临床诊断" in ADMIN_ANALYSIS_INSTRUCTIONS
    assert "不得使用精神疾病标签" in ADMIN_ANALYSIS_INSTRUCTIONS
    assert "敏感属性" in ADMIN_ANALYSIS_INSTRUCTIONS
    assert "问题 A" in ADMIN_ANALYSIS_INSTRUCTIONS
    assert "安全优先" in ADMIN_ANALYSIS_INSTRUCTIONS
    assert "目标不是预测未来" in ADMIN_ANALYSIS_INSTRUCTIONS
    assert "牌面是镜子，不是答案" in ADMIN_ANALYSIS_INSTRUCTIONS
    assert "参与者的描述优先于标准牌义" in ADMIN_ANALYSIS_INSTRUCTIONS


def test_analysis_prompt_rejects_fatalistic_prediction() -> None:
    prompt = build_analysis_prompt(analysis_input_from_session(_complete_session()))

    assert "不要预测未来" in prompt
    assert "不要把牌义说成宿命答案" in prompt
    assert "理解、探索与重构叙事" in prompt


def test_incomplete_session_cannot_be_analyzed() -> None:
    incomplete = _complete_session().with_updates(answer_c=None)

    with pytest.raises(ValueError, match="incomplete"):
        analysis_input_from_session(incomplete)


def test_analyzer_disables_response_storage() -> None:
    calls = []

    class FakeResponses:
        def create(self, **kwargs):
            calls.append(kwargs)
            return type("Response", (), {"output_text": "参考分析"})()

    analyzer = OpenAITarotAnalyzer.__new__(OpenAITarotAnalyzer)
    analyzer._client = type("Client", (), {"responses": FakeResponses()})()
    analyzer._model = "test-model"
    analyzer._fallback_model = ""

    result = analyzer.analyze(_complete_session())

    assert result == "参考分析"
    assert calls[0]["model"] == "test-model"
    assert calls[0]["store"] is False
    assert calls[0]["max_output_tokens"] == 3000


def test_openai_analyzer_falls_back_when_primary_model_is_unavailable() -> None:
    calls = []

    class FakeResponses:
        def create(self, **kwargs):
            calls.append(kwargs)
            if kwargs["model"] == "primary-model":
                request = httpx.Request("POST", "https://api.openai.com/v1/responses")
                response = httpx.Response(404, request=request)
                raise NotFoundError(
                    "model not found",
                    response=response,
                    body=None,
                )
            return type("Response", (), {"output_text": "备用模型分析"})()

    analyzer = OpenAITarotAnalyzer.__new__(OpenAITarotAnalyzer)
    analyzer._client = type("Client", (), {"responses": FakeResponses()})()
    analyzer._model = "primary-model"
    analyzer._fallback_model = "fallback-model"

    result = analyzer.analyze(_complete_session())

    assert [call["model"] for call in calls] == ["primary-model", "fallback-model"]
    assert "主模型 primary-model 暂时不可用" in result
    assert "备用模型 fallback-model" in result
    assert "备用模型分析" in result


def test_openai_health_check_reports_safe_authentication_error() -> None:
    class FakeResponses:
        def create(self, **kwargs):
            request = httpx.Request("POST", "https://api.openai.com/v1/responses")
            response = httpx.Response(401, request=request)
            raise AuthenticationError(
                "invalid api key",
                response=response,
                body=None,
            )

    analyzer = OpenAITarotAnalyzer.__new__(OpenAITarotAnalyzer)
    analyzer._client = type("Client", (), {"responses": FakeResponses()})()
    analyzer._model = "primary-model"
    analyzer._fallback_model = "fallback-model"

    check = analyzer.check_connection()

    assert not check.ok
    assert check.model is None
    assert "API Key 无效" in check.message


def test_unrecoverable_openai_error_uses_safe_message() -> None:
    class FakeResponses:
        def create(self, **kwargs):
            request = httpx.Request("POST", "https://api.openai.com/v1/responses")
            response = httpx.Response(401, request=request)
            raise AuthenticationError(
                "invalid api key",
                response=response,
                body=None,
            )

    analyzer = OpenAITarotAnalyzer.__new__(OpenAITarotAnalyzer)
    analyzer._client = type("Client", (), {"responses": FakeResponses()})()
    analyzer._model = "primary-model"
    analyzer._fallback_model = "fallback-model"

    with pytest.raises(TarotAnalysisError, match="API Key"):
        analyzer.analyze(_complete_session())


def test_gemini_analyzer_uses_generate_content() -> None:
    calls = []

    class FakeTypes:
        class GenerateContentConfig:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            return type("Response", (), {"text": "Gemini 参考分析"})()

    analyzer = GeminiTarotAnalyzer.__new__(GeminiTarotAnalyzer)
    analyzer._client = type("Client", (), {"models": FakeModels()})()
    analyzer._types = FakeTypes
    analyzer._model = "gemini-test-model"
    analyzer._fallback_model = ""

    result = analyzer.analyze(_complete_session())

    assert result == "Gemini 参考分析"
    assert calls[0]["model"] == "gemini-test-model"
    assert "我是否应该离开现在的工作" in calls[0]["contents"]
    config = calls[0]["config"].kwargs
    assert config["system_instruction"] == ADMIN_ANALYSIS_INSTRUCTIONS
    assert config["max_output_tokens"] == 3000


def test_gemini_analyzer_retries_transient_503_before_failing_session() -> None:
    calls = []
    sleeps = []

    class FakeTypes:
        class GenerateContentConfig:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

    class GeminiServiceUnavailable(Exception):
        code = 503

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise GeminiServiceUnavailable("service unavailable")
            return type("Response", (), {"text": "重试后生成的 Gemini 分析"})()

    analyzer = GeminiTarotAnalyzer.__new__(GeminiTarotAnalyzer)
    analyzer._client = type("Client", (), {"models": FakeModels()})()
    analyzer._types = FakeTypes
    analyzer._model = "gemini-test-model"
    analyzer._fallback_model = ""
    analyzer._retry_delays = (0.1, 0.2)
    analyzer._sleep = sleeps.append

    result = analyzer.analyze(_complete_session())

    assert result == "重试后生成的 Gemini 分析"
    assert [call["model"] for call in calls] == [
        "gemini-test-model",
        "gemini-test-model",
    ]
    assert sleeps == [0.1]


def test_gemini_analyzer_reports_safe_message_after_retry_exhaustion() -> None:
    calls = []
    sleeps = []

    class FakeTypes:
        class GenerateContentConfig:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

    class GeminiServiceUnavailable(Exception):
        code = 503

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            raise GeminiServiceUnavailable("service unavailable")

    analyzer = GeminiTarotAnalyzer.__new__(GeminiTarotAnalyzer)
    analyzer._client = type("Client", (), {"models": FakeModels()})()
    analyzer._types = FakeTypes
    analyzer._model = "gemini-test-model"
    analyzer._fallback_model = ""
    analyzer._retry_delays = (0.1, 0.2)
    analyzer._sleep = sleeps.append

    with pytest.raises(TarotAnalysisError, match="503"):
        analyzer.analyze(_complete_session())

    assert len(calls) == 3
    assert sleeps == [0.1, 0.2]


def test_gemini_health_check_uses_enough_output_tokens() -> None:
    calls = []

    class FakeTypes:
        class GenerateContentConfig:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        class ThinkingConfig:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            return type("Response", (), {"text": "OK"})()

    analyzer = GeminiTarotAnalyzer.__new__(GeminiTarotAnalyzer)
    analyzer._client = type("Client", (), {"models": FakeModels()})()
    analyzer._types = FakeTypes
    analyzer._model = "gemini-test-model"
    analyzer._fallback_model = ""

    check = analyzer.check_connection()

    assert check.ok
    config = calls[0]["config"].kwargs
    assert config["max_output_tokens"] == 200
    assert config["thinking_config"].kwargs == {"thinking_budget": 64}


def test_gemini_analyzer_reads_text_from_candidate_parts() -> None:
    class FakeTypes:
        class GenerateContentConfig:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

    class FakePart:
        text = "候选文本分析"

    class FakeContent:
        parts = [FakePart()]

    class FakeCandidate:
        content = FakeContent()

    class FakeModels:
        def generate_content(self, **kwargs):
            return type("Response", (), {"text": "", "candidates": [FakeCandidate()]})()

    analyzer = GeminiTarotAnalyzer.__new__(GeminiTarotAnalyzer)
    analyzer._client = type("Client", (), {"models": FakeModels()})()
    analyzer._types = FakeTypes
    analyzer._model = "gemini-test-model"
    analyzer._fallback_model = ""

    assert analyzer.analyze(_complete_session()) == "候选文本分析"


def test_gemini_empty_response_reports_finish_reason() -> None:
    class FakeTypes:
        class GenerateContentConfig:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

    class FakeCandidate:
        finish_reason = "MAX_TOKENS"
        content = type("Content", (), {"parts": []})()

    class FakeModels:
        def generate_content(self, **kwargs):
            return type("Response", (), {"text": "", "candidates": [FakeCandidate()]})()

    analyzer = GeminiTarotAnalyzer.__new__(GeminiTarotAnalyzer)
    analyzer._client = type("Client", (), {"models": FakeModels()})()
    analyzer._types = FakeTypes
    analyzer._model = "gemini-test-model"
    analyzer._fallback_model = ""

    with pytest.raises(TarotAnalysisError, match="MAX_TOKENS"):
        analyzer.analyze(_complete_session())


def test_gemini_analyzer_falls_back_when_primary_model_is_unavailable() -> None:
    calls = []

    class FakeTypes:
        class GenerateContentConfig:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

    class GeminiPermissionError(Exception):
        code = 403

    class FakeModels:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            if kwargs["model"] == "primary-gemini":
                raise GeminiPermissionError("model permission denied")
            return type("Response", (), {"text": "备用 Gemini 分析"})()

    analyzer = GeminiTarotAnalyzer.__new__(GeminiTarotAnalyzer)
    analyzer._client = type("Client", (), {"models": FakeModels()})()
    analyzer._types = FakeTypes
    analyzer._model = "primary-gemini"
    analyzer._fallback_model = "fallback-gemini"

    result = analyzer.analyze(_complete_session())

    assert [call["model"] for call in calls] == ["primary-gemini", "fallback-gemini"]
    assert "主模型 primary-gemini 暂时不可用" in result
    assert "备用模型 fallback-gemini" in result
    assert "备用 Gemini 分析" in result


def test_gemini_health_check_reports_safe_quota_error() -> None:
    class FakeTypes:
        class GenerateContentConfig:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

    class GeminiQuotaError(Exception):
        code = 429

    class FakeModels:
        def generate_content(self, **kwargs):
            raise GeminiQuotaError("quota exceeded")

    analyzer = GeminiTarotAnalyzer.__new__(GeminiTarotAnalyzer)
    analyzer._client = type("Client", (), {"models": FakeModels()})()
    analyzer._types = FakeTypes
    analyzer._model = "gemini-test-model"
    analyzer._fallback_model = ""

    check = analyzer.check_connection()

    assert not check.ok
    assert check.model is None
    assert "免费额度" in check.message

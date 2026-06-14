from datetime import UTC, datetime

import pytest

from schedule_bot.tarot_analysis import (
    ADMIN_ANALYSIS_INSTRUCTIONS,
    TarotAnalyzer,
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


def test_analysis_instructions_are_admin_only_and_non_diagnostic() -> None:
    assert "只提供给管理员" in ADMIN_ANALYSIS_INSTRUCTIONS
    assert "不是临床诊断" in ADMIN_ANALYSIS_INSTRUCTIONS
    assert "不得使用精神疾病标签" in ADMIN_ANALYSIS_INSTRUCTIONS
    assert "敏感属性" in ADMIN_ANALYSIS_INSTRUCTIONS
    assert "问题 A" in ADMIN_ANALYSIS_INSTRUCTIONS
    assert "安全优先" in ADMIN_ANALYSIS_INSTRUCTIONS


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

    analyzer = TarotAnalyzer.__new__(TarotAnalyzer)
    analyzer._client = type("Client", (), {"responses": FakeResponses()})()
    analyzer._model = "test-model"

    result = analyzer.analyze(_complete_session())

    assert result == "参考分析"
    assert calls[0]["model"] == "test-model"
    assert calls[0]["store"] is False
    assert calls[0]["max_output_tokens"] == 3000

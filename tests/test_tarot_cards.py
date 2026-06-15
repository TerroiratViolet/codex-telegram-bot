from pathlib import Path

from schedule_bot.tarot_cards import (
    MAJOR_ARCANA,
    MINOR_ARCANA,
    TAROT_DECK,
    draw_major_arcana,
    draw_tarot_card,
)


def test_major_arcana_has_22_unique_well_defined_cards() -> None:
    assert len(MAJOR_ARCANA) == 22
    assert {card.number for card in MAJOR_ARCANA} == set(range(22))
    assert len({card.image_filename for card in MAJOR_ARCANA}) == 22

    for card in MAJOR_ARCANA:
        assert card.name_zh
        assert card.name_en
        assert card.image_filename.startswith("RWS_Tarot_")
        assert card.image_path.is_file()
        assert card.image_path.stat().st_size > 10_000
        assert card.image_path.read_bytes()[:3] == b"\xff\xd8\xff"
        assert len(card.visual_symbols) >= 4
        assert card.archetype
        assert card.light
        assert card.shadow
        assert card.projection_focus


def test_draw_major_arcana_returns_a_defined_card() -> None:
    assert draw_major_arcana() in MAJOR_ARCANA


def test_full_tarot_deck_has_78_packaged_cards() -> None:
    assert len(MINOR_ARCANA) == 56
    assert len(TAROT_DECK) == 78
    assert len({card.number for card in TAROT_DECK}) == 78
    assert len({card.image_filename for card in TAROT_DECK}) == 78

    for card in TAROT_DECK:
        assert card.name_zh
        assert card.name_en
        assert card.image_path.is_file()
        assert card.image_path.stat().st_size > 10_000
        assert card.image_path.read_bytes()[:3] == b"\xff\xd8\xff"
        assert len(card.visual_symbols) >= 4
        assert card.archetype
        assert card.light
        assert card.shadow
        assert card.projection_focus


def test_draw_tarot_card_returns_a_defined_card() -> None:
    assert draw_tarot_card() in TAROT_DECK


def test_tarot_role_and_invitation_images_are_packaged() -> None:
    asset_dir = Path(__file__).parents[1] / "schedule_bot" / "assets"
    assert (asset_dir / "tarot-admin.png").stat().st_size > 100_000
    invitation_images = sorted(asset_dir.glob("tarot-consent-*.jpg"))

    assert len(invitation_images) == 10
    assert {image.name for image in invitation_images} == {
        f"tarot-consent-{index:02d}.jpg" for index in range(1, 11)
    }
    for image in invitation_images:
        assert image.stat().st_size > 100_000
        assert image.read_bytes()[:3] == b"\xff\xd8\xff"


def test_invitation_image_generation_rules_reject_black_hands() -> None:
    architecture_doc = (
        Path(__file__).parents[1] / "docs" / "ARCHITECTURE.md"
    ).read_text(encoding="utf-8")

    assert "邀请图生成规则" in architecture_doc
    assert "自然肤色" in architecture_doc
    assert "黑色的手" in architecture_doc
    assert "黑色手套" in architecture_doc
    assert "必须重新生成后再次确认" in architecture_doc

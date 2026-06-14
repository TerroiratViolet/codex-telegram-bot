from pathlib import Path

from schedule_bot.tarot_cards import MAJOR_ARCANA, draw_major_arcana


def test_major_arcana_has_22_unique_well_defined_cards() -> None:
    assert len(MAJOR_ARCANA) == 22
    assert {card.number for card in MAJOR_ARCANA} == set(range(22))
    assert len({card.image_url for card in MAJOR_ARCANA}) == 22

    for card in MAJOR_ARCANA:
        assert card.name_zh
        assert card.name_en
        assert card.image_url.startswith("https://upload.wikimedia.org/")
        assert len(card.visual_symbols) >= 4
        assert card.archetype
        assert card.light
        assert card.shadow
        assert card.projection_focus


def test_draw_major_arcana_returns_a_defined_card() -> None:
    assert draw_major_arcana() in MAJOR_ARCANA


def test_tarot_role_images_are_packaged() -> None:
    asset_dir = Path(__file__).parents[1] / "schedule_bot" / "assets"
    assert (asset_dir / "tarot-admin.png").stat().st_size > 100_000
    assert (asset_dir / "tarot-consent.png").stat().st_size > 100_000

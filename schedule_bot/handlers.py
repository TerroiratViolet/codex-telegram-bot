from __future__ import annotations

import asyncio
import html
import logging
import random
from pathlib import Path

from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatType, ParseMode
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from schedule_bot.config import Settings
from schedule_bot.responses import reply_for_text
from schedule_bot.tarot_analysis import TarotAnalyzer
from schedule_bot.tarot_cards import draw_major_arcana
from schedule_bot.tarot_sessions import TarotSession, TarotSessionStore, TarotStage

LOGGER = logging.getLogger(__name__)
ASSET_DIR = Path(__file__).parent / "assets"
MAX_TAROT_ANSWER_LENGTH = 1500

TAROT_INTROS = (
    (
        "紫罗兰酒馆的灯火已经为你留出一席。Terroir 不替世界许诺答案，只陪你在未知"
        "面前停一会儿。光明与阴影总是同行，而古老原型有时会借一幅画，提醒我们正在"
        "把什么带进眼前的问题。"
    ),
    (
        "杯中的紫色微光晃了一下，像世界在回答之前先保持沉默。Terroir 会替你守住这段"
        "谈话的边界；牌不会决定命运，它只是让人性里熟悉的光、影与原型暂时显形。"
    ),
    (
        "欢迎来到紫罗兰酒馆的一次小小夜谈。未知仍旧是未知，但人对爱、失去、自由与"
        "归属的渴望从未真正改变。若你愿意，Terroir 将为你翻开一张牌，把它当作照见"
        "内心联想的镜面。"
    ),
)


def _mention_html(session: TarotSession) -> str:
    if session.target_username:
        return f"@{html.escape(session.target_username)}"
    return (
        f'<a href="tg://user?id={session.target_user_id}">'
        f"{html.escape(session.target_display_name)}</a>"
    )


def _stores(context: ContextTypes.DEFAULT_TYPE) -> tuple[TarotSessionStore, TarotAnalyzer | None]:
    store = context.application.bot_data["tarot_store"]
    analyzer = context.application.bot_data.get("tarot_analyzer")
    return store, analyzer


def _force_reply(placeholder: str) -> ForceReply:
    return ForceReply(selective=True, input_field_placeholder=placeholder)


def _is_expected_reply(update: Update, session: TarotSession) -> bool:
    message = update.effective_message
    replied_to = message.reply_to_message if message else None
    return bool(
        replied_to
        and session.expected_reply_to_message_id is not None
        and replied_to.message_id == session.expected_reply_to_message_id
    )


async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    message = update.effective_message
    if message is None:
        return

    first_name = update.effective_user.first_name if update.effective_user else "朋友"
    await message.reply_text(reply_for_text(message.text or "", first_name=first_name))


async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    if update.effective_message is None or update.effective_user is None:
        return
    await update.effective_message.reply_text(
        f"你的 Telegram 数字 ID：{update.effective_user.id}\n"
        "只有管理员需要把这个数字加入 TELEGRAM_ADMIN_USER_IDS。"
    )


async def tarot_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    admin = update.effective_user
    chat = update.effective_chat
    if message is None or admin is None or chat is None:
        return

    admin_ids: frozenset[int] = context.application.bot_data["tarot_admin_ids"]
    if admin.id not in admin_ids:
        await message.reply_text("这项仪式只对 Terroir 管理员开放。")
        return
    if chat.type == ChatType.PRIVATE:
        await message.reply_text("请在群组中回复一位用户的消息，然后发送 /tarot。")
        return
    if message.reply_to_message is None or message.reply_to_message.from_user is None:
        await message.reply_text("请先回复你要邀请的用户消息，再发送 /tarot。")
        return

    target = message.reply_to_message.from_user
    if target.is_bot:
        await message.reply_text("不能邀请 Bot 参加塔罗投射练习。")
        return

    store, analyzer = _stores(context)
    try:
        session = store.create(
            group_chat_id=chat.id,
            admin_user_id=admin.id,
            target_user_id=target.id,
            target_display_name=target.full_name,
            target_username=target.username,
        )
    except ValueError:
        await message.reply_text("这位用户在本群已有一场尚未结束的塔罗练习。")
        return

    admin_caption = (
        "Terroir 管理界面\n\n"
        f"准备向 {target.full_name} 发出邀请。\n"
        f"群组 ID：{chat.id}\n"
        f"会话：{session.session_id}\n"
        f"LLM 分析：{'已配置' if analyzer else '尚未配置 OPENAI_API_KEY'}\n\n"
        "用户完成 A、B、C 后，分析只会送到这里。"
    )
    try:
        with (ASSET_DIR / "tarot-admin.png").open("rb") as image:
            await context.bot.send_photo(
                chat_id=admin.id,
                photo=image,
                caption=admin_caption,
            )
    except TelegramError:
        store.save(session.with_updates(stage=TarotStage.DECLINED))
        await message.reply_text(
            "尚未发出邀请：我无法私聊管理员。请 Terroir 先私聊 Bot 并发送 /start，"
            "然后回到群组重新发起 /tarot。"
        )
        return

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "我愿意开始",
                    callback_data=f"tarot:yes:{session.session_id}",
                ),
                InlineKeyboardButton(
                    "暂不参加",
                    callback_data=f"tarot:no:{session.session_id}",
                ),
            ]
        ]
    )
    intro = random.choice(TAROT_INTROS)
    mention = _mention_html(session)
    with (ASSET_DIR / "tarot-consent.png").open("rb") as image:
        await message.reply_photo(
            photo=image,
            caption=(
                f"{mention}\n\n{html.escape(intro)}\n\n"
                "这是一场自愿的投射性反思，不是预言、心理诊断或治疗。你的回答只会用于"
                "本次练习；LLM 生成的参考分析仅私聊发送给管理员，由管理员自行判断是否"
                "以及如何回应。你可以选择不参加。"
            ),
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )


async def tarot_consent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if query is None or user is None or query.data is None:
        return

    parts = query.data.split(":", maxsplit=2)
    if len(parts) != 3:
        return
    _, decision, session_id = parts
    store, _ = _stores(context)
    session = store.get(session_id)
    if session is None:
        await query.answer("这次邀请已经过期。", show_alert=True)
        return
    if user.id != session.target_user_id:
        await query.answer("只有被邀请的用户可以选择。", show_alert=True)
        return
    if session.stage != TarotStage.AWAITING_CONSENT:
        await query.answer("你已经做出选择。", show_alert=True)
        return

    if decision == "no":
        store.save(session.with_updates(stage=TarotStage.DECLINED))
        await query.answer("你的选择已被尊重。")
        await query.edit_message_caption(
            caption="这次邀请已经婉拒。紫罗兰酒馆会尊重每一次“不”。",
        )
        return

    session = store.save(session.with_updates(stage=TarotStage.AWAITING_QUESTION_A))
    await query.answer("占卜练习开始。")
    await query.edit_message_reply_markup(reply_markup=None)
    if query.message is not None:
        prompt_message = await query.message.reply_text(
            (
                f"{_mention_html(session)}\n\n"
                "问题 A：请回复这条消息，写下你此刻真正想问的问题。\n"
                "请不要写身份证件、住址、密码、医疗记录等敏感个人信息。"
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=_force_reply("问题 A：你真正想问什么？"),
        )
        store.save(
            session.with_updates(expected_reply_to_message_id=prompt_message.message_id)
        )


async def tarot_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if message is None or user is None or chat is None:
        return

    store, analyzer = _stores(context)
    session = store.get_active_for_user(chat.id, user.id)
    if session is None:
        await reply(update, context)
        return

    if not _is_expected_reply(update, session):
        return

    text = (message.text or "").strip()
    if not text:
        return
    if len(text) > MAX_TAROT_ANSWER_LENGTH:
        await message.reply_text(
            f"这段回答超过 {MAX_TAROT_ANSWER_LENGTH} 个字符，请简化后重新回复上一条问题。"
        )
        return

    mention = _mention_html(session)
    if session.stage == TarotStage.AWAITING_QUESTION_A:
        card = draw_major_arcana()
        session = session.with_updates(
            question_a=text,
            card=card,
            stage=TarotStage.AWAITING_ANSWER_B,
            expected_reply_to_message_id=None,
        )
        caption = (
            f"{mention}，你抽到的是：{html.escape(card.display_name)}\n\n"
            "问题 B：请想着问题 A，只描述你在牌面中主动看见的内容。哪些人物、物品、"
            "颜色、动作或关系最先吸引你？请回复这张牌回答。\n\n"
            "先不要查牌义。这里重要的是你的第一眼。"
        )
        try:
            prompt_message = await message.reply_photo(
                photo=card.image_url,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=_force_reply("问题 B：你在牌面中看见了什么？"),
            )
        except TelegramError:
            prompt_message = await message.reply_text(
                f"{card.image_url}\n\n{caption}",
                parse_mode=ParseMode.HTML,
                reply_markup=_force_reply("问题 B：你在牌面中看见了什么？"),
            )
        store.save(
            session.with_updates(expected_reply_to_message_id=prompt_message.message_id)
        )
        return

    if session.stage == TarotStage.AWAITING_ANSWER_B:
        prompt_message = await message.reply_text(
            (
                f"{mention}\n\n"
                "问题 C：这张牌让你怎么想？你觉得画面正在发生什么，它与你的问题 A "
                "有什么关系？请回复这条消息回答。"
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=_force_reply("问题 C：你如何理解这张牌？"),
        )
        store.save(
            session.with_updates(
                answer_b=text,
                stage=TarotStage.AWAITING_ANSWER_C,
                expected_reply_to_message_id=prompt_message.message_id,
            )
        )
        return

    if session.stage != TarotStage.AWAITING_ANSWER_C:
        await message.reply_text("你的回答正在处理中，请稍候。")
        return

    session = store.save(
        session.with_updates(
            answer_c=text,
            stage=TarotStage.ANALYZING,
            expected_reply_to_message_id=None,
        )
    )
    await message.reply_text(
        (
            f"{mention}，你的三段回答已经收好。\n\n"
            "牌面不会替你决定命运。Terroir 会在私聊中收到一份仅供参考的投射分析，"
            "再由他亲自决定如何回应你。"
        ),
        parse_mode=ParseMode.HTML,
    )

    if analyzer is None:
        store.save(session.with_updates(stage=TarotStage.COMPLETE))
        await context.bot.send_message(
            chat_id=session.admin_user_id,
            text=(
                "塔罗会话已完成，但 OPENAI_API_KEY 尚未配置，因此没有生成 LLM 分析。\n"
                f"会话：{session.session_id}"
            ),
        )
        return

    await context.bot.send_message(
        chat_id=session.admin_user_id,
        text=f"正在整理塔罗投射分析……\n会话：{session.session_id}",
    )
    try:
        analysis = await asyncio.to_thread(analyzer.analyze, session)
    except Exception:
        LOGGER.exception("Tarot analysis failed for session_id=%s", session.session_id)
        store.save(session.with_updates(stage=TarotStage.COMPLETE))
        await context.bot.send_message(
            chat_id=session.admin_user_id,
            text=(
                "LLM 分析暂时失败。用户回答没有被公开，请稍后重新发起或检查 OpenAI 配置。\n"
                f"会话：{session.session_id}"
            ),
        )
        return

    store.save(session.with_updates(stage=TarotStage.COMPLETE))
    header = (
        "Terroir 私密参考 · 塔罗投射分析\n"
        f"牌面：{session.card.display_name if session.card else '未知'}\n"
        f"会话：{session.session_id}\n\n"
        "以下内容是可验证的解释假设，不是心理诊断。请结合你对参与者的真实了解进行"
        "人工判断，不要原样照搬。\n\n"
    )
    await _send_long_private_message(
        context=context,
        chat_id=session.admin_user_id,
        text=header + analysis,
    )


async def _send_long_private_message(
    *,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str,
) -> None:
    limit = 3900
    remaining = text
    while remaining:
        if len(remaining) <= limit:
            chunk, remaining = remaining, ""
        else:
            split_at = remaining.rfind("\n", 0, limit)
            if split_at < limit // 2:
                split_at = limit
            chunk, remaining = remaining[:split_at], remaining[split_at:].lstrip()
        await context.bot.send_message(chat_id=chat_id, text=chunk)


async def log_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    update_id = update.update_id if isinstance(update, Update) else None
    LOGGER.error("Unhandled update error. update_id=%s", update_id, exc_info=context.error)


def build_application(settings: Settings) -> Application:
    application = Application.builder().token(settings.telegram_bot_token).build()
    application.bot_data["tarot_store"] = TarotSessionStore()
    application.bot_data["tarot_admin_ids"] = settings.telegram_admin_user_ids
    if settings.openai_api_key:
        application.bot_data["tarot_analyzer"] = TarotAnalyzer(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )

    for command in ("start", "help", "ping", "about"):
        application.add_handler(CommandHandler(command, reply))
    application.add_handler(CommandHandler("whoami", whoami))
    application.add_handler(CommandHandler("tarot", tarot_start))
    application.add_handler(
        CallbackQueryHandler(tarot_consent, pattern=r"^tarot:(yes|no):")
    )
    application.add_handler(MessageHandler(filters.COMMAND, reply))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, tarot_text_router)
    )
    application.add_error_handler(log_error)
    return application

from __future__ import annotations

from telegram.ext import Application, CommandHandler, ConversationHandler

from tonus_bot.handlers import register_handlers


def test_register_handlers_adds_expected_handlers() -> None:
    application = Application.builder().token("123:abc").build()

    register_handlers(application)

    handlers = application.handlers[0]
    assert any(isinstance(h, ConversationHandler) for h in handlers)
    command_handlers = [h for h in handlers if isinstance(h, CommandHandler)]
    commands = {cmd for h in command_handlers for cmd in h.commands}
    assert {"stats", "week", "settings"} <= commands

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from markupsafe import Markup, escape
from odoo import Command, fields, models, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    """Extension of res.partner to hold Telegram-related fields."""
    _inherit = "res.partner"
    _description = 'Contact'

    telegram_chat_id = fields.Char(
        string="Telegram Chat ID", 
        index=True,
        help="The unique identifier for this contact's Telegram chat. Used by the system to route messages to the correct user in Telegram."
    )
    telegram_username = fields.Char(
        string="Telegram Username",
        help="The Telegram username of the contact. Useful for identifying the contact in Telegram."
    )
    telegram_opt_in = fields.Boolean(
        string="Allow Telegram Messages", 
        default=True,
        help="If checked, the system will allow sending Telegram messages to this contact. Uncheck to opt-out the contact from Telegram communications."
    )
    telegram_bot_id = fields.Many2one(
        'telegram.bot', 
        string="Default Bot",
        help="The default Telegram bot used to communicate with this contact."
    )

    def send_telegram_message(self, text, telegram_template_id=None, bot=None, attachment_ids=None):
        """Send a Telegram message directly to this contact."""
        self.ensure_one()
        converted_message = text
        if telegram_template_id:
            converted_message = telegram_template_id.render_template(text, record=self)

        if not self.telegram_opt_in:
            raise ValidationError(_("Telegram messaging is disabled for this contact."))
        if not self.telegram_chat_id:
            raise ValidationError(_("Telegram Chat ID is missing. Please link the contact with Telegram."))

        bot = (bot or self.telegram_bot_id).sudo()
        if not bot:
            raise ValidationError(_("No Telegram Bot configured. Please set a default bot on the contact."))

        msg = self.env['telegram.message'].create({
            'direction': 'outgoing',
            'chat_id': self.telegram_chat_id,
            'partner_id': self.id,
            'telegram_template_id': telegram_template_id.id if telegram_template_id else False,
            'bot_id': bot.id,
            'res_model': 'res.partner',
            'res_id': self.id,
            'message_text': converted_message,
            'attachment_ids': [Command.set(attachment_ids)] if attachment_ids else False,
            'state': 'new',
        })
        msg.send_via_bot(converted_message, bot=bot)
        self.message_post(
            body=Markup("<b>Telegram Sent:</b><br/>%s") % escape(converted_message).replace('\n', Markup('<br/>')),
            attachment_ids=attachment_ids if attachment_ids else []
        )
        return True

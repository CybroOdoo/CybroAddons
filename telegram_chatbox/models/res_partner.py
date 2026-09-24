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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


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

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
from odoo import fields, models, _


class ResPartner(models.Model):
    """
    Inherited model to add Telegram specific configuration fields to Contacts.
    Allows linking a partner to a Telegram chat for direct messaging.
    """
    _inherit = "res.partner"

    telegram_chat_id = fields.Char(string="Telegram Chat ID", index=True)
    telegram_username = fields.Char(string="Telegram Username")
    telegram_opt_in = fields.Boolean(string="Allow Telegram Messages", default=True)
    telegram_bot_id = fields.Many2one('telegram.bot', string="Default Bot")

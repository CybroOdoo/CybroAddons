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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models
from odoo.addons.mail.tools.discuss import Store


class ResUsers(models.Model):
    """Inherit res.users model to add a Many2many field for favourite chats."""
    _inherit = 'res.users'

    mail_channel_ids = fields.Many2many(
        'discuss.channel',
        string='Favourite Channels',
        help='Favourite chats and channels associated with this user.',
    )

    def _store_init_fields(self, res: Store.FieldList):
        """Append mail_channel_ids to Store field list for current user."""
        result = super()._store_init_fields(res)
        res.many("mail_channel_ids", [])
        return result

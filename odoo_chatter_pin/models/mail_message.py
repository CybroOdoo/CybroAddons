# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
from odoo import api, fields, models


class Message(models.Model):
    """Adds pin/unpin support to chat messages."""
    _inherit = 'mail.message'

    is_pinned = fields.Boolean(string='Pinned', default=False, index=True,
                               help="Shows whether the message is pinned.")

    @api.model
    def message_fetch(self, domain, fields, limit=None, order='id desc'):
        """Override to always include pinned status"""
        if fields and 'is_pinned' not in fields:
            fields.append('is_pinned')
        return super(Message, self).message_fetch(domain, fields, limit=limit, order=order)

    def toggle_pin(self):
        """Toggle the pinned status of messages."""
        for message in self:
            message.is_pinned = not message.is_pinned
            self.env['bus.bus']._sendone(
                f'{self._name},{message.id}',
                'mail.message/pin_changed',
                {
                    'id': message.id,
                    'is_pinned': message.is_pinned,
                }
            )
        return True

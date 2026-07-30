# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class ResUsers(models.Model):
    """Inherit res.users to store user-specific chatter position preference."""
    _inherit = 'res.users'

    chatter_position = fields.Selection(
        [
            ('default', 'Default'),
            ('bottom', 'Bottom'),
            ('right', 'Right'),
        ],
        string='Chatter Position',
        default='default',
        help='Select the preferred position of the chatter panel in form views.'
    )


class IrHttp(models.AbstractModel):
    """Extend ir.http to include chatter position in session information."""
    _inherit = 'ir.http'

    def session_info(self):
        """Override session_info to include chatter position in the user session."""
        res = super().session_info()
        chatter_position = self.env.user.chatter_position or 'default'
        res.update({
            'chatter_position': chatter_position
        })
        if 'user_context' in res:
            res['user_context']['chatter_position'] = chatter_position
        return res

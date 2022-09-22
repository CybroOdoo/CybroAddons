# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions, (odoo@cybrosys.com)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import http
from odoo.http import request


class ChatFavourite(http.Controller):
    @http.route('/check_is_favourite', type='json', auth='user')
    def check_is_favourite(self, **kw):
        """Check whether the chat is favourite"""
        result = []
        channel_id = request.env['mail.channel'].search([('is_favourite', '=', True)])
        for rec in channel_id:
            result.append(rec.id)
        return result

    @http.route('/mark_is_favourite', type='json', auth='user')
    def mark_is_favourite(self, **kw):
        """Make the selected chat as  favourite"""
        active_id = kw.get('active_id')
        channel_id = request.env['mail.channel'].browse(active_id)
        return channel_id.id

    @http.route('/enable_favourite', type='json', auth='user')
    def enable_favourite(self, **kw):
        """Enable the favourite button if selected"""
        active_id = kw.get('active_id')
        channel_id = request.env['mail.channel'].browse(active_id)
        if channel_id:
            channel_id.is_favourite = True
        return channel_id.id

    @http.route('/disable_favourite', type='json', auth='user')
    def disable_favourite(self, **kw):
        """Disable the favourite button if deselected"""
        active_id = kw.get('active_id')
        channel_id = request.env['mail.channel'].browse(active_id)
        if channel_id:
            channel_id.is_favourite = False
        return channel_id.id

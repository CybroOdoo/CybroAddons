# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
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
###############################################################################
from odoo import Command, http
from odoo.http import request


class ChatFavourite(http.Controller):
    """Controller Class is created to handle the favourite chat functions"""

    @http.route('/enable_favourite', type='json', auth='user')
    def enable_favourite(self, **kwargs):
        """Enable the favourite button if selected"""
        active_id = kwargs.get('active_id')
        user_id = kwargs.get('user_id')  # Directly from the JS
        user = request.env['res.users'].sudo().browse(int(user_id))
        user.mail_channel_ids = [Command.link(int(active_id))]
        return active_id

    @http.route('/disable_favourite', type='json', auth='user')
    def disable_favourite(self, **kwargs):
        """Disable the favourite button if deselected"""
        active_id = kwargs.get('active_id')
        user_id = kwargs.get('user_id')
        user = request.env['res.users'].sudo().browse(int(user_id))
        user.mail_channel_ids = [Command.unlink(int(active_id))]
        return active_id

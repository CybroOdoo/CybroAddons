# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import http
from odoo.http import request


class DynamicDashboard(http.Controller):
    """
    This is the class DynamicDashboard which is the subclass of the class
    http.Controller
    """

    @http.route('/create/tile', type='json', auth='user')
    def tile_creation(self, **kw):
        """This is the method to create the tile when create on the button
        ADD BLOCK"""
        tile_type = kw.get('type')
        action_id = kw.get('action_id')
        request.env['dashboard.block'].get_dashboard_vals(action_id)
        tile_id = request.env['dashboard.block'].sudo().create({
            'name': 'New Block',
            'type': tile_type,
            'tile_color': '#1f6abb',
            'text_color': '#FFFFFF',
            'fa_icon': 'fa fa-money',
            'fa_color': '#132e45',
            'edit_mode': True,
            'client_action': int(action_id),
        })
        return {'id': tile_id.id, 'name': tile_id.name, 'type': tile_type, 'icon': 'fa fa-money',
                'color': '#1f6abb',
                'tile_color': '#1f6abb',
                'text_color': '#FFFFFF',
                'icon_color': '#1f6abb'}

    @http.route('/get/values', type='json', auth='user')
    def get_value(self, **kw):
        """This is the method get_value which will get the records inside the
        tile"""
        action_id = kw.get('action_id')
        datas = request.env['dashboard.block'].get_dashboard_vals(action_id)
        return datas

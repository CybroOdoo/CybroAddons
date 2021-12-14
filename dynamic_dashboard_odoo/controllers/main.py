# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError


class DynamicDashboard(http.Controller):

    @http.route('/create/tile', type='json', auth='user')
    def tile_creation(self, **kw):
        """While clicking ADD Block"""
        type = kw.get('type')
        action_id = kw.get('action_id')
        tile_id = request.env['dashboard.block'].sudo().create({
            'name': 'New Block',
            'type': type,
            'tile_color': '#1f6abb',
            'text_color': '#FFFFFF',
            'fa_icon': 'fa fa-money',
            'edit_mode': True,
            'client_action': int(action_id),
        })

        return {'id': tile_id.id, 'name': tile_id.name, 'type': type, 'icon': 'fa fa-money',
                'color': 'background-color: #1f6abb;',
                'text_color': 'color: #FFFFFF',
                'icon_color': 'color: #1f6abb'}

    @http.route('/tile/details', type='json', auth='user')
    def tile_details(self, **kw):
        tile_id = request.env['dashboard.block'].sudo().search([('id', '=', kw.get('id'))])
        if tile_id:
            return {'model': tile_id.model_id.model, 'filter': tile_id.filter, 'model_name': tile_id.model_id.name}
        return False

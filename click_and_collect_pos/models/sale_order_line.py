# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """here user can identify click and collect order"""
    _inherit = 'sale.order.line'

    is_click_and_collect = fields.Boolean(
        string='Collect', help='if you want to enable click and collect for '
                               'this product enable this field')
    pos_config_id = fields.Many2one('pos.config',
                                    string='PoS Session',
                                    help='Select pos session')

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Load pos data fields"""
        return []

    @api.model
    def _load_pos_data_domain(self, data):
        """Load pos data domain"""
        return []

    def _load_pos_data(self, data):
        """Load pos data"""
        domain = self._load_pos_data_domain(data)
        fields = self._load_pos_data_fields(data['pos.config']['data'][0]['id'])
        return {
            'data': self.search_read(domain, fields, load=False) if domain is not False else [],
            'fields': fields,
        }

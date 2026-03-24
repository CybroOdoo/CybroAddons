# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjali VP (Contact : odoo@cybrosys.com)
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
from odoo import models, fields, api, _

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    custom_uom_name = fields.Char(string='Custom UoM Name')
    custom_uom_price = fields.Float(string='Custom UoM Price')

    @api.model
    def _load_pos_data_fields(self, config):
        """Include custom UoM fields so they are sent to the POS frontend when
        loading saved/shared orders in a different POS session."""
        fields = super()._load_pos_data_fields(config)
        fields += ['custom_uom_name', 'custom_uom_price']
        return fields

    @api.model
    def _order_line_fields(self, line, session_id=None):
        """Updating order line fields to include custom UoM name and price."""
        fields_res = super(PosOrderLine, self)._order_line_fields(line, session_id)
        if line[2].get('custom_uom_name'):
            fields_res[2].update({'custom_uom_name': line[2].get('custom_uom_name')})
        if line[2].get('custom_uom_price'):
            fields_res[2].update({'custom_uom_price': line[2].get('custom_uom_price')})
        return fields_res

# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models


class PosOrderLine(models.Model):
    """
    Inherits pos.order.line to add washing type tracking for POS order lines.
    """
    _inherit = 'pos.order.line'

    washing_type_id = fields.Many2one('washing.type',
                                      string='Washing Type',
                                      help='The many2one filed that related'
                                           ' to the washing type')

    @api.model
    def _load_pos_data_fields(self, config_id):
        """
        Load pos data fields for the given config id.
        """
        fields = super()._load_pos_data_fields(config_id)
        fields += ['washing_type_id']
        return fields

    def _export_for_ui(self, orderline):
        """super the exporting function in the pos order line"""
        result = super()._export_for_ui(orderline)
        result['washing_type_id'] = \
            orderline.washing_type.read(fields=['name'])[0]
        return result

    def _order_line_fields(self, line, session_id):
        """
            Adding order-line details in the pos orders
        """
        result = super()._order_line_fields(line, session_id)
        vals = result[2]
        washing_type_id_custom = line[2].get('washing_type_id_custom')
        new_values = {'washing_type_id': int(washing_type_id_custom) if washing_type_id_custom else False}
        vals.update(new_values)
        return result

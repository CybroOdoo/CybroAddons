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
    """ This class is inherited for model pos_order_line.
            It contains field and the functions for the model

            Methods:
                _export_for_ui(self, orderline):
                    Supering the export_for_ui function for generating
                    the washing type in the order line for the model.

                _order_line_fields(self, line, session_id):
                    Action perform to adding order-line details in the pos orders.
    """
    _inherit = 'pos.order.line'

    washing_type_id = fields.Many2one('washing.type',
                                      string='Washing Type',
                                      help='The many2one field that related'
                                           ' to the washing type')

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Add washing_type_id to the list of fields to load in POS"""
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
        washing_type_id = line[2].get('washingType_id')
        new_values = {'washing_type_id': int(washing_type_id) if washing_type_id else False}
        vals.update(new_values)
        return result

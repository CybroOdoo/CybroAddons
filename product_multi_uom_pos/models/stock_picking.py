# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (Contact : odoo@cybrosys.com)
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
from odoo import models


class StockPicking(models.Model):
    """Inherits model 'stock.picking' and updates unit of measure in move
    lines"""
    _inherit = 'stock.picking'

    def _prepare_stock_move_vals(self, first_line, order_lines):
        """Updates unit of measure in move lines"""
        for line in order_lines:
            self._cr.execute(
                """select * from pos_order_line where id = %s""" % (line.id))
            uom_id = self._cr.dictfetchall()[0]['uom_id']
            return {
                'name': first_line.name,
                'product_uom': uom_id,
                'picking_id': self.id,
                'picking_type_id': self.picking_type_id.id,
                'product_id': first_line.product_id.id,
                'product_uom_qty': abs(sum(order_lines.mapped('qty'))),
                'state': 'draft',
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'company_id': self.company_id.id,
            }

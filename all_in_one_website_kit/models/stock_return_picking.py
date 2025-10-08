# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
from odoo import models


class StockReturnPicking(models.TransientModel):
    """Inherit stock.return.picking and adding function"""
    _inherit = 'stock.return.picking'

    def _create_returns(self):
        """for creating return orders"""
        new_picking, pick_type_id = super(
            StockReturnPicking,self)._create_returns()
        picking = self.env['stock.picking'].browse(new_picking)
        if self.picking_id.return_order_id:
            picking.write({'return_order_picking': False,
                           'return_order_id': False,
                           'return_order_pick_id':
                               self.picking_id.return_order_id.id})
            self.picking_id.return_order_id.write({'state': 'confirm'})
        return new_picking, pick_type_id

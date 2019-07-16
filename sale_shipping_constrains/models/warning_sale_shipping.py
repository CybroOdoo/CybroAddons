# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2016-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, api
from openerp.tools.translate import _
from openerp.exceptions import UserError


class StockMoveWarning(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def onchange_quantity(self, product_id, product_qty, product_uom):
        qty_sales = 0
        for orders in self.env['sale.order'].search([('name', '=', self.picking_id.origin)]).order_line:
            if orders.product_id == product_id:
                qty_sales += orders.product_uom_qty
        if product_qty > qty_sales:
            raise UserError(_('You are trying to deliver more than ordered quantity'))
        return super(StockMoveWarning, self).onchange_quantity(product_id, product_qty, product_uom)

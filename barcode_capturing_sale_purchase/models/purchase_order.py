# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Rahul CK(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, models


class PurchaseOrder(models.Model):
    """Module is inherited and function is created to create a purchase
    order line with the scanned barcode of product"""
    _inherit = 'purchase.order'

    @api.model
    def barcode_search(self, args):
        """Purchase Order line is created and product is added by checking
        the barcode. args contains the barcode of product and purchase order
        id"""
        product = self.env['product.product'].search([('barcode', '=',
                                                       args[0])])
        if not product:
            return True
        else:
            purchase_order = self.browse(args[1])
            if purchase_order.order_line:
                for rec in purchase_order.order_line:
                    if rec.product_id == product:
                        rec.product_qty += 1
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'reload',
                        }
            purchase_order.order_line.create({
                'order_id': purchase_order.id,
                'product_id': product.id,
                'product_uom_qty': 1
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
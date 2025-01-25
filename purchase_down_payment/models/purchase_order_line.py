# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ashwin T(odoo@cybrosys.com)
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
##############################################################################
from odoo import fields, models


class PurchaseOrderLine(models.Model):
    """
            The class is created for inherited the model purchase.order.line.

            Methods:
                _prepare_invoice_line():
                    Function to add the invoice lines of down payment
    """
    _inherit = 'purchase.order.line'

    is_downpayment = fields.Boolean(
        string="Is a down payment", help="Down payments are made when "
                                         "creating Bills from a purchase order."
                                         "They are not copied when "
                                         "duplicating a purchase order.")

    def _prepare_invoice_line(self, **optional_values):
        """
        Prepare the dict of values to create the new bill line for a purchase
        order line. :param qty: float quantity to bill :param
        optional_values: any parameter that should be added to the returned
        bill line
        """
        self.ensure_one()
        res = {
            'display_type': 'product',
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'price_unit': self.price_unit,
            'purchase_line_id': self.id,
        }
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res

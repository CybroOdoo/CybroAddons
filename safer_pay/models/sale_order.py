# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
#
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    """For getting get_portal_last_transaction method in sale order"""
    _inherit = 'sale.order'

    payment = fields.Boolean(string="Payment", help="For payment details")
    sale_order = fields.Integer(string="Sale order Number",
                                help="To get sale order")

    def get_portal_last_transaction(self):
        """For updating the transaction"""
        super().get_portal_last_transaction()
        self.ensure_one()
        if self.transaction_ids:
            code = self.transaction_ids.provider_id.id
            provider = self.env.ref('safer_pay.payment_acquirer_data').id
            sale_order = self.env['sale.order'].search(
                [('transaction_ids', 'in', self.transaction_ids.ids)])
            if (sale_order.id == sale_order.sale_order and
                    not sale_order.payment and code == provider):
                self.transaction_ids.write({
                    'state': 'done'
                })
        return self.transaction_ids._get_last()

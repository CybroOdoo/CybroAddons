# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#############################################################################
from odoo import models


class SaleAdvancePaymentInv(models.TransientModel):
    """Inheriting the model of sale.advance.payment.inv to generate advance
     payment of invoice"""
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        """Create invoices for the laundry sale order using Odoo's wizard."""
        laundry_sale_id = self.env.context.get('laundry_sale_id')
        if laundry_sale_id:
            self.sale_order_ids = self.env['sale.order'].browse(laundry_sale_id)
        return super().create_invoices()

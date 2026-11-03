# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import models


class PurchaseOrder(models.Model):
    """
    Inherits Purchase Order to ensure lot creation upon order confirmation.
    """
    _inherit = 'purchase.order'

    def button_confirm(self):
        for order in self:
            for line in order.order_line:
                if line.is_lot_product and not line.lot_id:
                    line._ensure_custom_stock_lot()
        return super().button_confirm()

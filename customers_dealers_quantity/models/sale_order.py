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
from odoo import api, models


class SaleOrder(models.Model):
    """This class is to set the dealer price"""
    _inherit = "sale.order"

    @api.onchange('partner_id')
    def _onchange_partner_id_dealer_price(self):
        """Triggered when the 'partner_id' field is changed.
        This method iterates through the order lines and recomputes the price unit.
        """
        for line in self.order_line:
            line._compute_price_unit()

    def _onchange_partner_id(self):
        """Compatibility wrapper in case _onchange_partner_id is called directly."""
        res = None
        if hasattr(super(), '_onchange_partner_id'):
            res = super()._onchange_partner_id()
        self._onchange_partner_id_dealer_price()
        return res
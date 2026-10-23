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
from odoo import api, fields, models


class SaleOrder(models.Model):
    """Inherits 'sale.order' and adds new field"""
    _inherit = 'sale.order'

    is_delivery_split = fields.Boolean(string='Delivery Split',
                                       help='Enable the option to add recipients '
                                            'to each sale order line to split '
                                            'the delivery')
    is_consolidate = fields.Boolean(string='Consolidate Orders',
                                    help='Enable the option to consolidate '
                                         'orders if the same recipient is chosen '
                                         'in split delivery')

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """ Update recipients in order lines when the customer of the sale order
        is changed """
        if self.is_delivery_split:
            for line in self.order_line:
                line.recipient_id = self.partner_id.id

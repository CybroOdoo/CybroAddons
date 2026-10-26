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
    """Inheriting Sale Order model to activate the
       price-list based on customer group."""
    _inherit = 'sale.order'

    @api.depends('partner_id')
    def _compute_pricelist_id(self):
        super()._compute_pricelist_id()
        for order in self:
            if order.state != 'draft' or not order.partner_id:
                continue
            group = self.env['customer.group'].search([
                ('contact_ids', 'in', order.partner_id.id),
                ('pricelist_id', '!=', False),
            ], limit=1)
            if group:
                order.pricelist_id = group.pricelist_id

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Price list will be added based on the customer group"""
        for order in self:
            if not order.partner_id:
                continue
            group = self.env['customer.group'].search([
                ('contact_ids', 'in', order.partner_id.id),
                ('pricelist_id', '!=', False),
            ], limit=1)
            if group:
                order.pricelist_id = group.pricelist_id


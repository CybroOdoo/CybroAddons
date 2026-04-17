# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
#
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    """The module is used to add the approval state in the product form page"""
    _inherit = 'product.product'

    approve_state = fields.Selection([('draft', 'Draft'),
                                      ('confirmed', 'Confirmed')],
                                     default='draft', string='State',
                                     help='State to approve',
                                     tracking=True)

    def action_confirm_product_approval(self):
        """Confirm button on the product form page"""
        for rec in self:
            rec.approve_state = 'confirmed'

    def action_reset_product_approval(self):
        """Reset to295.00 draft state button on the product form page"""
        for rec in self:
            rec.approve_state = 'draft'

    def action_confirm_products(self):
        """Bulk product approval button on the product form page"""
        active_ids = self.env.context.get('active_ids')
        products = self.env['product.product'].browse(active_ids)
        products.action_confirm_product_approval()

    def write(self, vals):
        """Reset to draft if any field is modified and the variant was confirmed."""
        if 'approve_state' not in vals:
            for rec in self:
                if rec.approve_state == 'confirmed':
                    rec.action_reset_product_approval()
        return super(ProductTemplate, self).write(vals)

    def _is_variant_possible(self, parent_combination=None):
        """Only confirmed variants are considered possible in the configurator and elsewhere."""
        res = super()._is_variant_possible(parent_combination=parent_combination)
        return res and self.approve_state == 'confirmed'

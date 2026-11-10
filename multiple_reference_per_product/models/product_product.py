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


class ProductProductInherit(models.Model):
    """Inherit the 'product_product' model to include Multiple References in
    the form view."""
    _inherit = 'product.product'

    multiple_references_ids = fields.One2many("multiple.reference.per.product",
                                              "product_id",
                                              string="Multiple Reference Lines",
                                              help="Choose Multiple Reference"
                                                   " per Product and checks "
                                                   "simultaneously")
    multiple_references_code = fields.Char(string="Multiple Reference Codes",
                                           related="multiple_references_ids"
                                                   ".multiple_references_name",
                                           search="_search_multiple_references_code",
                                           help="Enter Code for Multiple "
                                                "Reference")

    def _search_multiple_references_code(self, operator, value):
        """Search method for multiple_references_code on product.product."""
        return [('multiple_references_ids.multiple_references_name', operator, value)]
    multiple_product_references_ids = fields.Many2many(
        "multiple.reference.per.product",
        string="Multiple References",
        compute="_compute_multiple_product_references_ids",
        help="Choose Multiple Reference"
             "per Product")
    multiple_references_count = fields.Integer(string="Number of references",
                                               compute="_compute_multiple_references_count",
                                               help="Enter Number of Reference")

    @api.depends('multiple_references_ids')
    def _compute_multiple_references_count(self):
        """Function to get the count of reference code"""
        for product in self:
            product.multiple_references_count = len(product.multiple_references_ids)

    @api.depends('multiple_references_ids.multiple_references_name', 'default_code')
    def _compute_multiple_product_references_ids(self):
        """Function for getting all Multiple References"""
        for product in self:
            product.multiple_product_references_ids = product.multiple_references_ids.filtered(
                lambda references: references.multiple_references_name != product.default_code
            )

    def multiple_references_list(self):
        """Function to open the Multiple References form and tree view
        when clicking the 'Add More' button."""
        self.ensure_one()
        return {
            'name': "Multiple References",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_model': 'multiple.reference.per.product',
            'views': [[False, "list"], [False, "form"]],
            'context': {'default_product_id': self.id},
            'domain': [('product_id', '=', self.id)],
        }

    def write(self, values):
        """Function for update the Product Reference"""
        if values.get('default_code'):
            for product in self:
                if product.default_code:
                    self.env['multiple.reference.per.product'].create_reference(
                        product.default_code, product.id
                    )
        return super().write(values)

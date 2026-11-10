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


class ProductTemplateInherit(models.Model):
    """Inherit product_template model for adding multiple_reference_code"""
    _inherit = 'product.template'

    multiple_references_code = fields.Char(string="Multiple Reference Codes",
                                           related="product_variant_ids"
                                                   ".multiple_references_ids"
                                                   ".multiple_references_name",
                                           search="_search_multiple_references_code",
                                           help="Enter Code for Multiple "
                                                "Reference")

    def _search_multiple_references_code(self, operator, value):
        """Search method for multiple_references_code traversing variants and references."""
        return [('product_variant_ids.multiple_references_ids.multiple_references_name', operator, value)]
    multiple_product_references_ids = fields.Many2many(
        "multiple.reference.per.product",
        string="Multiple References",
        compute="_compute_multiple_product_references_ids",
        help="Choose Multiple Reference"
             " per Product")
    multiple_references_count = fields.Integer(string="Number of References",
                                               compute="_compute_multiple_references_count",
                                               help="Enter Number of Reference")

    @api.depends('multiple_product_references_ids')
    def _compute_multiple_references_count(self):
        """Function for getting total count of References"""
        for template in self:
            template.multiple_references_count = len(
                template.multiple_product_references_ids
            )

    @api.depends('product_variant_ids.multiple_product_references_ids', 'default_code')
    def _compute_multiple_product_references_ids(self):
        """Function for getting all Multiple References"""
        for template in self:
            template.multiple_product_references_ids = template.product_variant_ids.mapped(
                'multiple_product_references_ids'
            ).filtered(
                lambda references: references.multiple_references_name != template.default_code
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
            'context': {'default_product_id': self.product_variant_id.id},
            'domain': [('product_id', '=', self.product_variant_id.id)],
        }

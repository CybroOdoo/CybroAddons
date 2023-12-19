# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Farhana Jahan PT (odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class ProductTemplateInherit(models.Model):
    """Inherit product_template model for adding multiple_reference_code"""
    _inherit = 'product.template'

    multiple_references_code = fields.Char(string="Multiple References",
                                           related="product_variant_ids"
                                                   ".multiple_references_ids"
                                                   ".multiple_references_name",
                                           help="Enter Code for Multiple "
                                                "Reference")
    multiple_product_references_ids = fields.Many2many(
        "multiple.reference.per.product",
        string="Multiple References",
        compute="_get_multiple_reference",
        help="Choose Multiple Reference"
             " per Product")
    multiple_references_count = fields.Integer(string="Number of References",
                                               compute="_get_multiple_reference_count",
                                               help="Enter Number of Reference")

    @api.depends('multiple_product_references_ids')
    def _get_multiple_reference_count(self):
        """Function for getting total count of References"""
        self.multiple_references_count = len(
            self.multiple_product_references_ids)

    def _get_multiple_reference(self):
        """Function for getting all Multiple References"""
        self.multiple_product_references_ids = self.product_variant_ids.mapped(
            'multiple_product_references_ids').filtered(lambda
                                                            references: references.multiple_references_name != self.default_code).ids

    def multiple_references_list(self):
        """Function to open the Multiple References form and tree view
        when clicking the 'Add More' button."""
        return {
            'name': "Multiple References",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_model': 'multiple.reference.per.product',
            'views': [[False, "tree"], [False, "form"]],
            'context': {'default_product_id': self.product_variant_id.id},
            'domain': [('product_id', '=', self.product_variant_id.id)],
        }

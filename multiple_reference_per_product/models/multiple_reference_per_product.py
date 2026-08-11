# -*- coding: utf-8 -*-
###############################################################################
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
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class MultipleReferencePerProduct(models.Model):
    """Create a new model for managing multiple references."""
    _name = 'multiple.reference.per.product'
    _description = 'Multiple Reference Per Product'
    _rec_name = 'multiple_references_name'

    multiple_references_name = fields.Char(string='Multiple References',
                                           required=True,
                                           help="Name for Multiple Reference")
    product_id = fields.Many2one('product.product', string="Product",
                                 required=True,
                                 help="Choose Product for Multiple Reference")
    is_default_reference = fields.Boolean(string="Is Default Reference",
                                          compute='_is_default_reference',
                                          help="Checks it is Default Reference"
                                               " or not")

    def _is_default_reference(self):
        """Check if the current code is default code for the product"""
        for reference in self:
            if reference.product_id:
                reference.is_default_reference = True if reference.product_id.default_code == reference.multiple_references_name else False

    def action_set_as_default(self):
        """Set the current code as default code for the product"""
        self.ensure_one()
        self.product_id.default_code = self.multiple_references_name

    def create_reference(self, reference_code, product_id):
        """Add existing default code into the reference model"""
        reference = self.create({
            'multiple_references_name': reference_code,
            'product_id': product_id,
        })
        return True if reference else False

    @api.model_create_multi
    def create(self, vals_list):
        """Prevent duplicate references when adding new records.
        If a duplicate is found, return the existing record instead of creating a new one.
        """
        records = self.env[self._name]

        for values in vals_list:
            if values.get('multiple_references_name') and values.get('product_id'):
                existing = self.search([
                    ('multiple_references_name', '=', values['multiple_references_name']),
                    ('product_id', '=', values['product_id']),
                ], limit=1)

                if existing:
                    if not existing.product_id.default_code:
                        existing.product_id.default_code = existing.multiple_references_name
                    records |= existing
                else:
                    new_record = super(MultipleReferencePerProduct, self).create([values])
                    records |= new_record
            else:
                new_record = super(MultipleReferencePerProduct, self).create([values])
                records |= new_record

        return records

    def write(self, values):
        """Function to eliminate duplicate references when editing details."""
        multiple_references_name = values.get('multiple_references_name')
        multiple_references_name = [
            multiple_references_name] if multiple_references_name else self.mapped(
            'name')
        product_id = values.get('product_id')
        product_ids = [product_id] if product_id else self.mapped(
            'product_id').ids
        reference_code = self.search(
            [('multiple_references_name', 'in', multiple_references_name),
             ('product_id', 'in', product_ids)])
        if reference_code:
            return False
        return super(MultipleReferencePerProduct, self).write(values)

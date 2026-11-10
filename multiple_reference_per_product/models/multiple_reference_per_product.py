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
from odoo.exceptions import ValidationError


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
                                          compute='_compute_is_default_reference',
                                          help="Checks it is Default Reference"
                                               " or not")

    @api.depends('product_id', 'product_id.default_code', 'multiple_references_name')
    def _compute_is_default_reference(self):
        """Check if the current code is default code for the product"""
        for reference in self:
            if reference.product_id:
                reference.is_default_reference = reference.product_id.default_code == reference.multiple_references_name
            else:
                reference.is_default_reference = False

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
        res = super().write(values)
        for record in self:
            duplicate = self.search([
                ('id', '!=', record.id),
                ('product_id', '=', record.product_id.id),
                ('multiple_references_name', '=', record.multiple_references_name),
            ], limit=1)
            if duplicate:
                raise ValidationError(
                    self.env._(
                        "The reference '%(reference)s' already exists for product '%(product)s'.",
                        reference=record.multiple_references_name,
                        product=record.product_id.display_name,
                    )
                )
        return res

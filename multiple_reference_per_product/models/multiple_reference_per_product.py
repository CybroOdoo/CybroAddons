# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
#############################################################################

from odoo import models, fields, api


class MultipleReferencePerProduct(models.Model):
    _name = 'multiple.reference.per.product'
    _description = 'Multiple Reference Per Product'
    _rec_name = 'multiple_references_name'

    multiple_references_name = fields.Char('Multiple References', required=True)
    product_id = fields.Many2one('product.product', string="Product", required=True)
    is_default_reference = fields.Boolean(string="Is default reference", compute='_is_default_reference')

    def _is_default_reference(self):
        """Check if the current code is default code for the product"""
        for reference in self:
            if reference.product_id:
                reference.is_default_reference = True if reference.product_id.default_code == reference.multiple_references_name else False

    def set_as_default(self):
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

    @api.model
    def create(self, values):
        if values.get('multiple_references_name') and values.get('product_id'):
            reference_code = self.search([('multiple_references_name', '=', values.get('multiple_references_name')), ('product_id', '=', values.get('product_id'))])
            print(reference_code)

            if reference_code:
                res = reference_code[0]
            else:
                res = super(MultipleReferencePerProduct, self).create(values)

            if not res.product_id.default_code:
                res.product_id.default_code = res.multiple_references_name
            return res

        else:
            res = super(MultipleReferencePerProduct, self).create(values)
            return res

    def write(self, values):
        multiple_references_name = values.get('multiple_references_name')
        multiple_references_name = [multiple_references_name] if multiple_references_name else self.mapped('name')

        product_id = values.get('product_id')
        product_ids = [product_id] if product_id else self.mapped('product_id').ids

        reference_code = self.search([('multiple_references_name', 'in', multiple_references_name), ('product_id', 'in', product_ids)])

        if reference_code:
            return False

        return super(MultipleReferencePerProduct, self).write(values)


class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    multiple_references_ids = fields.One2many("multiple.reference.per.product", "product_id", string="Multiple "
                                                                                                     "References")
    multiple_references_code = fields.Char(string="Multiple References", related="multiple_references_ids"
                                                                                 ".multiple_references_name")
    multiple_references_id = fields.Many2many("multiple.reference.per.product", string="Multiple References",
                                              compute="_get_multiple_reference")
    multiple_references_count = fields.Integer(string="NUmber of references", compute="_get_multiple_reference_count")

    @api.depends('multiple_references_id')
    def _get_multiple_reference_count(self):
        """Get the count of reference code"""
        self.multiple_references_count = len(self.multiple_references_ids)

    def _get_multiple_reference(self):
        self.multiple_references_id = self.multiple_references_ids.filtered(lambda references: references.multiple_references_name != self.default_code).ids

    def multiple_references_list(self):
        return {
            'name': "Multiple References",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_model': 'multiple.reference.per.product',
            'views': [[False, "tree"], [False, "form"]],
            'context': {'default_product_id': self.id},
            'domain': [('product_id', '=', self.id)],
        }

    def write(self, values):
        if values.get('default_code'):
            if self.default_code:
                self.env['multiple.reference.per.product'].sudo().create_reference(self.default_code, self.id)
        # print(values)
        res = super(ProductProductInherit, self).write(values)
        return res


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    multiple_references_code = fields.Char(string="Multiple References", related="product_variant_ids"
                                                                                 ".multiple_references_ids"
                                                                                 ".multiple_references_name")
    multiple_references_id = fields.Many2many("multiple.reference.per.product", string="Multiple References",
                                              compute="_get_multiple_reference")
    multiple_references_count = fields.Integer(string="NUmber of references", compute="_get_multiple_reference_count")

    @api.depends('multiple_references_id')
    def _get_multiple_reference_count(self):
        self.multiple_references_count = len(self.multiple_references_id)
        # print("Count",self.multiple_references_count)

    def _get_multiple_reference(self):
        self.multiple_references_id = self.product_variant_ids.mapped('multiple_references_id').filtered(lambda references: references.multiple_references_name != self.default_code).ids

    def multiple_references_list(self):
        return {
            'name': "Multiple References",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_model': 'multiple.reference.per.product',
            'views': [[False, "tree"], [False, "form"]],
            'context': {'default_product_id': self.product_variant_id.id},
            'domain': [('product_id', '=', self.product_variant_id.id)],
        }



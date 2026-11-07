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


class ProductMultiBarcode(models.Model):
    """Creating multiple barcode for products"""
    _name = 'product.multiple.barcodes'
    _description = 'Product Multiple Barcodes'
    _rec_name = 'product_multi_barcode'

    product_multi_barcode = fields.Char(
        string="Barcode",
        help="Provide alternate barcodes for the product",
    )
    product_id = fields.Many2one(
        'product.product',
        string="Product Variant",
        help="This will be the Product variants",
    )
    product_template_id = fields.Many2one(
        'product.template',
        string="Product",
        help="This will be the products",
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id and not self.product_template_id:
            self.product_template_id = self.product_id.product_tmpl_id

    @api.onchange('product_template_id')
    def _onchange_product_template_id(self):
        if self.product_template_id and not self.product_id:
            self.product_id = self.product_template_id.product_variant_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            pid = vals.get('product_id') or self.env.context.get('default_product_id')
            ptid = vals.get('product_template_id') or self.env.context.get('default_product_template_id')
            if pid and not vals.get('product_template_id'):
                product = self.env['product.product'].browse(pid)
                vals['product_template_id'] = product.product_tmpl_id.id
            elif ptid and not vals.get('product_id'):
                tmpl = self.env['product.template'].browse(ptid)
                if tmpl.product_variant_id:
                    vals['product_id'] = tmpl.product_variant_id.id
        records = super().create(vals_list)
        if not self.env.context.get('syncing_barcode'):
            for record in records:
                if record.product_id and not record.product_id.barcode:
                    record.product_id.with_context(syncing_barcode=True).barcode = record.product_multi_barcode
        return records

    def write(self, vals):
        if vals.get('product_id') and 'product_template_id' not in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            vals['product_template_id'] = product.product_tmpl_id.id
        res = super().write(vals)
        if not self.env.context.get('syncing_barcode') and 'product_multi_barcode' in vals:
            for record in self:
                if record.product_id:
                    first_barcode = record.product_id.multi_barcode_ids[:1].product_multi_barcode or False
                    if record.product_id.barcode != first_barcode:
                        record.product_id.with_context(syncing_barcode=True).barcode = first_barcode
        return res

    def unlink(self):
        products = self.mapped('product_id')
        res = super().unlink()
        if not self.env.context.get('syncing_barcode'):
            for product in products.exists():
                first_barcode = product.multi_barcode_ids[:1].product_multi_barcode or False
                if product.barcode != first_barcode:
                    product.with_context(syncing_barcode=True).barcode = first_barcode
        return res

    @api.constrains('product_multi_barcode', 'product_id')
    def _check_unique_barcode(self):
        """Ensure barcode uniqueness across records"""
        for record in self:
            if not record.product_multi_barcode:
                continue
            domain = [
                ('product_multi_barcode', '=', record.product_multi_barcode),
                ('id', '!=', record.id),
            ]
            if self.search_count(domain):
                raise ValidationError(
                    self.env._(
                        "Barcode '%(barcode)s' already exists!",
                        barcode=record.product_multi_barcode,
                    ),
                )

    def _resolve_product_variant(self):
        """
        Summary:
            Resolve the product.product record from a barcode entry.
            Works whether the barcode was linked via product_id (variant) or
            only via product_template_id.
        Returns:
            product.product record or empty recordset
        """
        self.ensure_one()
        if self.product_id:
            return self.product_id
        if self.product_template_id:
            return self.product_template_id.product_variant_id or self.product_template_id.product_variant_ids[:1]
        return self.env['product.product']

    @api.model
    def find_product_by_barcode(self, barcode):
        """
        Find a product.product record by barcode:
        1. Checks product.multiple.barcodes (multi-barcodes)
        2. Falls back to product.product.barcode (standard variant barcode)
        3. Falls back to product.template.barcode (standard template barcode)
        Returns a product.product record (singleton or empty recordset).
        """
        if not barcode:
            return self.env['product.product']
        barcode_clean = str(barcode).strip()
        # 1. Search in multi-barcodes (exact, then case-insensitive)
        multi_rec = self.search([('product_multi_barcode', '=', barcode_clean)], limit=1)
        if not multi_rec:
            multi_rec = self.search([('product_multi_barcode', '=ilike', barcode_clean)], limit=1)
        if multi_rec:
            product = multi_rec._resolve_product_variant()
            if product:
                return product
        # 2. Search in standard product.product barcode
        product = self.env['product.product'].search([('barcode', '=', barcode_clean)], limit=1)
        if not product:
            product = self.env['product.product'].search([('barcode', '=ilike', barcode_clean)], limit=1)
        if product:
            return product
        # 3. Search in standard product.template barcode
        template = self.env['product.template'].search([('barcode', '=', barcode_clean)], limit=1)
        if not template:
            template = self.env['product.template'].search([('barcode', '=ilike', barcode_clean)], limit=1)
        if template:
            return template.product_variant_id or template.product_variant_ids[:1]
        return self.env['product.product']

    def get_barcode_val(self, product):
        """
        Summary:
            get barcode of record in self and product id
        Args:
            product(int): current product
        Returns:
            barcode of the record in self and product
        """
        return self.product_multi_barcode, product

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


class ProductProduct(models.Model):
    """Inherits Products for multiple barcodes"""
    _inherit = 'product.product'

    multi_barcode_ids = fields.One2many(
        'product.multiple.barcodes',
        'product_id',
        string='Barcodes',
        help='Set multiple barcodes for the product',
    )

    @api.model
    def _expand_barcode_domain(self, domain):
        """Expand domain filters on 'barcode' to also match alternate barcodes in multi_barcode_ids."""
        if not domain:
            return domain
        new_domain = []
        for leaf in domain:
            if isinstance(leaf, (list, tuple)) and len(leaf) == 3 and leaf[0] == 'barcode':
                field, op, val = leaf
                new_domain.extend(['|', (field, op, val), ('multi_barcode_ids.product_multi_barcode', op, val)])
            else:
                new_domain.append(leaf)
        return new_domain

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None,
                    order=None, **kwargs):
        """For searching the product with multi barcode"""
        domain = self._expand_barcode_domain(domain)
        return super().search_read(
            domain=domain, fields=fields, offset=offset,
            limit=limit, order=order, **kwargs,
        )

    @api.model_create_multi
    def create(self, vals_list):
        """Creating multi barcodes and ensuring barcode exists in lines"""
        for vals in vals_list:
            if vals.get('barcode') and not vals.get('multi_barcode_ids'):
                vals['multi_barcode_ids'] = [
                    fields.Command.create({
                        'product_multi_barcode': vals['barcode'],
                    }),
                ]
        res = super().create(vals_list)
        for product in res:
            if product.multi_barcode_ids:
                product.multi_barcode_ids.write({
                    'product_template_id': product.product_tmpl_id.id,
                })
        return res

    def write(self, vals):
        """Updating multi barcodes and keeping barcode in sync"""
        if self.env.context.get('syncing_barcode'):
            return super().write(vals)

        res = super().write(vals)
        for product in self.with_context(syncing_barcode=True):
            if product.multi_barcode_ids:
                product.multi_barcode_ids.write({
                    'product_template_id': product.product_tmpl_id.id,
                })

            # When barcode is updated directly, add it to multi_barcode_ids if missing
            if 'barcode' in vals and vals.get('barcode'):
                existing_barcodes = product.multi_barcode_ids.mapped('product_multi_barcode')
                if vals['barcode'] not in existing_barcodes:
                    product.write({
                        'multi_barcode_ids': [fields.Command.create({
                            'product_multi_barcode': vals['barcode'],
                            'product_template_id': product.product_tmpl_id.id,
                        })],
                    })

            # When multi_barcode_ids lines are modified, sync primary barcode with first line
            if 'multi_barcode_ids' in vals:
                first_barcode = product.multi_barcode_ids[:1].product_multi_barcode or False
                if product.barcode != first_barcode:
                    product.barcode = first_barcode

        return res

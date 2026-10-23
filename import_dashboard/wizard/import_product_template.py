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
from .import_utils import get_file_content, read_csv_data, read_xlsx_data
from odoo.exceptions import ValidationError
from odoo import fields, models


class ImportProductTemplate(models.TransientModel):
    """ Model for import product template. """
    _name = 'import.product.template'
    _description = 'Product Template Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xls', 'Excel File')],
        string='Select File Type', default='csv', help="Type of the file to import")
    method = fields.Selection(selection=[('create_product', 'Create Product'),
                                         ('update_product',
                                          'Create or Update Product')],
                              default='create_product',
                              help="Create new products only, or also update existing ones")
    import_product_by = fields.Selection(
        selection=[('name', 'Name'),
                   ('internal_reference', 'Internal Reference'),
                   ], string="Match Products By",
        default='name', help="Product field used to match existing products")
    file_upload = fields.Binary(help="File to import")

    def action_import_product_template(self):
        """Creating product record using uploaded xl/csv files"""
        items = []
        if self.file_type == 'csv':
            try:
                items = read_csv_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the file format and try again!")
                )

        elif self.file_type == 'xls':
            try:
                items = read_xlsx_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the file format and try again!")
                )
        else:
            raise ValidationError(self.env._("Unsupported file type."))

        PRODUCT_TYPE_MAP = {
            'goods': 'consu',
            'consu': 'consu',
            'product': 'consu',
            'storable': 'consu',
            'service': 'service',
            'combo': 'combo',
        }
        created = 0
        updated = 0
        for item in items:
            product = False
            raw_type = (item.get('Product Type') or '').strip().lower()
            product_type = PRODUCT_TYPE_MAP.get(raw_type)

            if not product_type:
                raise ValidationError(self.env._(
                    "Invalid Product Type '%s'.\n"
                    "Allowed values: consu (Goods), service, combo, storable",
                    item.get('Product Type'),
                ))
            vals = {
                "name": item.get('Name'),
                "type": product_type,
                "default_code": item.get('Internal Reference'),
                "list_price": item.get('Sales Price') or 0.0,
                "standard_price": item.get('Cost') or 0.0,
            }
            if raw_type in ('storable', 'product') and 'is_storable' in self.env['product.template']._fields:
                vals['is_storable'] = True
            if self.method == "create_product":
                product = self.env['product.template'].search(
                    [('name', '=', item.get('Name'))],
                    limit=1
                )
            elif self.method == "update_product":
                if self.import_product_by == "name":
                    product = self.env['product.template'].search(
                        [('name', '=', item.get('Name'))],
                        limit=1
                    )
                elif self.import_product_by == "internal_reference":
                    product = self.env['product.template'].search(
                        [('default_code', '=', item.get('Internal Reference'))],
                        limit=1
                    )
                if product:
                    product.write(vals)
                    updated += 1
            if not product:
                self.env['product.template'].create(vals)
                created += 1

        msg = self.env._("Imported %(created)d records.\nUpdated %(updated)d records.", created=created, updated=updated)
        self.env['import.message'].create({'message': msg})
        return {
            'effect': {
                'fadeout': 'slow',
                'message': msg,
                'type': 'rainbow_man',
            }
        }

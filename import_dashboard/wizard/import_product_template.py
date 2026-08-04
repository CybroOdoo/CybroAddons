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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import binascii
import csv
import io
import tempfile
import os
import openpyxl
from odoo.exceptions import ValidationError
from odoo import fields, models, _


class ImportProductTemplate(models.TransientModel):
    """ Model for import product template. """
    _name = 'import.product.template'
    _description = 'Product Template Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xls', 'Excel File')],
        string='Select File Type', default='csv', help="file type")
    method = fields.Selection(selection=[('create_product', 'Create Product'),
                                         ('update_product',
                                          'Create or Update Product')],
                              string='Method', default='create_product',
                              help="method")
    import_product_by = fields.Selection(
        selection=[('name', 'Name'),
                   ('internal_reference', 'Internal Reference'),
                   ], string="Product Update By",
        default='name', help="It helps to import product")
    file_upload = fields.Binary(string='File Upload',
                                help="It helps to upload file")

    def action_import_product_template(self):
        """Creating product record using uploaded xl/csv files"""

        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                items = csv.DictReader(data_file, delimiter=',')
            except Exception:
                raise ValidationError(
                    "File not valid.\n\nPlease check the file format and try again!"
                )


        elif self.file_type == 'xls':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload))
                fp.flush()
                fp.close()
                workbook = openpyxl.load_workbook(fp.name, data_only=True)
                sheet = workbook.active
            except Exception:
                raise ValidationError(
                    "File not valid.\n\nPlease check the file format and try again!"
                )
            rows = list(sheet.iter_rows(values_only=True))
            headers = list(rows[0]) if rows else []
            items = []
            for row in rows[1:]:
                if all(c is None or str(c).strip() == '' for c in row):
                    continue
                items.append({k: v for k, v in zip(headers, row) if k is not None})
            try:
                os.unlink(fp.name)
            except Exception:
                pass
        else:
            raise ValidationError("Unsupported file type.")

        PRODUCT_TYPE_MAP = {
            'goods': 'consu',
            'consu': 'consu',
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
                raise ValidationError(
                    f"Invalid Product Type '{item.get('Product Type')}'.\n"
                    "Allowed values: consu (Goods), service, combo"
                )
            vals = {
                "name": item.get('Name'),
                "type": product_type,
                "default_code": item.get('Internal Reference'),
                "list_price": item.get('Sales Price') or 0.0,
                "standard_price": item.get('Cost') or 0.0,
            }
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

        msg = "Imported %d records.\nUpdated %d records." % (created, updated)
        self.env['import.message'].create({'message': msg})
        return {
            'effect': {
                'fadeout': 'slow',
                'message': msg,
                'type': 'rainbow_man',
            }
        }

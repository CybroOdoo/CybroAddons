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
import openpyxl
from odoo.exceptions import ValidationError
from odoo import fields, models


class ImportProductTemplate(models.TransientModel):
    """ Model for import product template. """
    _name = 'import.product.template'
    _description = 'Product Template Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xlsx', 'XLSX File')],
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

    def get_val(self, item, *keys, default=None):
        for key in keys:
            if item.get(key):
                return item.get(key)
        return default

    def action_import_product_template(self):
        """Creating product record using uploaded xl/csv files"""
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the "
                    "type and format of the file and try again!")
            items = csv_reader
        if self.file_type == 'xlsx':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False,
                                                 suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload))
                fp.seek(0)
                workbook = openpyxl.load_workbook(fp.name, data_only=True)
                sheet = workbook.active
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the "
                    "type and format of the file and try again!")
            rows = list(sheet.rows)
            headers = [cell.value for cell in rows[0]]
            data = []
            for row in rows[1:]:
                data += [{k: v.value for k, v in zip(headers, row)}]
            items = data
        updated = 0
        created = 0
        for item in items:
            product = False
            name = self.get_val(item, 'Name')
            product_type = self.get_val(item, 'Product Type', 'Type')
            internal_ref = self.get_val(item, 'Internal Reference', 'Code')
            sale_price = self.get_val(item, 'Sales Price', 'Price')
            cost = self.get_val(item, 'Cost')
            vals = {
                "name": name,
                "type": product_type,
                "default_code": internal_ref,
                "list_price": sale_price,
                "standard_price": cost
            }
            if self.method == "create_product":
                product = self.env['product.template'].search(
                    [('name', '=', name)])
            if self.method == "update_product":
                # if method is update and if product exists then update the product
                if self.import_product_by == "name":
                    product = self.env['product.template'].search(
                        [('name', '=', name)])
                elif self.import_product_by == "internal_reference":
                    product = self.env['product.template'].search(
                        [('default_code', '=', internal_ref)])
                if product:
                    self.env['product.template'].browse(product.id).write(vals)
                    updated += 1
            if not product:
                self.env['product.template'].create(vals)
                created += 1
        msg = (("Imported %d records.\nUpdated %d records."
                % (created, updated)))
        message = self.env['import.message'].create(
            {'message': msg})
        if message:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': msg,
                    'type': 'rainbow_man',
                }
            }
        return False

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import xlrd
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
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the "
                    "type and format of the file and try again!")
            items = csv_reader
        if self.file_type == 'xls':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False,
                                                 suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload))
                fp.seek(0)
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the "
                    "type and format of the file and try again!")
            headers = sheet.row_values(0)
            data = []
            for row_index in range(1, sheet.nrows):
                row = sheet.row_values(row_index)
                data += [{k: v for k, v in zip(headers, row)}]
            items = data
        updated = 0
        created = 0
        for item in items:
            product = False
            vals = {
                "name": item.get('Name'),
                "type": item.get('Product Type'),
                "default_code": item.get('Internal Reference'),
                "list_price": item.get('Sales Price'),
                "standard_price": item.get('Cost')
            }
            if self.method == "create_product":
                product = self.env['product.template'].search(
                    [('name', '=', item.get('Name'))])
            if self.method == "update_product":
                # if method is update and if product exists then update the product
                if self.import_product_by == "name":
                    product = self.env['product.template'].search(
                        [('name', '=', item.get('Name'))])
                elif self.import_product_by == "internal_reference":
                    product = self.env['product.template'].search(
                        [('default_code', '=', item.get('Internal Reference'))])
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

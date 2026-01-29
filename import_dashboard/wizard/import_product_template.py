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
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ImportProduct(models.TransientModel):
    """For handling importing of Product Template"""
    _name = 'import.product.template'
    _description = 'Importing Products'

    name = fields.Char(string="Name", help="Name", default="Import Products")
    file_type = fields.Selection([('csv', 'CSV File'),
                                  ('xls', 'Excel File')],
                                 string='Select File Type', default='csv',
                                 help="file type")
    method = fields.Selection([('create_product', 'Create Product'),
                               ('update_product', 'Update Product')],
                              string='Method', default='create_product',
                              help="method")
    import_product_by = fields.Selection(
        [('internal_reference', 'Internal Reference'),
         ('barcode', 'Barcode')], string="Product Update By",
        default='internal_reference', help="It helps to import product")
    file_upload = fields.Binary(string='File Upload',
                                help="It helps to upload file")

    def make_json_dict(self, column, row):
        """"Converting json data to dictionary"""
        return [{col: item[i] for i, col in enumerate(column)} for item in row]

    def action_product_template_import(self):
        """Creating product record using uploaded xl/csv files"""
        data = {}
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                data = csv.DictReader(data_file, delimiter=',')
            except:
                raise ValidationError(_(
                    "File not Valid.\n\nPlease check the type and format "
                    "of the file and try again!"))
        if self.file_type == 'xls':
            try:
                book_dict = {}
                fp = tempfile.NamedTemporaryFile(delete=False,
                                                 suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload))
                fp.seek(0)
                book = xlrd.open_workbook(fp.name)
                sheets = book.sheets()
                for sheet in sheets:
                    book_dict[sheet.name] = {}
                    columns = sheet.row_values(0)
                    rows = []
                    for row_index in range(1, sheet.nrows):
                        row = sheet.row_values(row_index)
                        rows.append(row)
                    sheet_data = self.make_json_dict(columns, rows)
                    book_dict[sheet.name] = sheet_data
                data = book_dict['Sheet1']
            except:
                raise ValidationError(_(
                    "File not Valid.\n\nPlease check the type and format "
                    "of the file and try again!"))
        for item in data:
            search_field = 'default_code' \
                if self.import_product_by == 'internal_reference' else 'barcode'
            product = self.env['product.template'].search([(search_field, '=',
                                                            str(item.get(
                                                                'Internal Reference' if self.import_product_by == 'internal_reference' else 'Barcode')))])
            product_values = {
                'name': item.get('Name'),
                'default_code': item.get('Internal Reference'),
                'list_price': item.get('Sales Price'),
                'standard_price': item.get('Cost'),
                'barcode': item.get('Barcode'),
            }
            if not product:
                if item.get('Product Type') == 'Consumable':
                    product_type = 'consu'
                elif item.get('Product Type') == 'Storable Product':
                    product_type = 'product'
                else:
                    product_type = 'service'
                product_values.update({
                    'detailed_type': product_type
                })
                self.env['product.template'].create(product_values)
            else:
                product.write(product_values)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Imported Successfully',
                'type': 'rainbow_man',
            }
        }

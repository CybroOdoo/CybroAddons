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


class ImportVendorPricelist(models.TransientModel):
    """For handling importing of vendor pricelist"""
    _name = 'import.vendor.pricelist'
    _description = 'Importing of vendor pricelist'

    name = fields.Char(string="Name", help="Name",
                       default="Import Vendor Pricelist")
    file_type = fields.Selection([('csv', 'CSV File'),
                                  ('xls', 'Excel File')],
                                 string='Select File Type', default='csv',
                                 help='File type')
    company_id = fields.Many2one('res.company', string='Company',
                                 help="Company", required=True,
                                 default=lambda self: self.env.company)
    file_upload = fields.Binary(string="Upload File", help="Upload your file")

    def make_json_dict(self, column, row):
        """Converting json data to dictionary"""
        return [{col: item[i] for i, col in enumerate(column)} for item in row]

    def action_vendor_pricelist_import(self):
        """Creating vendor pricelist record using uploaded xl/csv files"""
        datas = {}
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                datas = csv.DictReader(data_file, delimiter=',')
            except:
                raise ValidationError(_(
                    "File not Valid.\n\nPlease check the type and format "
                    "of the file, and try again!"))
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
                datas = book_dict['Sheet1']
            except:
                raise ValidationError(_(
                    "File not Valid.\n\nPlease check the type and format "
                    "of the file, and try again!"))
        for item in datas:
            vendor_name = None
            product_name = None
            currency = None
            if item.get('Vendor'):
                vendor_name = self.env['res.partner'].search(
                    [('name', '=', item.get('Vendor'))])
                if not vendor_name:
                    vendor_name = self.env['res.partner'].create({
                        'name': item.get('Vendor'),
                    })
            if item.get('Product Template'):
                product_name = self.env['product.template'].search(
                    [('name', '=', item.get('Product Template'))])
                if not product_name:
                    product_name = self.env['product.template'].create(
                        {'name': item.get('Product Template')})
            if item.get('Currency'):
                currency = self.env['res.currency'].search(
                    [('name', '=', item.get('Currency'))])
            self.env['product.supplierinfo'].create({
                "product_tmpl_id": product_name.id,
                "name": vendor_name.id,
                "min_qty": item.get('Quantity'),
                "price": item.get('Price'),
                "delay": item.get('Delivery Lead Time'),
                'company_id': self.company_id.id,
                'currency_id': currency.id
            })
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Imported Successfully',
                'type': 'rainbow_man',
            }
        }

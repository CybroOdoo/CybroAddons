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


class ImportVendorPricelist(models.TransientModel):
    """ Model for import vendor pricelist. """
    _name = 'import.vendor.pricelist'
    _description = 'Vendor Pricelist Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xls', 'Excel File')],
        string='Select File Type', default='csv', help='File type')
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                 help="Company", required=True,
                                 default=lambda self: self.env.company)
    file_upload = fields.Binary(string="Upload File",
                                help="Helps to upload your file")

    def action_import_vendor_pricelist(self):
        """Creating vendor pricelist record using uploaded xl/csv files"""
        items = False
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format "
                    "of the file and try again!")
            items = csv_reader
        if self.file_type == 'xls':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload))
                fp.seek(0)
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format of "
                    "the file and try again!")
            headers = sheet.row_values(0)  # list
            data = []
            for row_index in range(1, sheet.nrows):
                row = sheet.row_values(row_index)  # list
                data += [{k: v for k, v in zip(headers, row)}]
            items = data
        info_msg = ""
        imported = 0
        for item in items:
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
                    info_msg += f"\nCreated new partner with name: {item.get('Vendor')}"
            if item.get('Product Template'):
                product_name = self.env['product.template'].search(
                    [('name', '=', item.get('Product Template'))])
                if not product_name:
                    product_name = self.env['product.template'].create(
                        {'name': item.get('Product Template')})
                    info_msg += f"\nCreated new product with name: {item.get('Product Template')}"
            if item.get('Currency'):
                currency = self.env['res.currency'].search(
                    [('name', '=', item.get('Currency'))])
            self.env['product.supplierinfo'].create({
                "product_tmpl_id": product_name.id,
                "partner_id": vendor_name.id,
                "min_qty": item.get('Quantity'),
                "price": item.get('Price'),
                "delay": item.get('Delivery Lead Time'),
                'company_id': self.company_id.id,
                'currency_id': currency.id,
            })
            imported += 1
        if info_msg:
            info_msg = f"\nInformation : {info_msg}"
        msg = (("Imported %d records."
                % imported) + info_msg)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': msg,
                'type': 'rainbow_man',
            }
        }

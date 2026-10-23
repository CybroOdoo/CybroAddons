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


class ImportVendorPricelist(models.TransientModel):
    """ Model for import vendor pricelist. """
    _name = 'import.vendor.pricelist'
    _description = 'Vendor Pricelist Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xls', 'Excel File')],
        string='Select File Type', default='csv', help='Type of the file to import')
    company_id = fields.Many2one(comodel_name='res.company', help="Company", required=True,
                                 default=lambda self: self.env.company)
    file_upload = fields.Binary(string="Upload File",
                                help="File to import")

    def action_import_vendor_pricelist(self):
        """Creating vendor pricelist record using uploaded xl/csv files"""
        items = []
        if self.file_type == 'csv':
            try:
                items = read_csv_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the type and format "
                               "of the file and try again!"))
        if self.file_type == 'xls':
            try:
                items = read_xlsx_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the type and format of "
                               "the file and try again!"))
        info_msg = ""
        error_msg = ""
        imported = 0
        row_count = 0
        company_currency = self.company_id.currency_id
        for item in items:
            row_count += 1
            vendor_name = None
            product_name = None
            currency = company_currency

            row_error = ""
            if not item.get('Vendor'):
                row_error += "\n\tMissing 'Vendor' name."
            if not item.get('Product Template'):
                row_error += "\n\tMissing 'Product Template' name."

            if row_error:
                error_msg += self.env._("\nRow %(row_count)s not imported: %(row_error)s", row_count=row_count, row_error=row_error)
                continue

            if item.get('Vendor'):
                vendor_name = self.env['res.partner'].search(
                    [('name', '=', item.get('Vendor'))])
                if not vendor_name:
                    vendor_name = self.env['res.partner'].create({
                        'name': item.get('Vendor'),
                    })
                    info_msg += self.env._("\nCreated new partner with name: %(value0)s", value0=item.get('Vendor'))
            if item.get('Product Template'):
                product_name = self.env['product.template'].search(
                    [('name', '=', item.get('Product Template'))])
                if not product_name:
                    product_name = self.env['product.template'].create(
                        {'name': item.get('Product Template')})
                    info_msg += self.env._("\nCreated new product with name: %(value0)s", value0=item.get('Product Template'))

            # Check the values before creating the record
            if not product_name or not vendor_name:
                error_msg += self.env._("\nRow %(row_count)s not imported: Could not find or create Product Template or Vendor.", row_count=row_count)
                continue

            if item.get('Currency'):
                currency = self.env['res.currency'].search(
                    ['|',
                     ('name', '=', item.get('Currency')),
                     ('symbol', '=', item.get('Currency'))],
                    limit=1
                ) or company_currency
            qty = item.get('Quantity') or 0.0
            price = item.get('Price') or item.get('Unit Price') or 0.0
            delay = item.get('Delivery Lead Time') or item.get('Lead Time') or 0
            self.env['product.supplierinfo'].create({
                "product_tmpl_id": product_name.id,
                "partner_id": vendor_name.id,
                "min_qty": qty,
                "price": price,
                "delay": delay,
                'company_id': self.company_id.id,
                'currency_id': currency.id,
            })
            imported += 1

        if error_msg:
            error_msg = self.env._("\n\n⚠⚠⚠ ERROR !!! ⚠⚠⚠") + error_msg
            error_message = self.env['import.message'].create(
                {'message': error_msg})
            return {
                'name': self.env._('Error!'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'import.message',
                'res_id': error_message.id,
                'target': 'new'
            }

        if info_msg:
            info_msg = self.env._("\nInformation : %(info_msg)s", info_msg=info_msg)
        msg = ((self.env._("Imported %d records.", imported)) + info_msg)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': msg,
                'type': 'rainbow_man',
            }
        }

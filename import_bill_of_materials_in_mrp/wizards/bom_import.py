# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (<https://www.cybrosys.com>)
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
import binascii
import tempfile
import certifi
import urllib3
import xlrd
from odoo import models, fields, _
import csv
import base64
import openpyxl
from io import BytesIO
from odoo.exceptions import UserError
from odoo.tools import ustr


class BomImportWizard(models.TransientModel):
    """This is a transient model for creating a wizard for importing bom """
    _name = 'bom.import'
    _description = 'Import Bom wizard'

    file_type = fields.Selection([('csv', 'CSV File'),
                                  ('xls', 'Excel File')],
                                 String='File Type', Required=True,
                                 default='csv',
                                 help='File type of importing file')
    name = fields.Char(string='name')
    bom_type = fields.Selection(
        [('mtp', 'Manufacture This Product'), ('kit', 'Kit')],
        String='BOM Type', Required=True,
        default='mtp', helf='Type of Bill of Materials')
    product_variant_by = fields.Selection(
        [('default_code', 'Internal Reference'),
         ('barcode', 'Barcode')], String='Product Variant By', Required=True,
        default='default_code', help='Product variant type in file')
    product_by = fields.Selection([('name', 'Name'),
                                   ('default_code', 'Internal Reference'),
                                   ('barcode', 'Barcode')], String='Product By',
                                  Required=True, default='name',
                                  help='Product type in file')
    file = fields.Binary(String='Upload File', Required=True,
                         help='File to Import')

    def action_import_bom(self):
        """Function for importing bom through csv or Excel file"""
        if self.file:
            if self.file_type == 'csv':
                try:
                    file = base64.b64decode(self.file)
                    file_string = file.decode('utf-8')
                    file_string.split('\n')
                    urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                                        ca_certs=certifi.where())
                except:
                    raise UserError(_("Please choose the correct file!"))
                for rec in self:
                    file = str(base64.decodebytes(
                        rec.file).decode('utf-8'))
                    reader = csv.reader(file.splitlines())
                    next(reader)
                    last_bom_id = False
                    rec_count = 0
                    try:
                        for col in reader:
                            bom_data = {}
                            bom_line_dict = {}
                            if col[1]:
                                rec_count += 1
                                if rec.product_by == 'name':
                                    product_search = 'name'
                                elif rec.product_by == 'default_code':
                                    product_search = 'default_code'
                                else:
                                    product_search = 'barcode'
                                product = self.env['product.template'].search(
                                    [(product_search, '=', col[1])], limit=1)
                                bom_data.update({'product_tmpl_id': product.id,
                                                 'code': col[0]})
                                if col[2]:
                                    if rec.product_variant_by == 'default_code':
                                        variant_search = 'default_code'
                                    else:
                                        variant_search = 'barcode'
                                    variant = self.env[
                                        'product.product'].search(
                                        [(variant_search, '=', col[2])],
                                        limit=1)
                                    bom_data.update({'product_id': variant.id})
                                    if col[4]:
                                        uom = self.env['uom.uom'].search(
                                            [('name', '=', col[4])], limit=1)
                                        bom_data.update(
                                            {'product_uom_id': uom.id})
                                    else:
                                        bom_data.update(
                                            {'product_uom_id': variant.uom_id})
                                if col[3]:
                                    bom_data.update({'product_qty': col[3]})
                                else:
                                    bom_data.update({'product_qty': 1})

                                if rec.bom_type == 'mtp':
                                    bom_data.update({'type': 'normal'})
                                else:
                                    bom_data.update({'type': 'phantom'})
                                bom_bom = rec.env['mrp.bom'].create(bom_data)
                                last_bom_id = bom_bom.id
                            if col[5]:
                                if rec.product_variant_by == 'default_code':
                                    variant_search = 'default_code'
                                else:
                                    variant_search = 'barcode'
                                variant = self.env['product.product'].search(
                                    [(variant_search, '=', col[5])], limit=1)
                                bom_line_dict.update({'product_id': variant.id,
                                                      'bom_id': last_bom_id
                                                      })
                                if col[6]:
                                    bom_line_dict.update(
                                        {'product_qty': col[6]})
                                else:
                                    bom_line_dict.update({'product_qty': 1})
                                if col[7]:
                                    uom = self.env['uom.uom'].search(
                                        [('name', '=', col[7])], limit=1)
                                    bom_line_dict.update(
                                        {'product_uom_id': uom.id})
                                else:
                                    bom_line_dict.update(
                                        {'product_uom_id': product.uom_id})
                                self.env['mrp.bom.line'].create(bom_line_dict)
                        return rec.success_message(rec_count)
                    except Exception as e:
                        raise UserError(
                            _("Sorry, The CSV file you provided "
                              "does not match our required format" + ustr(
                                e)))

            if self.file_type == 'xls':
                try:
                    file_string = tempfile.NamedTemporaryFile(suffix=".xlsx")
                    file_string.write(binascii.a2b_base64(self.file))
                    book = xlrd.open_workbook(file_string.name)
                    book.sheet_by_index(0)
                    urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                                        ca_certs=certifi.where())
                except:
                    raise UserError(_("Please choose the correct file"))
                for rec in self:
                    try:
                        wb = openpyxl.load_workbook(
                            filename=BytesIO(base64.b64decode(rec.file)),
                            read_only=True)
                        ws = wb.active
                        rec_count = 0
                        for col in ws.iter_rows(min_row=2, values_only=True):
                            bom_data = {}
                            bom_line_dict = {}
                            if col[1]:
                                rec_count += 1
                                if rec.product_by == 'name':
                                    product_search = 'name'
                                elif rec.product_by == 'default_code':
                                    product_search = 'default_code'
                                else:
                                    product_search = 'barcode'
                                product = self.env['product.template'].search(
                                    [(product_search, '=', col[1])], limit=1)
                                bom_data.update({'product_tmpl_id': product.id,
                                                 'code': col[0]})
                                if col[2]:
                                    if rec.product_variant_by == 'default_code':
                                        variant_search = 'default_code'
                                    else:
                                        variant_search = 'barcode'
                                    variant = self.env[
                                        'product.product'].search(
                                        [(variant_search, '=', col[2])],
                                        limit=1)
                                    bom_data.update({'product_id': variant.id})
                                    if col[4]:
                                        uom = self.env['uom.uom'].search(
                                            [('name', '=', col[4])], limit=1)
                                        bom_data.update(
                                            {'product_uom_id': uom.id})
                                    else:
                                        bom_data.update(
                                            {'product_uom_id': variant.uom_id})
                                if col[3]:
                                    bom_data.update({'product_qty': col[3]})
                                else:
                                    bom_data.update({'product_qty': 1})

                                if rec.bom_type == 'mtp':
                                    bom_data.update({'type': 'normal'})
                                else:
                                    bom_data.update({'type': 'phantom'})
                                bom_bom = rec.env['mrp.bom'].create(bom_data)
                                last_bom_id = bom_bom.id
                            if col[5]:
                                if rec.product_variant_by == 'default_code':
                                    variant_search = 'default_code'
                                else:
                                    variant_search = 'barcode'
                                variant = self.env['product.product'].search(
                                    [(variant_search, '=', col[5])], limit=1)
                                bom_line_dict.update({'product_id': variant.id,
                                                      'bom_id': last_bom_id
                                                      })
                                if col[6]:
                                    bom_line_dict.update(
                                        {'product_qty': col[6]})
                                else:
                                    bom_line_dict.update({'product_qty': 1})
                                if col[7]:
                                    uom = self.env['uom.uom'].search(
                                        [('name', '=', col[7])], limit=1)
                                    bom_line_dict.update(
                                        {'product_uom_id': uom.id})
                                else:
                                    bom_line_dict.update(
                                        {'product_uom_id': product.uom_id})
                                self.env['mrp.bom.line'].create(bom_line_dict)
                        return rec.success_message(rec_count)
                    except Exception as e:
                        raise UserError(
                            _("Sorry, The Excel file you provided"
                              " does not match our required format" + ustr(
                                e)))

    def success_message(self, rec_count):
        """function for displaying success message"""
        message_id = self.env['success.message'].create(
            {'message': str(rec_count) + " Records imported successfully"})
        return {
            'name': 'Message',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'success.message',
            'res_id': message_id.id,
            'target': 'new'
        }

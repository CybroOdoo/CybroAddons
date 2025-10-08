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
from odoo import fields, models
from odoo.exceptions import ValidationError


class ImportBillOfMaterial(models.TransientModel):
    """ Model for importing Bill of Materials. """
    _name = 'import.bill.of.material'
    _description = 'Bill of Material Import'

    file_type = fields.Selection(selection=[('csv', 'CSV File'),
                                            ('xls', 'XLS File')], default='csv',
                                 string='Select File Type',
                                 help="Uploading file Type")
    file_upload = fields.Binary(string='Upload File',
                                help="Helps to upload file")
    import_product_by = fields.Selection(
        selection=[
            ('default_code', 'Internal Reference'), ('barcode', 'Barcode')],
        default='default_code', string="Import Products By",
        help="Helps to import product")
    bom_type = fields.Selection(
        selection=[('manufacture_this_product', 'Manufacture this Product'),
                   ('kit', 'Kit'), ('both', 'Both')], string="Bom Type",
        default='both', help="Helps to choose the bom type")
    bom_component = fields.Selection(
        selection=[('add', 'Add Components'),
                   ('do_not', 'Do not add Components')], default='add',
        string="Bom Component", help="Helps to choose the bom component")

    def action_import_bom(self):
        """Creating sale order record using uploaded xl/csv files"""
        datas = {}
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                datas = csv.DictReader(data_file, delimiter=',')
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format "
                    "of the file and try again!")
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
                    """File not Valid.\n\nPlease check the """
                    """type and format of the file and try again!""")
            headers = sheet.row_values(0)
            data = []
            for row_index in range(1, sheet.nrows):
                row = sheet.row_values(row_index)
                data += [{k: v for k, v in zip(headers, row)}]
            datas = data
        row = 0
        imported = 0
        updated = 0
        error_msg = ""
        warning_msg = ""
        for item in datas:
            row += 1
            vals = {}
            if item.get('Product'):
                if self.import_product_by == 'default_code' and item.get(
                        'Product/Internal Reference'):
                    product_tmpl = self.env['product.template'].search(
                        [('default_code',
                          '=', item.get(
                            'Product/Internal Reference'))])
                elif self.import_product_by == 'barcode' and item.get(
                        'Product/Barcode'):
                    product_tmpl = self.env['product.template'].search(
                        [('barcode', '=', item.get('Product/Barcode'))])
                else:
                    product_tmpl = self.env['product.template'].search(
                        [('name', '=', item.get('Product'))])
                vals['product_tmpl_id'] = product_tmpl.id
                if not product_tmpl:
                    product_template = self.env['product.template'].create({
                        'name': item.get('Product'),
                        'default_code': item.get('Product/Internal Reference'),
                        'barcode': item.get('Product/Barcode')
                    })
                    warning_msg += ("\n◼ A Product is created with "
                                    "\"Internal Reference\" as "
                                    "product name since \"Product\""
                                    " name is missing in file."
                                    "(row %d)" % row)
                    vals['product_tmpl_id'] = product_template.id
            else:
                error_msg += "\n\t⚠ Product name missing in file!"
            if item.get('Quantity'):
                vals['product_qty'] = item.get('Quantity')
            if item.get('Reference'):
                vals['code'] = item.get('Reference')
            if self.bom_type == 'manufacture_this_product':
                vals['type'] = 'normal'
            elif self.bom_type == 'kit':
                vals['type'] = 'phantom'
            else:
                if item.get('BoM Type'):
                    if item.get('BoM Type') == 'Manufacture this product':
                        vals['type'] = 'normal'
                    else:
                        vals['type'] = 'phantom'
            components = {}
            if self.bom_component == 'add':
                if item.get('Components'):
                    if item.get('Components/Internal Reference'):
                        product_tmpl = self.env['product.product'].search([(
                            'default_code',
                            '=',
                            item.get(
                                'Components/Internal Reference'))])
                    elif item.get('Components/Barcode'):
                        product_tmpl = self.env['product.product'].search(
                            [('barcode', '=', item.get('Components/Barcode'))])
                    else:
                        product_tmpl = self.env['product.product'].search(
                            [('name', '=', item.get('Components'))])
                    components['product_id'] = product_tmpl.id
                    if not product_tmpl:
                        product_template = (
                            self.env['product.product'].create({
                                'name': item.get('Components'),
                                'default_code': item.get(
                                    'Components/Internal Reference'),
                                'barcode': item.get('Components/Barcode')
                            }))
                        warning_msg += ("\n◼ A Component Product is created with "
                                        "\"Internal Reference\" as "
                                        "product name since \"Product\""
                                        " name is missing in file."
                                        "(row %d)" % row)
                        components['product_id'] = product_template.id
                    if item.get('BoM Lines/Quantity'):
                        components['product_qty'] = item.get(
                            'BoM Lines/Quantity')
                    vals['bom_line_ids'] = [(0, 0, components)]
                else:
                    raise ValidationError(
                        "File not contain any BoM Lines/Components."
                        "\n\nPlease check the file.")
            if item.get('Product'):
                bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', vals['product_tmpl_id'])])
                if bom_id and self.bom_component == 'add':
                    bom_id.write({
                        'bom_line_ids': [(0, 0, components)]
                    })
                    updated += 1
                else:
                    self.env['mrp.bom'].create(vals)
                    imported += 1
            if error_msg:
                error_msg = "\n\n🏮 ERROR 🏮" + error_msg
                error_message = self.env['import.message'].create(
                    {'message': error_msg})
                return {
                    'name': 'Error!',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'import.message',
                    'res_id': error_message.id,
                    'target': 'new'
                }
            msg = (("Imported %d records.\nUpdated %d records"
                    % (imported, updated)) +
                   warning_msg)
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

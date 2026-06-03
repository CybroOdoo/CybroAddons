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
from odoo import Command, fields, models
from odoo.exceptions import ValidationError


class ImportBillOfMaterial(models.TransientModel):
    """ Model for importing Bill of Materials. """
    _name = 'import.bill.of.material'
    _description = 'Bill of Material Import'

    file_type = fields.Selection(selection=[('csv', 'CSV File'),
                                            ('xlsx', 'XLSX File')], default='csv',
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
        default='both', help="Helps to choose the bom type", required=True)
    bom_component = fields.Selection(
        selection=[('add', 'Add Components'),
                   ('do_not', 'Do not add Components')], default='add', required=True,
        string="Bom Component", help="Helps to choose the bom component")

    def get_val(self, item, *keys, default=None):
        for key in keys:
            if item.get(key):
                return item.get(key)
        return default

    def set_bom_lines(self, item, warning_msg, row, vals):
        """Setting up the BOM lines if add component option is used"""
        components = {}
        component_name = self.get_val(item, 'Components', 'Component/Internal Reference', 'Component/Barcode',
                                      'BoM Lines', 'BoM Lines/Internal Reference', 'BoM Lines/Barcode')
        if not component_name:
            raise ValidationError(
                "File not contain any BoM Lines/Components.\n\nPlease check the file."
            )
        # --- FIND COMPONENT PRODUCT ---
        internal_ref = self.get_val(
            item,
            'Components/Internal Reference',
            'BoM Lines/Internal Reference',
        )
        barcode = self.get_val(
            item,
            'Components/Barcode',
            'BoM Lines/Barcode'
        )
        if internal_ref:
            product = self.env['product.product'].search(
                [('default_code', '=', internal_ref)], limit=1
            )
        elif barcode:
            product = self.env['product.product'].search(
                [('barcode', '=', barcode)], limit=1
            )
        else:
            product = self.env['product.product'].search(
                [('name', '=', component_name)], limit=1
            )
        # --- CREATE IF NOT FOUND ---
        if not product:
            product = self.env['product.product'].create({
                'name': component_name,
                'default_code': internal_ref or '',
                'barcode': barcode or '',
            })
            warning_msg += (
                    "\n◼ A Component Product is created (row %d)" % row
            )
        components['product_id'] = product.id
        # --- QUANTITY ---
        components['product_qty'] = self.get_val(
            item,
            'BoM Lines/Quantity',
            'Component/Quantity',
            default=1.0
        )
        vals['bom_line_ids'] = [Command.create(components)]
        return vals, warning_msg

    def action_import_bom(self):
        """Creating BOM records using uploaded xl/csv files"""
        datas = {}
        # --- FILE READ ---
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                datas = csv.DictReader(data_file, delimiter=',')
            except Exception:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format of the file and try again!"
                )
        elif self.file_type == 'xlsx':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload))
                fp.seek(0)
                workbook = openpyxl.load_workbook(fp.name, data_only=True)
                sheet = workbook.active
                rows = list(sheet.rows)
                headers = [cell.value for cell in rows[0]]
                datas = []
                for row in rows[1:]:
                    datas.append({k: v.value for k, v in zip(headers, row)})
            except Exception:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format of the file and try again!"
                )
        row = 0
        imported = 0
        updated = 0
        error_msg = ""
        warning_msg = ""
        if datas:
            # --- MAIN LOOP ---
            for item in datas:
                row += 1
                vals = {}
                product_name = self.get_val(item, 'Product')
                if not product_name:
                    error_msg += "\n\t⚠ Product name missing in file!"
                    continue
                # --- FIND PRODUCT TEMPLATE ---
                internal_ref = self.get_val(
                    item,
                    'Product/Internal Reference',
                    'Internal Reference'
                )
                barcode = self.get_val(
                    item,
                    'Product/Barcode',
                    'Barcode'
                )
                if self.import_product_by == 'default_code' and internal_ref:
                    product_template = self.env['product.template'].search(
                        [('default_code', '=', internal_ref)], limit=1
                    )
                elif self.import_product_by == 'barcode' and barcode:
                    product_template = self.env['product.template'].search(
                        [('barcode', '=', barcode)], limit=1
                    )
                else:
                    product_template = self.env['product.template'].search(
                        [('name', '=', product_name)], limit=1
                    )
                # --- CREATE PRODUCT IF NOT FOUND ---
                if not product_template:
                    product_template = self.env['product.template'].create({
                        'name': product_name,
                        'default_code': internal_ref or '',
                        'barcode': barcode or '',
                    })
                    warning_msg += (
                            "\n◼ A Product is created (row %d)" % row
                    )
                vals['product_tmpl_id'] = product_template.id
                # --- BASIC FIELDS ---
                vals['product_qty'] = self.get_val(item, 'Quantity', default=1.0)
                vals['code'] = self.get_val(item, 'Reference', 'Code')
                # --- BOM TYPE ---
                if self.bom_type == 'manufacture_this_product':
                    vals['type'] = 'normal'
                elif self.bom_type == 'kit':
                    vals['type'] = 'phantom'
                else:
                    bom_type_val = self.get_val(item, 'BoM Type', 'Type')
                    if bom_type_val == 'Manufacture this product':
                        vals['type'] = 'normal'
                    else:
                        vals['type'] = 'phantom'
                # --- CREATE / UPDATE BOM ---
                bom = self.env['mrp.bom'].search(
                    [('product_tmpl_id', '=', product_template.id)], limit=1
                )
                if not bom:
                    bom = self.env['mrp.bom'].create(vals)
                else:
                    bom.write(vals)
                # --- COMPONENTS ---
                if bom and self.bom_component == 'add':
                    vals, warning_msg = self.set_bom_lines(item, warning_msg, row, vals)
                    bom.write({'bom_line_ids': vals['bom_line_ids']})
                    updated += 1
                imported += 1
            # --- ERROR HANDLING ---
            if error_msg:
                error_msg = "\n\n🏮 ERROR 🏮" + error_msg
                error_message = self.env['import.message'].create({'message': error_msg})
                return {
                    'name': 'Error!',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'import.message',
                    'res_id': error_message.id,
                    'target': 'new'
                }
            msg = f"Imported {imported} records.\nUpdated {updated} records{warning_msg}"
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': msg,
                    'type': 'rainbow_man',
                }
            }
        return False

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

from odoo import fields, models
from odoo.exceptions import ValidationError


class ImportBillOfMaterial(models.TransientModel):
    """ Model for importing Bill of Materials. """
    _name = 'import.bill.of.material'
    _description = 'Bill of Materials Import'

    file_type = fields.Selection(selection=[('csv', 'CSV File'),
                                            ('xls', 'XLS File')], default='csv',
                                 string='Select File Type',
                                 help="Type of the file to import")
    file_upload = fields.Binary(string='Upload File',
                                help="File to import")
    import_product_by = fields.Selection(
        selection=[
            ('default_code', 'Internal Reference'), ('barcode', 'Barcode')],
        default='default_code', string="Match Products By",
        help="Product field used to match the products in the file")
    bom_type = fields.Selection(
        selection=[('manufacture_this_product', 'Manufacture this Product'),
                   ('kit', 'Kit'), ('both', 'Both')], default='both', help="Type of the bills of materials to import")
    bom_component = fields.Selection(
        selection=[('add', 'Add Components'),
                   ('do_not', 'Do not add Components')], default='add',
        help="Add the components from the file to the bills of materials")

    def action_import_bom(self):
        """Creating sale order record using uploaded xl/csv files"""
        datas = {}
        if self.file_type == 'csv':
            try:
                datas = read_csv_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the type and format "
                               "of the file and try again!"))

        if self.file_type == 'xls':
            try:
                datas = read_xlsx_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the "
                               "type and format of the file and try again!")
                )

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
                    warning_msg += (self.env._("\n◼ Product \"%(product)s\" was "
                                    "not found, so a new product was "
                                    "created. (row %(row)d)",
                                    product=item.get('Product'), row=row))
                    vals['product_tmpl_id'] = product_template.id
            else:
                error_msg += self.env._("\n\t⚠ Product name missing in file!")

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
                comp_name = item.get('Components') or item.get('Component')
                if comp_name:
                    if item.get('Components/Internal Reference'):
                        product_tmpl = self.env['product.product'].search([(
                            'default_code',
                            '=',
                            item.get(
                                'Components/Internal Reference'))], limit=1)
                    elif item.get('Components/Barcode'):
                        product_tmpl = self.env['product.product'].search(
                            [('barcode', '=', item.get('Components/Barcode'))], limit=1)
                    else:
                        product_tmpl = self.env['product.product'].search(
                            [('name', '=', comp_name)], limit=1)
                    components['product_id'] = product_tmpl.id if product_tmpl else False
                    if not product_tmpl:
                        product_template = (
                            self.env['product.product'].create({
                                'name': comp_name,
                                'default_code': item.get(
                                    'Components/Internal Reference'),
                                'barcode': item.get('Components/Barcode')
                            }))
                        warning_msg += (
                                self.env._("\n◼ Component \"%(component)s\" was "
                                "not found, so a new product was "
                                "created. (row %(row)d)",
                                component=comp_name, row=row))
                        components['product_id'] = product_template.id
                    qty = item.get('BoM Lines/Quantity') or item.get('Quantity') or 1
                    components['product_qty'] = float(qty)
                    vals['bom_line_ids'] = [(0, 0, components)]
                else:
                    raise ValidationError(
                        self.env._("The file does not contain any BoM lines or components."
                                   "\n\nPlease check the file."))

            if item.get('Product'):
                bom_id = self.env['mrp.bom'].search(
                    [('product_tmpl_id', '=', vals['product_tmpl_id'])])
                if bom_id and self.bom_component == 'add':
                    bom_id.write({
                        'bom_line_ids': [(0, 0, components)]
                    })
                    updated += 1
                else:
                    self.env['mrp.bom'].create(vals)
                    imported += 1

        if error_msg:
            error_msg = self.env._("\n\nERROR") + error_msg
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

        msg = ((self.env._("Imported %(imported)d records.\nUpdated %(updated)d records", imported=imported, updated=updated)) +
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

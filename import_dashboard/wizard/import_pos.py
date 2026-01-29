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
import datetime
import io
import tempfile
import xlrd
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ImportPOS(models.TransientModel):
    """For handling importing of pos orders"""
    _name = 'import.pos'
    _description = 'For handling of importing of POS'

    name = fields.Char(string="Name", help="Name", default="Import PoS Order")
    file_type = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')],
                                 string='Select File Type', default='csv',
                                 help='It helps to choose the file type')
    file_upload = fields.Binary(string='File Upload',
                                help="It helps to upload file")

    def action_pos_order_import(self):
        """Creating sale order record using uploaded xl/csv files"""
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
                    "of the file and try again!"))
        if self.file_type == 'xls':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False,
                                                 suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload))
                fp.seek(0)
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except:
                raise ValidationError(_(
                    """File not Valid.\n\nPlease check the """
                    """type and format of the file and try again!"""))
            headers = sheet.row_values(0)
            data = []
            for row_index in range(1, sheet.nrows):
                row = sheet.row_values(row_index)
                data += [{k: v for k, v in zip(headers, row)}]
            datas = data
        previous_item = None
        error_msg = ''
        row = 0
        imported = 0
        for item in datas:
            row += 1
            row_not_import_msg = "\n◼  Row {rn} not imported.".format(
                rn=row)
            vals = {}
            order_ref = None
            if item.get('Order Ref'):
                order_ref = self.env['pos.order'].search(
                    [('name', '=', item.get('Order Ref'))])
            if order_ref:
                raise ValidationError(_(
                    "\n\t⚠ Order with reference \"%s\" already exists."
                        " This record will not be imported." % item.get(
                    'Order Ref')))
            else:
                vals['name'] = item.get('Order Ref')
                vals['amount_tax'] = item.get('Tax Amount') if item.get(
                    'Tax Amount') else 0.0
                vals['amount_total'] = item.get('Total') if item.get(
                    'Total') else 0.0
                vals['amount_paid'] = item.get('Paid Amount') if item.get(
                    'Paid Amount') else 0.0
                vals['amount_return'] = item.get(
                    'Amount Returned') if item.get(
                    'Amount Returned') else 0.0
                vals['company_id'] = self.env['res.company'].search([('name', '=', item.get('Company'))]).id
                vals['pricelist_id'] = self.env['product.pricelist'].search([('name', '=', item.get('Pricelist'))]).id
                vals['session_id'] = self.env['pos.session'].search(
                    [('name', '=', item.get('Session'))]).id
                if item.get('Receipt Number'):
                    vals['pos_reference'] = item.get('Receipt Number')
                if item.get('Order Date'):
                    if self.file_type == 'csv':
                        vals['date_order'] = item.get('Order Date')
                    else:
                        vals[
                            'date_order'] = datetime.datetime.fromtimestamp(
                            item.get('Order Date')).strftime(
                            '%Y-%m-%d %H:%M:%S')
                if item.get('Responsible'):
                    vals['user_id'] = self.env['res.users'].search(
                        [('name', '=', item.get('Responsible'))]).id
                if item.get('Customer'):
                    partner_id = self.env['res.partner'].search(
                        [('name', '=', item.get('Customer'))])
                    if not partner_id:
                        partner_id = self.env['res.partner'].create({
                            'name': item.get('Customer')
                        })
                    vals['partner_id'] = partner_id.id
                lines = {}
                if item.get('Product'):
                    product = self.env['product.product'].search([('name', '=',
                                                                   item[
                                                                       'Product'])])
                    if not product:
                        product = self.env['product.product'].create({
                            'name': item.get('Product')
                        })
                    if len(product) > 1:
                        if item.get('Variant Values'):
                            pro_tmpl_id = product.mapped('product_tmpl_id')
                            if len(pro_tmpl_id) > 1:
                                error_msg += row_not_import_msg + (
                                        "\n\t⚠ Multiple Product records are "
                                        "linked with the product variant \"%s\""
                                        "." % item['Product'])
                                continue
                            variant_values = item['Variant Values'].split(
                                ',')
                            variant_value_ids = []
                            for var in variant_values:
                                k_v = var.partition(":")
                                attr = k_v[0].strip()
                                attr_val = k_v[2].strip()
                                var_attr_ids = self.env[
                                    'product.attribute'].search(
                                    [('name', '=', attr)]).ids
                                var_attr_val_ids = self.env[
                                    'product.attribute.value'].search(
                                    [('name', '=', attr_val),
                                     ('attribute_id', 'in',
                                      var_attr_ids)]).ids
                                pro_temp_attr_val_id = self.env[
                                    'product.template.attribute.value'].search(
                                    [('product_attribute_value_id', 'in',
                                      var_attr_val_ids),
                                     ('product_tmpl_id', '=',
                                      pro_tmpl_id.id)]).id
                                variant_value_ids += [pro_temp_attr_val_id]
                            if variant_value_ids:
                                product = product.filtered(
                                    lambda p:
                                    p.product_template_variant_value_ids.ids
                                    == variant_value_ids)
                            else:
                                error_msg += row_not_import_msg + (
                                        "\n\t⚠ Product variant with variant "
                                        "values \"%s\" not found."
                                        % (item['Variant Values']))
                                continue
                            if len(product) != 1:
                                error_msg += row_not_import_msg + (
                                        "\n\t⚠ Multiple variants with same "
                                        "Variant Values \"%s\" found. Please "
                                        "check if the product Variant Values"
                                        " are unique."
                                        % (item['Variant Values']))
                                continue
                        else:
                            error_msg += row_not_import_msg + (
                                    "\n\t⚠ Multiple Products with same "
                                    "Name \"%s\" found. Please "
                                    "provide unique product \"Variant "
                                    "Values\" to filter the records."
                                    % (item['Product']))
                            continue
                    lines['product_id'] = product.id
                    lines['full_product_name'] = product.name
                    lines['qty'] = item.get('Quantity')
                    lines['price_unit'] = item.get('Unit Price')
                    lines['discount'] = item.get('Discount %')
                    lines['price_subtotal'] = item.get('Sub Total')
                    lines['price_subtotal_incl'] = 0.0
                vals['lines'] = [(0, 0, lines)]
                if item.get('Session'):
                    pos_order = self.env['pos.order'].create(vals)
                    previous_item = pos_order
                if not item.get('Session'):
                    if item.get('Product'):
                        previous_item.write({
                            'lines': [(0, 0, lines)]
                        })
                imported += 1
            if error_msg:
                error_msg = "\n\n🏮 WARNING 🏮" + error_msg
            msg = (("Imported %d records."
                    % imported) + error_msg)
            message = self.env['import.message'].create(
                {'message': msg})
        if message:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Imported Successfully',
                    'type': 'rainbow_man',
                }
            }

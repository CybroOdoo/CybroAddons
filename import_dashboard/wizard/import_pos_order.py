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
from odoo.exceptions import ValidationError
from odoo import fields, models, _


class ImportPosOrder(models.TransientModel):
    """ Model for import POS Orders """
    _name = 'import.pos.order'
    _description = 'Pos Orders Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xls', 'XLS File')],
        string='Select File Type', default='xls',
        help='It helps to choose the file type')
    file_upload = fields.Binary(string='File Upload',
                                help="It helps to upload file")
    import_product_by = fields.Selection(
        selection=[('name', 'Name'), ('default_code', 'Internal Reference'),
                   ('barcode', 'Barcode')], string="Import order by",
        help="Import product", default="name")

    def action_import_pos_order(self):
        """Creating POS Order record using uploaded xl/csv files"""
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
        pos_order = None
        for item in datas:
            vals = {}
            order_ref = None
            if item.get('Order Ref'):
                order_ref = self.env['pos.order'].search(
                    [('name', '=', item.get('Order Ref'))])
            if order_ref:
                error_msg = ('POS order with order reference :` %s ` is already exists.' % item.get('Order Ref'))
                error_message = self.env['import.message'].create({'message': error_msg})
                return {
                    'name': 'Error!',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'import.message',
                    'res_id': error_message.id,
                    'target': 'new'
                }
            else:
                vals['pricelist_id'] = (self.env.user.partner_id.
                                        property_product_pricelist.id)
                vals['company_id'] = self.env.user.company_id.id
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
                if item.get('Responsible'):
                    vals['user_id'] = self.env['res.users'].search(
                        [('name', '=', item.get('Responsible'))]).id
                else:
                    continue
                vals['session_id'] = self.env['pos.session'].search(
                    [('name', '=', item.get('Session'))]).id
                if not vals['session_id']:
                    vals['session_id'] = self.env['pos.session'].create({
                                            'name': item.get('Session'),
                                            'user_id': vals['user_id'],
                                            'config_id': 1
                                        }).id
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
                    lines['product_id'] = self.env[
                        'product.product'].search(
                        [('name', '=', item.get('Product'))]).id
                    lines['full_product_name'] = item.get('Product')
                    lines['qty'] = item.get('Quantity')
                    lines['price_unit'] = item.get('Unit Price')
                    lines['discount'] = item.get('Discount %')
                    lines['price_subtotal'] = item.get('Sub Total')
                    lines['price_subtotal_incl'] = 0.0
                vals['lines'] = [(0, 0, lines)]
                if item.get('Session'):
                    pos_order = self.env['pos.order'].create(vals)
                if not item.get('Session'):
                    if item.get('Product'):
                        lines['order_id'] = pos_order.id
                        self.env['pos.order.line'].create(lines)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Imported Successfully',
                'type': 'rainbow_man',
            }
        }

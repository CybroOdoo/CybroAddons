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
import datetime
import io
import tempfile
import openpyxl
from odoo.exceptions import ValidationError
from odoo import fields, models, Command


class ImportPosOrder(models.TransientModel):
    """ Model for import POS Orders """
    _name = 'import.pos.order'
    _description = 'Pos Orders Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xlsx', 'XLSX File')],
        string='Select File Type', default='xlsx',
        help='It helps to choose the file type')
    file_upload = fields.Binary(string='File Upload',
                                help="It helps to upload file")
    import_product_by = fields.Selection(
        selection=[('name', 'Name'), ('default_code', 'Internal Reference'),
                   ('barcode', 'Barcode')], string="Import order by",
        help="Import product", default="name")

    def get_val(self, item, *keys, default=None):
        for key in keys:
            if item.get(key):
                return item.get(key)
        return default

    def set_pos_lines(self, item):
        """Set POS Lines"""
        lines = {}
        product_name = self.get_val(item, 'Product', 'Order Lines/Products', default='')
        if product_name:
            domain = [('name', '=', product_name)]
            product = self.env['product.product'].search(domain, limit=1)
            lines['product_id'] = product.id
            lines['full_product_name'] = product_name
            lines['qty'] = self.get_val(
                item,
                'Quantity',
                'Order Lines/Quantity',
                default=0.0
            )
            lines['price_unit'] = self.get_val(
                item,
                'Unit Price',
                'Order Lines/Unit Price',
                default=0.0
            )
            discount = self.get_val(
                item,
                'Disc.%',
                'Order Lines/Disc.%',
                'Disc',
                'Order Lines/Disc',
                'Discount',
                'Order Lines/Discount',
                default=0.0
            )
            if discount:
                lines['discount'] = discount
            lines['price_subtotal'] = self.get_val(
                item,
                'Sub Total',
                'Order Lines/Sub total',
                default=0.0
            )
            lines['price_subtotal_incl'] = 0.0
        return lines

    def action_import_pos_order(self):
        """Creating POS Order record using uploaded xl/csv files"""
        datas = {}
        # --- FILE READ ---
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
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
        pos_order = None
        # --- MAIN LOOP ---
        if datas:
            for item in datas:
                vals = {}
                order_ref = self.get_val(item, 'Order Ref', default='')
                if order_ref:
                    existing = self.env['pos.order'].search([('name', '=', order_ref)])
                    if existing:
                        error_msg = f'POS order with order reference : `{order_ref}` already exists.'
                        error_message = self.env['import.message'].create({'message': error_msg})
                        return {
                            'name': 'Error!',
                            'type': 'ir.actions.act_window',
                            'view_mode': 'form',
                            'res_model': 'import.message',
                            'res_id': error_message.id,
                            'target': 'new'
                        }
                # --- BASIC FIELDS ---
                vals.update({
                    'pricelist_id': self.env.user.partner_id.property_product_pricelist.id,
                    'company_id': self.env.user.company_id.id,
                    'name': order_ref,
                    'amount_tax': self.get_val(item, 'Tax Amount', default=0.0),
                    'amount_total': self.get_val(item, 'Total', default=0.0),
                    'amount_paid': self.get_val(item, 'Paid Amount', default=0.0),
                    'amount_return': self.get_val(item, 'Amount Returned', default=0.0),
                })
                # --- USER ---
                user_name = self.get_val(item, 'Responsible')
                if not user_name:
                    continue
                vals['user_id'] = self.env['res.users'].search(
                    [('name', '=', user_name)], limit=1
                ).id
                # --- SESSION ---
                session_name = self.get_val(item, 'Session')
                session = self.env['pos.session'].search(
                    [('name', '=', session_name)], limit=1
                )
                if not session:
                    session = self.env['pos.session'].create({
                        'name': session_name,
                        'user_id': vals['user_id'],
                        'config_id': 1
                    })
                vals['session_id'] = session.id
                # --- OPTIONAL FIELDS ---
                vals['pos_reference'] = self.get_val(item, 'Receipt Number', 'Reference', 'POS Reference',
                                                     'Pos Reference', 'POS Ref', 'Pos Ref', default='')
                order_date = self.get_val(item, 'Order Date')
                if order_date:
                    if self.file_type == 'csv':
                        vals['date_order'] = order_date
                    else:
                        if isinstance(order_date, (datetime.datetime, datetime.date)):
                            vals['date_order'] = order_date.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            try:
                                vals['date_order'] = datetime.datetime.fromtimestamp(float(order_date)).strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                vals['date_order'] = order_date
                # --- CUSTOMER ---
                customer_name = self.get_val(item, 'Customer')
                if customer_name:
                    partner = self.env['res.partner'].search(
                        [('name', '=', customer_name)], limit=1
                    )
                    if not partner:
                        partner = self.env['res.partner'].create({'name': customer_name})
                    vals['partner_id'] = partner.id
                # --- ORDER LINES ---
                lines = self.set_pos_lines(item)
                if lines:
                    vals['lines'] = [Command.create(lines)]
                # --- CREATE ORDER ---
                if session_name:
                    pos_order = self.env['pos.order'].create(vals)
                # --- ADDITIONAL LINES (NO SESSION CASE) ---
                if not session_name:
                    product_name = self.get_val(item, 'Product', 'Order Lines/Products')
                    if product_name and pos_order:
                        lines['order_id'] = pos_order.id
                        self.env['pos.order.line'].create(lines)
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Imported Successfully',
                    'type': 'rainbow_man',
                }
            }
        return False

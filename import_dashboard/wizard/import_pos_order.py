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
import datetime
from .import_utils import get_file_content, read_csv_data, read_xlsx_data
from odoo.exceptions import ValidationError
from odoo import fields, models


class ImportPosOrder(models.TransientModel):
    """ Model for import POS Orders """
    _name = 'import.pos.order'
    _description = 'Pos Orders Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xls', 'XLS File')],
        string='Select File Type', default='xls',
        help='Type of the file to import')
    file_upload = fields.Binary(help="File to import")
    import_product_by = fields.Selection(
        selection=[('name', 'Name'), ('default_code', 'Internal Reference'),
                   ('barcode', 'Barcode')], string="Match Products By",
        help="Product field used to match the products in the file", default="name")

    def action_import_pos_order(self):
        """Creating POS Order record using uploaded xl/csv files"""
        datas = []
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
                               "type and format of the file and try again!"))
        row = 0
        for item in datas:
            row += 1
            vals = {}
            order_ref = None
            if item.get('Order Ref'):
                order_ref = self.env['pos.order'].search(
                    [('name', '=', item.get('Order Ref'))])
            if order_ref:
                error_msg = self.env._(
                    "A POS order with the order reference '%s' already exists.",
                    item.get('Order Ref'))
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
            else:
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
                responsible = self.env['res.users']
                if item.get('Responsible'):
                    responsible = self.env['res.users'].search(
                        [('name', '=', item.get('Responsible'))], limit=1)
                vals['user_id'] = (responsible or self.env.user).id
                if item.get('Session'):
                    # Search for an existing session by name (any non-closed state)
                    session = self.env['pos.session'].search(
                        [('name', '=', item.get('Session')),
                         ('state', '!=', 'closed')], limit=1)
                    if not session:
                        # Fallback: find any open session (state='opened')
                        session = self.env['pos.session'].search(
                            [('state', '=', 'opened')], limit=1)
                    if not session:
                        raise ValidationError(
                            self.env._("No open POS session found. "
                                       "Please open a POS session before importing orders."))
                    vals['session_id'] = session.id
                else:
                    raise ValidationError(
                        self.env._("Row %d: 'Session' column is required for POS order import.", row))
                if item.get('Receipt Number'):
                    vals['pos_reference'] = item.get('Receipt Number')
                if item.get('Order Date'):
                    if self.file_type == 'csv':
                        vals['date_order'] = item.get('Order Date')
                    else:
                        order_date = item.get('Order Date')
                        if isinstance(order_date, datetime.datetime):
                            vals['date_order'] = order_date.strftime(
                                '%Y-%m-%d %H:%M:%S')
                        elif isinstance(order_date, datetime.date):
                            vals['date_order'] = datetime.datetime.combine(
                                order_date, datetime.time()).strftime(
                                '%Y-%m-%d %H:%M:%S')
                        else:
                            vals['date_order'] = order_date
                if item.get('Customer'):
                    partner_id = self.env['res.partner'].search(
                        [('name', '=', item.get('Customer'))])
                    if not partner_id:
                        partner_id = self.env['res.partner'].create({
                            'name': item.get('Customer')
                        })
                    vals['partner_id'] = partner_id.id
                lines = {}
                product_field, column = {
                    'name': ('name', 'Product'),
                    'default_code': ('default_code', 'Product Code'),
                    'barcode': ('barcode', 'Barcode'),
                }[self.import_product_by]
                if item.get(column):
                    product = self.env['product.product'].search(
                        [(product_field, '=', item.get(column))], limit=1)
                    if not product:
                        raise ValidationError(self.env._(
                            "Row %(row)d: no product found with %(column)s '%(value)s'.",
                            row=row, column=column, value=item.get(column)))
                    lines['name'] = product.display_name
                    lines['product_id'] = product.id
                    lines['full_product_name'] = item.get('Product') or product.display_name
                    lines['qty'] = item.get('Quantity')
                    lines['price_unit'] = item.get('Unit Price')
                    lines['discount'] = item.get('Discount %')
                    lines['price_subtotal'] = item.get('Sub Total')
                    lines['price_subtotal_incl'] = float(item.get('Sub Total') or item.get('Total') or 0.0)
                if lines:
                    vals['lines'] = [(0, 0, lines)]
                self.env['pos.order'].create(vals)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': self.env._('Imported Successfully'),
                'type': 'rainbow_man',
            }
        }

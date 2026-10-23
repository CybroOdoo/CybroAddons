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
from datetime import datetime
from .import_utils import get_file_content, read_csv_data, read_xlsx_data
from odoo.exceptions import ValidationError
from odoo import fields, models


class ImportPayment(models.TransientModel):
    """ Model for import payment """
    _name = 'import.payment'
    _description = 'Payment Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xlsx', 'XLS File')],
        string='Select File Type', default='xlsx',
        help='Type of the file to import')
    file_upload = fields.Binary(help='File to import')

    def action_import_payment(self):
        """ Method to import payments from .csv or .xlsx files. """
        items = []
        if self.file_type == 'csv':
            try:
                items = read_csv_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the type and format "
                               "of the file, and try again!"))
        if self.file_type == 'xlsx':
            try:
                items = read_xlsx_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the "
                               "type and format of the file and try again!"))
        row = 0
        imported = 0
        updated = 0
        error_msg = ""
        info_msg = ""
        if items:
            for item in items:
                row += 1
                vals = {}
                row_not_import_msg = self.env._("\nRow %(rn)s not imported.", rn=row)
                if item.get('Amount'):
                    vals['amount'] = item['Amount']
                if item.get('Date'):
                    date_val = item.get('Date')
                    if isinstance(date_val, datetime):
                        date_val = date_val.date()
                    vals['date'] = date_val
                if item.get('Journal'):
                    journal = self.env['account.journal'].search(
                        [('name', '=', item.get('Journal'))], limit=1)
                    if journal:
                        vals['journal_id'] = journal.id
                if item.get('Customer/Vendor'):
                    partner = self.env['res.partner'].search(
                        [('name', '=', item.get('Customer/Vendor'))], limit=1)
                    if not partner:
                        partner = self.env['res.partner'].create({
                            'name': item.get('Customer/Vendor')
                        })
                        info_msg += self.env._("\nCreated new partner with name: %(value0)s", value0=item.get('Customer/Vendor'))
                    vals['partner_id'] = partner.id
                if item.get('Reference'):
                    vals['memo'] = item.get('Reference')
                if item.get('Payment Type') == 'Send':
                    vals['payment_type'] = 'outbound'
                elif item.get('Payment Type') == 'Receive':
                    vals['payment_type'] = 'inbound'
                else:
                    error_msg += row_not_import_msg + (
                        self.env._("\n\tInvalid Payment Type value in file! Allowed values are \"Send\" and \"Receive\"."))
                    continue
                if item.get('Number'):
                    payment_ref = self.env['account.payment'].search(
                        [('name', '=', item.get('Number'))])
                    if payment_ref:
                        payment_ref.write(vals)
                        updated += 1
                    else:
                        vals['name'] = item.get('Number')
                        self.env['account.payment'].create(vals)
                        imported += 1
            if error_msg:
                error_msg = self.env._("\n\n⚠⚠⚠ERROR!!!⚠⚠⚠") + error_msg
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
            msg = ((self.env._("Imported %(imported)d records. Updated %(updated)d records", imported=imported, updated=updated)) + info_msg)
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

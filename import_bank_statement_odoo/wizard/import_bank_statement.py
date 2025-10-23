# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil Ashok (odoo@cybrosys.com)
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
###############################################################################
import base64
import codecs
import openpyxl
import os
from datetime import datetime
from io import BytesIO
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from ofxparse import OfxParser
from qifparse.parser import QifParser


class ImportBankStatement(models.TransientModel):
    """ A class to import files as bank statement """
    _name = "import.bank.statement"
    _description = "Import button"
    _rec_name = "file_name"

    attachment = fields.Binary(string="File", required=True,
                               help="Choose the file to import")
    file_name = fields.Char(string="File Name", help="Name of the file")
    journal_id = fields.Many2one('account.journal', string="Journal ID",
                                 help="Journal in which the file importing")

    def action_statement_import(self):
        """Function to import csv, xlsx, ofx and qif file format"""
        split_tup = os.path.splitext(self.file_name)
        if split_tup[1] in ['.csv', '.xlsx', '.ofx', '.qif']:
            # ----------------------- CSV Import -----------------------
            if split_tup[1] == '.csv':
                try:
                    file = base64.b64decode(self.attachment)
                    file_string = file.decode('utf-8')
                    file_string = file_string.split('\n')
                except:
                    raise ValidationError(_("Choose correct file"))
                firstline = True
                for file_item in file_string:
                    if firstline:
                        firstline = False
                        continue
                    if file_item.split(',') != ['']:
                        cols = file_item.split(',')
                        # Expected columns:
                        # Reference, Amount, Date, Partner Name, Start Bal, End Bal
                        if len(cols) < 6:
                            continue
                        ref, amount, date_str, partner_name, start_bal, end_bal = cols[
                                                                                  :6]
                        if ref and amount and partner_name:
                            date_obj = str(
                                fields.date.today()) if not date_str else date_str
                            transaction_date = datetime.strptime(date_obj,
                                                                 "%Y-%m-%d")
                            partner = self.env['res.partner'].search(
                                [('name', '=', partner_name)])
                            start_balance = float(
                                start_bal) if start_bal else 0.0
                            end_balance = float(end_bal) if end_bal else 0.0
                            if partner:
                                statement = self.env[
                                    'account.bank.statement'].create({
                                    'name': ref,
                                    'balance_start': start_balance,
                                    'balance_end_real': end_balance,
                                    'line_ids': [
                                        (0, 0, {
                                            'date': transaction_date,
                                            'payment_ref': 'csv file',
                                            'partner_id': partner.id,
                                            'journal_id': self.journal_id.id,
                                            'amount': amount,
                                        }),
                                    ],
                                })
                            else:
                                raise ValidationError(_("Partner not exist"))
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Statements',
                    'view_mode': 'tree',
                    'res_model': 'account.bank.statement',
                    'res_id': statement.id,
                }

            # ----------------------- XLSX Import -----------------------
            elif split_tup[1] == '.xlsx':
                try:
                    order = openpyxl.load_workbook(
                        filename=BytesIO(base64.b64decode(self.attachment)))
                    xl_order = order.active
                except:
                    raise ValidationError(_("Choose correct file"))

                for record in xl_order.iter_rows(min_row=2, values_only=True):
                    # Expected columns:
                    # Reference, Amount, Date, Partner Name, Start Bal, End Bal
                    line = list(record)
                    ref, amount, date_val, partner_name, start_bal, end_bal = \
                        line + [None] * (6 - len(line))  # ensure 6 items

                    if ref and amount and partner_name:
                        partner = self.env['res.partner'].search(
                            [('name', '=', partner_name)])
                        # Handle date formats
                        if not date_val:
                            date_obj = fields.Date.today()
                        else:
                            if isinstance(date_val, str):
                                try:
                                    date_obj = datetime.strptime(date_val,
                                                                 "%Y-%m-%d").date()
                                except ValueError:
                                    date_obj = datetime.strptime(date_val,
                                                                 "%d/%m/%Y").date()
                            else:
                                date_obj = date_val if isinstance(date_val,
                                                                  date) else date_val.date()

                        start_balance = float(start_bal) if start_bal else 0.0
                        end_balance = float(end_bal) if end_bal else 0.0

                        if partner:
                            statement = self.env[
                                'account.bank.statement'].create({
                                'name': ref,
                                'balance_start': start_balance,
                                'balance_end_real': end_balance,
                                'line_ids': [
                                    (0, 0, {
                                        'date': date_obj,
                                        'payment_ref': 'xlsx file',
                                        'partner_id': partner.id,
                                        'journal_id': self.journal_id.id,
                                        'amount': amount,
                                    }),
                                ],
                            })
                        else:
                            raise ValidationError(_("Partner not exist"))
                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Statements',
                    'view_mode': 'tree',
                    'res_model': 'account.bank.statement',
                    'res_id': statement.id,
                }

            # ----------------------- OFX Import -----------------------
            elif split_tup[1] == '.ofx':
                file_attachment = self.env["ir.attachment"].search(
                    ['|', ('res_field', '!=', False),
                     ('res_field', '=', False),
                     ('res_id', '=', self.id),
                     ('res_model', '=', 'import.bank.statement')],
                    limit=1)
                file_path = file_attachment._full_path(
                    file_attachment.store_fname)
                try:
                    with codecs.open(file_path) as fileobj:
                        ofx_file = OfxParser.parse(fileobj)
                except:
                    raise ValidationError(_("Wrong file format"))
                if not ofx_file.account or not ofx_file.account.statement:
                    raise ValidationError(
                        _("OFX file missing account or statement info"))

                statement_list = []
                start_balance = ofx_file.account.statement.balance or 0.0
                end_balance = ofx_file.account.statement.balance_end or 0.0

                for transaction in ofx_file.account.statement.transactions:
                    if transaction.type in ["debit",
                                            "credit"] and transaction.amount != 0:
                        payee = transaction.payee
                        amount = transaction.amount
                        date = transaction.date or fields.Date.today()
                        partner = self.env['res.partner'].search(
                            [('name', '=', payee)])
                        if partner:
                            statement_list.append([partner.id, amount, date])
                        else:
                            raise ValidationError(_("Partner not exist"))

                if statement_list:
                    for item in statement_list:
                        statement = self.env['account.bank.statement'].create({
                            'name': ofx_file.account.routing_number,
                            'balance_start': start_balance,
                            'balance_end_real': end_balance,
                            'line_ids': [
                                (0, 0, {
                                    'date': item[2],
                                    'payment_ref': 'ofx file',
                                    'partner_id': item[0],
                                    'journal_id': self.journal_id.id,
                                    'amount': item[1],
                                }),
                            ],
                        })
                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'Statements',
                        'view_mode': 'tree',
                        'res_model': 'account.bank.statement',
                        'res_id': statement.id,
                    }
                else:
                    raise ValidationError(_("There is no data to import"))

            # ----------------------- QIF Import -----------------------
            elif split_tup[1] == '.qif':
                file_attachment = self.env["ir.attachment"].search(
                    ['|', ('res_field', '!=', False),
                     ('res_field', '=', False),
                     ('res_id', '=', self.id),
                     ('res_model', '=', 'import.bank.statement')],
                    limit=1)
                file_path = file_attachment._full_path(
                    file_attachment.store_fname)
                try:
                    parser = QifParser()
                    with open(file_path, 'r') as qiffile:
                        qif = parser.parse(qiffile)
                except:
                    raise ValidationError(_("Wrong file format"))

                statement_list = []
                start_balance = 0.0
                end_balance = 0.0

                file_string = str(qif)
                file_item = file_string.split('^')
                file_item[-1] = file_item[-1].rstrip('\n')
                if file_item[-1] == '':
                    file_item.pop()

                for item in file_item:
                    if not item.startswith('!Type:Bank'):
                        item = '!Type:Bank' + item
                    data = item.split('\n')
                    date_entry = data[1][1:]
                    amount = float(data[2][1:])
                    payee = data[3][1:]
                    if amount and payee:
                        if not date_entry:
                            date_entry = str(fields.Date.today())
                        date_object = datetime.strptime(date_entry, '%d/%m/%Y')
                        date = date_object.strftime('%Y-%m-%d')
                        statement_list.append([payee, amount, date])
                    else:
                        if not amount:
                            raise ValidationError(_("Amount is not set"))
                        elif not payee:
                            raise ValidationError(_("Payee is not set"))

                if statement_list:
                    for item in statement_list:
                        statement = self.env['account.bank.statement'].create({
                            'name': item[0],
                            'balance_start': start_balance,
                            'balance_end_real': end_balance,
                            'line_ids': [
                                (0, 0, {
                                    'date': item[2],
                                    'payment_ref': 'qif file',
                                    'journal_id': self.journal_id.id,
                                    'amount': item[1],
                                }),
                            ],
                        })
                    return {
                        'type': 'ir.actions.act_window',
                        'name': 'Statements',
                        'view_mode': 'tree',
                        'res_model': 'account.bank.statement',
                        'res_id': statement.id,
                    }
        else:
            raise ValidationError(_("Choose correct file"))

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
from odoo.exceptions import ValidationError
from odoo import fields, models, _


class ImportPayment(models.TransientModel):
    """ Model for import payment """
    _name = 'import.payment'
    _description = 'Payment Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xlsx', 'XLS File')],
        string='Select File Type', default='xlsx',
        help='It helps to choose the file type')
    file_upload = fields.Binary(string='File Upload',
                                help='It helps to upload files')

    def action_import_payment(self):
        """ Method to import payments from .csv or .xlsx files. """
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the type and format "
                    "of the file, and try again!")
            items = csv_reader
        if self.file_type == 'xlsx':
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
            items = data
        row = 0
        imported = 0
        updated = 0
        error_msg = ""
        info_msg = ""
        if items:
            for item in items:
                row += 1
                vals = {}
                row_not_import_msg = "\nRow {rn} not imported.".format(rn=row)
                if item.get('Amount'):
                    vals['amount'] = item['Amount']
                if item.get('Date'):
                    vals['date'] = item['Date']
                if item.get('Journal'):
                    journal = self.env['account.journal'].search(
                        [('name', '=', item.get('Journal'))])
                    if journal:
                        vals['journal_id'] = journal.id
                if item.get('Customer/Vendor'):
                    partner = self.env['res.partner'].search(
                        [('name', '=', item.get('Customer/Vendor'))])
                    if not partner:
                        partner = self.env['res.partner'].create({
                            'name': item.get('Customer/Vendor')
                        })
                        info_msg += f"\nCreated new partner with name :{item.get('Customer/Vendor')}"
                    vals['partner_id'] = partner.id
                if item.get('Reference'):
                    vals['ref'] = item.get('Reference')
                if item.get('Payment Type') == 'Send':
                    vals['payment_type'] = 'outbound'
                elif item.get('Payment Type') == 'Receive':
                    vals['payment_type'] = 'inbound'
                else:
                    error_msg += row_not_import_msg + (
                        "\n\tPayment type Values is wrong in file!")
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
                error_msg = "\n\n⚠⚠⚠ERROR!!!⚠⚠⚠" + error_msg
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
            if info_msg:
                info_msg = f"\nInformation : {info_msg}"
            msg = (("Imported %d records. Updated %d records"
                    % (imported, updated)) + info_msg)
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

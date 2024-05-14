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
from datetime import date
import io
import tempfile
import xlrd
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ImportPayment(models.TransientModel):
    """For handling importing of payments"""
    _name = 'import.payment'
    _description = 'For handling importing of payments'

    name = fields.Char(string="Name", help="Name", default="Import Payments")
    file_type = fields.Selection([('csv', 'CSV File'),
                                  ('xls', 'XLS File')],
                                 string='Select File Type', default='csv',
                                 help='It helps to choose the file type')
    file_upload = fields.Binary(string='File Upload',
                                help='It helps to upload files')

    def action_payment_import(self):
        """Creating payment record using uploaded xl/csv files"""
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
        for item in datas:
            vals = {}
            if item.get('Date'):
                if self.file_type == 'csv':
                    vals['date'] = item.get('Date')
                else:
                    vals['date'] = date.fromordinal(
                        date(1900, 1, 1).toordinal() + int(
                            item.get('Date')) - 2)
            if item.get('Journal'):
                journal = self.env['account.journal'].search(
                    [('name', '=', item.get('Journal'))])
                if journal:
                    vals['journal_id'] = journal.id
                else:
                    continue
            if item.get('Customer/Vendor'):
                partner = self.env['res.partner'].search(
                    [('name', '=', item.get('Customer/Vendor'))])
                if not partner:
                    partner = self.env['res.partner'].create({
                        'name': item.get('Customer/Vendor')
                    })
                vals['partner_id'] = partner.id
            if item.get('Amount'):
                vals['amount'] = float(item.get('Amount'))
            if item.get('Reference'):
                vals['ref'] = item.get('Reference')
            if item.get('Payment Type') == 'Send':
                vals['payment_type'] = 'outbound'
            else:
                vals['payment_type'] = 'inbound'
            payment_ref = self.env['account.payment'].search(
                [('name', '=', item.get('Number'))])
            if payment_ref:
                payment_ref.write(vals)
            else:
                vals['name'] = item.get('Number') if item.get('Number') else '/'
            self.env['account.payment'].create(vals)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Imported Successfully',
                'type': 'rainbow_man',
            }
        }

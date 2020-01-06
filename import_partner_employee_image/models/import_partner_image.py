# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ijaz (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

import binascii
import tempfile

import certifi
import urllib3
import base64
import csv
import io
import xlrd

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError


class PartnerImageImportWizard(models.TransientModel):
    _name = 'import.partner_image'

    file = fields.Binary('File to import', required=True)
    file_type = fields.Selection([('csv', 'CSV'), ('xls', 'XLS')], string="File Type", default='csv')

    def import_file(self):
        if self.file_type == 'csv':

            keys = ['partner_id', 'partner_image']

            try:
                file = base64.b64decode(self.file)
                data = io.StringIO(file.decode("utf-8"))
                data.seek(0)
                file_reader = []
                csv_reader = csv.reader(data, delimiter=',')
                file_reader.extend(csv_reader)

            except:

                raise Warning(_("File is not Valid!"))

            for fr in range(len(file_reader)):
                line = list(map(str, file_reader[fr]))
                vals = dict(zip(keys, line))
                if vals:
                    if fr == 0:
                        continue
                    else:
                        vals.update({
                            'partner_id': line[0],
                            'partner_image': line[1],
                        })
                        self.import_partner_image(vals)

        elif self.file_type == 'xls':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file))
                fp.seek(0)
                vals = {}
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)

            except:
                raise Warning(_("File not Valid"))

            for row_no in range(sheet.nrows):
                val = {}
                if row_no <= 0:
                    fields = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
                else:

                    line = list(
                        map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                            sheet.row(row_no)))

                    vals.update({
                        'partner_id': line[0],
                        'partner_image': line[1],
                    })

                    self.import_partner_image(vals)
        else:
            raise UserError(_("Please select xls or csv format!"))


    def import_partner_image(self, vals):
        if vals.get('partner_id') == "":
            raise UserError(_("ID Field is Empty."))
        if vals.get('partner_image') == "":
            raise UserError(_("Image Field is Empty."))
        print('vals.get',vals.get('partner_id'))

        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                                   ca_certs=certifi.where())
        id = str(vals.get("partner_id"))
        p_id = id.rstrip('0').rstrip('.') if '.' in id else id


        if "http://" in vals.get('partner_image') or "https://" in vals.get('partner_image'):
            try:
                print('yesss')
                link = vals.get('partner_image')
                image_response = http.request('GET', link)
                image_thumbnail = base64.b64encode(image_response.data)
                image = image_thumbnail
                print('image', image_thumbnail)
            except:
                raise UserError('The Link Is Not valid')
        else:
            try:
                with open(vals.get('partner_image'), 'rb') as f:
                    data = base64.b64encode(f.read())
                    image = data
            except:

                raise UserError('The Link Is Not Valid')

        partner_id = self.env['res.partner'].search([('id', '=', p_id)], limit=1)
        print('employee_id', partner_id.name)

        partner_id.update({
            'image_1920': image,
        })


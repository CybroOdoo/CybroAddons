# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Mruthul Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import base64
import binascii
import certifi
import csv
import io
import tempfile
import urllib3
import xlrd
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


class ImportPartnerImage(models.TransientModel):
    _name = 'import.partner_image'
    _description = "Import partner image"

    file = fields.Binary(string='File to import',
                         help="Import excel or csv file", required=True)
    file_type = fields.Selection([('csv', 'CSV'), ('xls', 'XLS')],
                                 string="File Type", default='csv',
                                 help="Choose the file type")

    def action_import_file(self):
        """Import partner image based on the selected file type
        (CSV or XLS)."""
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
                raise ValidationError(_("File is not Valid!"))
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
                raise ImportError(_("File not Valid"))
            for row_no in range(sheet.nrows):
                if row_no <= 0:
                    map(lambda row: row.value.encode('utf-8'),
                        sheet.row(row_no))
                else:
                    line = list(
                        map(lambda row: isinstance(row.value,
                                                   bytes) and row.value.encode(
                            'utf-8') or str(row.value),
                            sheet.row(row_no)))
                    vals.update({
                        'partner_id': line[0],
                        'partner_image': line[1],
                    })
                    self.import_partner_image(vals)
        else:
            raise UserError(_("Please select xls or csv format!"))

    def import_partner_image(self, vals):
        """Import partner image based on the provided values.
        Args:
            vals (dict): Dictionary containing 'emp_id' and 'emp_image' keys.
        Raises:
            UserError: If the 'emp_id' or 'emp_image' field is empty.
                       If the selected file format is not valid."""
        if vals.get('partner_id') == "":
            raise UserError(_("ID Field is Empty."))
        if vals.get('partner_image') == "":
            raise UserError(_("Image Field is Empty."))
        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                                   ca_certs=certifi.where())
        id = str(vals.get("partner_id"))
        p_id = id.rstrip('0').rstrip('.') if '.' in id else id
        if "http://" in vals.get('partner_image') or "https://" in vals.get(
                'partner_image'):
            try:
                link = vals.get('partner_image')
                image_response = http.request('GET', link)
                image_thumbnail = base64.b64encode(image_response.data)
                image = image_thumbnail
            except:
                raise UserError('The Link Is Not valid')
        else:
            try:
                with open(vals.get('partner_image'), 'rb') as f:
                    data = base64.b64encode(f.read())
                    image = data
            except:
                raise UserError('The Link Is Not Valid')
        partner_id = self.env['res.partner'].search([('id', '=', p_id)],
                                                    limit=1)
        partner_id.update({
            'image_1920': image,
        })

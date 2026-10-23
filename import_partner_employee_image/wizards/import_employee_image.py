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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import base64
import certifi
import csv
import io
import os
import tempfile
import urllib3
import openpyxl
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


class ImportEmployeeImage(models.TransientModel):
    _name = 'import.employee.image'
    _description = "Import employees image from csv or excel file"

    file = fields.Binary(string='File to import',
                         help="Import excel or csv file", required=True)
    filename = fields.Char(string='File Name')
    file_type = fields.Selection([('csv', 'CSV'), ('excel', 'EXCEL')],
                                 string="File Type", default='csv',
                                 help="Choose the file type")

    def _get_raw_bytes(self, data):
        if not data:
            return b''
        if hasattr(data, 'content'):
            return data.content
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)
        if isinstance(data, str):
            data_bytes = data.encode('ascii', errors='ignore')
            data_stripped = b''.join(data_bytes.split())
            missing_padding = len(data_stripped) % 4
            if missing_padding:
                data_stripped += b'=' * (4 - missing_padding)
            return base64.b64decode(data_stripped)
        return bytes(data)

    def action_import_file(self):
        """Import employee image based on the selected file type
        (CSV or EXCEL)."""
        if not self.file:
            raise UserError(_("Please upload a file to import."))

        try:
            file_bytes = self._get_raw_bytes(self.file)
        except (UserError, ValidationError):
            raise
        except Exception as e:
            raise ValidationError(_("Invalid file format or corruption: %s", e))

        if self.file_type == 'csv':
            if file_bytes.startswith(b'PK\x03\x04'):
                raise ValidationError(_("The uploaded file appears to be an Excel (.xlsx) file, but 'File Type' is set to CSV. Please change 'File Type' to EXCEL."))

            try:
                file_str = None
                for encoding in ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252'):
                    try:
                        file_str = file_bytes.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue

                if file_str is None:
                    raise ValidationError(_("Could not decode file content. Please check file encoding."))

                data = io.StringIO(file_str)
                data.seek(0)
                first_line = data.readline()
                data.seek(0)

                delimiter = ';' if ';' in first_line and ',' not in first_line else ','
                csv_reader = csv.reader(data, delimiter=delimiter)
                file_reader = [row for row in csv_reader if row and any(cell.strip() for cell in row)]
            except (UserError, ValidationError):
                raise
            except Exception as e:
                raise ValidationError(_("File is not Valid: %s", e))

            count = 0
            for fr, line in enumerate(file_reader):
                if fr == 0:
                    continue
                vals = {
                    'emp_id': line[0].strip() if len(line) > 0 else '',
                    'emp_image': line[1].strip() if len(line) > 1 else '',
                }
                self.import_employee_image(vals)
                count += 1

        elif self.file_type == 'excel':
            if not file_bytes.startswith(b'PK\x03\x04'):
                raise ValidationError(_("The uploaded file does not appear to be an Excel (.xlsx) file. If you are uploading a CSV file, please change 'File Type' to CSV."))

            rows_data = []
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            try:
                fp.write(file_bytes)
                fp.close()

                workbook = openpyxl.load_workbook(fp.name)
                sheet = workbook.active

                for row_no, row in enumerate(sheet.iter_rows(values_only=True)):
                    if row_no == 0:
                        continue
                    line = [str(cell).strip() if cell is not None else '' for cell in row]
                    if not any(line):
                        continue
                    rows_data.append({
                        'emp_id': line[0] if len(line) > 0 else '',
                        'emp_image': line[1] if len(line) > 1 else '',
                    })
            except (UserError, ValidationError):
                raise
            except Exception as e:
                raise ValidationError(_("File not Valid: %s", e))
            finally:
                if os.path.exists(fp.name):
                    os.unlink(fp.name)

            count = 0
            for vals in rows_data:
                self.import_employee_image(vals)
                count += 1
        else:
            raise UserError(_("Please select excel or csv format!"))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Success"),
                'message': _("Successfully imported %d employee image(s).", count),
                'type': 'success',
                'sticky': False,
            }
        }

    def _clean_id(self, raw_id):
        if not raw_id:
            return ''
        raw_id = str(raw_id).strip()
        if raw_id.endswith('.0'):
            return raw_id[:-2]
        try:
            val = float(raw_id)
            if val.is_integer():
                return str(int(val))
        except ValueError:
            pass
        return raw_id

    def import_employee_image(self, vals):
        """Imports employee image based on the provided values."""
        emp_id_val = vals.get('emp_id')
        emp_image_val = vals.get('emp_image')

        if not emp_id_val:
            raise UserError(_("ID Field is Empty."))
        if not emp_image_val:
            raise UserError(_("Image Field is Empty."))

        emp_id = self._clean_id(emp_id_val)
        employee_id = self.env['hr.employee'].search([('id', '=', emp_id)], limit=1)

        if not employee_id:
            raise UserError(_("Employee with ID '%s' not found.", emp_id))

        http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
        image_val = emp_image_val.strip()

        if image_val.startswith("http://") or image_val.startswith("https://"):
            try:
                image_response = http.request('GET', image_val)
                if image_response.status == 200:
                    image = base64.b64encode(image_response.data).decode('utf-8')
                else:
                    raise UserError(_("Failed to fetch image from URL '%s' (HTTP %s).", image_val, image_response.status))
            except (UserError, ValidationError):
                raise
            except Exception as e:
                raise UserError(_("The link '%s' is not valid or accessible: %s", image_val, e))
        else:
            try:
                with open(image_val, 'rb') as f:
                    image = base64.b64encode(f.read()).decode('utf-8')
            except (UserError, ValidationError):
                raise
            except Exception as e:
                raise UserError(_("Could not read local image file '%s': %s", image_val, e))

        employee_id.write({
            'image_1920': image,
        })

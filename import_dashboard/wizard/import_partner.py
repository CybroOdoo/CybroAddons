# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha MK @cybrosys(odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.UserError
#
#############################################################################
import base64
import binascii
import csv
import io
import tempfile
import xlrd
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ImportPartner(models.TransientModel):
    """For handling importing of partners"""
    _name = 'import.partner'
    _description = 'For handling importing of partners'

    name = fields.Char(string="Name", help="Name", default="Import Partner")
    file_type = fields.Selection([('csv', 'CSV File'),
                                  ('xlsx', 'XLSX File')], default='csv',
                                 string='Import File Type', help="File type")
    method = fields.Selection(
        [('create_update', 'Create or Update Customer/Vendor'),
         ('create', 'Create Customer/Vendor')],
        string='Import Method', default='create_update',
        help="Helps to choose the import Method")
    update_by = fields.Selection([('name', 'Name'),
                                  ('email', 'Email'),
                                  ('phone', 'Phone'),
                                  ('mobile', 'Mobile')],
                                 string='Update By', default='name',
                                 help="Update using the fields")
    file_upload = fields.Binary(string="Upload File",
                                help="It helps to upload files")

    def action_partner_import(self):
        """Creating Partner record using uploaded xl/csv files"""
        res_partner = self.env['res.partner']
        res_country_state = self.env['res.country.state']
        datas = {}
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                datas = csv.DictReader(data_file, delimiter=',')
            except:
                raise ValidationError(_(
                    "File not Valid.\n\nPlease check the "
                    "type and format of the file and try again!"))
        if self.file_type == 'xlsx':
            try:
                fp = tempfile.NamedTemporaryFile(delete=False,
                                                 suffix=".xlsx")
                fp.write(binascii.a2b_base64(self.file_upload))
                fp.seek(0)
                workbook = xlrd.open_workbook(fp.name)
                sheet = workbook.sheet_by_index(0)
            except:
                raise ValidationError(_(
                    "File not Valid.\n\nPlease check the "
                    "type and format of the file and try again!"))
            headers = sheet.row_values(0)
            data = []
            for row_index in range(1, sheet.nrows):
                row = sheet.row_values(row_index)
                data += [{k: v for k, v in zip(headers, row)}]
            datas = data
        row = 0
        created = 0
        updated = 0
        error_msg = ""
        warning_msg = ""
        for item in datas:
            row += 1
            vals = {}
            row_not_import_msg = "\nRow {rn} not imported.".format(rn=row)
            if item.get('Is company? (Yes/No)') == 'Yes':
                vals['company_type'] = 'company'
            else:
                vals['company_type'] = 'person'
                if item.get('Related Company'):
                    rel_company = res_partner.search(
                        [('name', '=', item['Related Company'])])
                    if not rel_company:
                        rel_company = res_partner.create({
                            'name': item['Related Company'],
                            'company_type': "company"})
                    vals['parent_id'] = rel_company.id
            if item.get('Name'):
                vals['name'] = item['Name']
            if item.get('Street'):
                vals['street'] = item['Street']
            if item.get('Street2'):
                vals['street2'] = item['Street2']
            if item.get('City'):
                vals['city'] = item['City']
            state_vals = {}
            if item.get('Country'):
                country = self.env['res.country'].search(
                    [('name', '=', item['Country'])])
                vals['country_id'] = state_vals['country_id'] = country.id
            if item.get('State'):
                country_state = res_country_state.search(
                    [('name', '=', item['State'])])
                if not country_state:
                    state_vals['name'] = state_vals['code'] = item['State']
                    country_state = res_country_state.create(state_vals)
                vals['state_id'] = country_state.id
            if item.get('Zip'):
                vals['zip'] = item['Zip']
            if item.get('Phone'):
                vals['phone'] = item['Phone']
            if item.get('Mobile'):
                vals['mobile'] = item['Mobile']
            if item.get('Email'):
                vals['email'] = item['Email']
            if item.get('Tags'):
                tags = item['Tags'].split(',')
                tag_list = []
                for tag in tags:
                    tag_list += [tag.strip()]
                tag_ids = self.env['res.partner.category'].search(
                    [('name', 'in', tag_list)]).ids
                if not tag_ids:
                    tag_ids = []
                    for tag in tag_list:
                        tag_id = self.env['res.partner.category'].create({
                            'name': tag
                        })
                        tag_ids += [tag_id.id]
                if tag_ids:
                    vals['category_id'] = tag_ids
            if self.method == 'create_update':
                if self.update_by == 'name':
                    if item.get('Name'):
                        partner = res_partner.search([('name', '=',
                                                       item['Name'])])
                        if not partner:
                            res_partner.create(vals)
                            created += 1
                        elif len(partner) > 1:
                            error_msg += row_not_import_msg + (
                                    "\n\tMultiple Partners with name "
                                    "(%s) found!" % item['Name'])
                            continue
                        else:
                            partner.write(vals)
                            updated += 1
                    else:
                        error_msg += row_not_import_msg + (
                            "\n\tName missing!")
                        continue
                if self.update_by == 'email':
                    if item.get('Email'):
                        partner = res_partner.search([('email', '=',
                                                       item['Email'])])
                        if not partner:
                            if not vals.get('name'):
                                error_msg += row_not_import_msg + (
                                    "\n\tName missing!")
                                continue
                            else:
                                partner = res_partner.search(
                                    [('name', '=', vals['name'])])
                                if not partner:
                                    res_partner.create(vals)
                                    created += 1
                                elif len(partner) > 1:
                                    error_msg += row_not_import_msg + (
                                            "\n\tMultiple Partners with name "
                                            "(%s) found!" % item['Name'])
                                    continue
                                else:
                                    partner.write(vals)
                                    updated += 1
                        elif len(partner) > 1:
                            error_msg += row_not_import_msg + (
                                    "\n\tMultiple Partners with Email "
                                    "(%s) found!" % item['Email'])
                            continue
                        else:
                            partner.write(vals)
                            updated += 1
                    else:
                        error_msg += row_not_import_msg + (
                            "\n\tEmail missing!")
                        continue
                if self.update_by == 'phone':
                    if item.get('Phone'):
                        partner = res_partner.search([('phone', '=',
                                                       item['Phone'])])
                        if not partner:
                            if not vals.get('name'):
                                error_msg += row_not_import_msg + (
                                    "\n\tName missing!")
                                continue
                            else:
                                partner = res_partner.search(
                                    [('name', '=', vals['name'])])
                                if not partner:
                                    res_partner.create(vals)
                                    created += 1
                                elif len(partner) > 1:
                                    error_msg += row_not_import_msg + (
                                            "\n\tMultiple Partners with name "
                                            "(%s) found!" % item['Name'])
                                    continue
                                else:
                                    partner.write(vals)
                                    updated += 1
                        elif len(partner) > 1:
                            error_msg += row_not_import_msg + (
                                    "\n\tMultiple Partners with Phone "
                                    "(%s) found!" % item['Phone'])
                            continue
                        else:
                            partner.write(vals)
                            updated += 1
                    else:
                        error_msg += row_not_import_msg + (
                            "\n\tPhone missing!")
                        continue
                if self.update_by == 'mobile':
                    if item.get('Mobile'):
                        partner = res_partner.search([('mobile', '=',
                                                       item['Mobile'])])
                        if not partner:
                            if not vals.get('name'):
                                error_msg += row_not_import_msg + (
                                    "\n\tName missing!")
                                continue
                            else:
                                partner = res_partner.search(
                                    [('name', '=', vals['name'])])
                                if not partner:
                                    res_partner.create(vals)
                                    created += 1
                                elif len(partner) > 1:
                                    error_msg += row_not_import_msg + (
                                            "\n\tMultiple Partners with name "
                                            "(%s) found!" % item['Name'])
                                    continue
                                else:
                                    partner.write(vals)
                                    updated += 1
                        elif len(partner) > 1:
                            error_msg += row_not_import_msg + (
                                    "\n\tMultiple Partners with Mobile "
                                    "(%s) found!" % item['Mobile'])
                            continue
                        else:
                            partner.write(vals)
                            updated += 1
                    else:
                        error_msg += row_not_import_msg + (
                            "\n\tMobile missing!")
                        continue
            elif self.method == 'create':
                if vals.get('name'):
                    res_partner.create(vals)
                    created += 1
                else:
                    error_msg += row_not_import_msg + (
                        "\n\tName missing!")
                    continue
        if error_msg:
            error_msg = "\n\n⚠ Warning ⚠" + error_msg
        msg = (("Created %d records.\nUpdated %d records"
                % (created, updated)) + error_msg + warning_msg)
        rainbow_msg = ("Created %d records.\nUpdated %d records"
                % (created, updated))
        message = self.env['import.message'].create(
            {'message': msg})
        if message:
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': rainbow_msg,
                    'type': 'rainbow_man',
                }
            }

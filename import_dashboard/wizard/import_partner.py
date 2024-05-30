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
from odoo import fields, models
from odoo.exceptions import ValidationError


class ImportPartner(models.TransientModel):
    """ Model for import partners """
    _name = 'import.partner'
    _description = 'Partner Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xlsx', 'XLSX File')],
        string='Import File Type', default='xlsx', help="File type")
    method = fields.Selection(
        selection=[('create_update', 'Create or Update Customer/Vendor'),
                   ('create', 'Create Customer/Vendor')],
        string='Import Method', default='create_update',
        help="Helps to choose the import Method")
    update_by = fields.Selection(selection=[('name', 'Name'),
                                            ('email', 'Email'),
                                            ('phone', 'Phone'),
                                            ('mobile', 'Mobile')],
                                 string='Update By', default='name',
                                 help="Update using the fields")
    is_customer = fields.Boolean(string='Is Customer', help="Is Customer")
    is_vendor = fields.Boolean(string='Is Vendor', help="Is Vendor")
    file_upload = fields.Binary(string="Upload File",
                                help="It helps to upload files")

    def action_import_partner(self):
        """Creating Partner record using uploaded xl/csv files"""
        res_partner = self.env['res.partner']
        res_users = self.env['res.users']
        res_country_state = self.env['res.country.state']
        res_country = self.env['res.country']
        res_partner_title = self.env['res.partner.title']
        res_partner_category = self.env['res.partner.category']
        if self.file_type == 'csv':
            try:
                csv_data = base64.b64decode(self.file_upload)
                data_file = io.StringIO(csv_data.decode("utf-8"))
                data_file.seek(0)
                csv_reader = csv.DictReader(data_file, delimiter=',')
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the "
                    "type and format of the file and try again!")
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
                    "File not Valid.\n\nPlease check the "
                    "type and format of the file and try again!")
            headers = sheet.row_values(0)  # list
            data = []
            for row_index in range(1, sheet.nrows):
                row = sheet.row_values(row_index)  # list
                data += [{k: v for k, v in zip(headers, row)}]
            items = data
        row = 0
        created = 0
        updated = 0
        error_msg = ""
        warning_msg = ""
        if items:
            for item in items:
                row += 1
                vals = {}
                row_not_import_msg = "\nRow {rn} not imported.".format(rn=row)
                if item.get('Is company? (y/n)') in ['y', 'Y']:
                    vals['company_type'] = 'company'
                else:
                    vals['company_type'] = 'person'
                    if item.get('Related Company'):
                        rel_company = res_partner.search(
                            [('name', '=', item['Related Company'])])
                        vals['parent_id'] = rel_company.id
                    if item.get('Job Position'):
                        vals['function'] = item['Job Position']
                    if item.get('Title'):
                        title = res_partner_title.search(
                            [('name', '=', item['Title'])])
                        if not title:
                            title = res_partner_title.create({
                                'name': item['Title']
                            })
                        vals['title'] = title.id
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
                    country = res_country.search(
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
                if item.get('Tax ID'):
                    vals['vat'] = item['Tax ID']
                if item.get('Phone'):
                    vals['phone'] = item['Phone']
                if item.get('Mobile'):
                    vals['mobile'] = item['Mobile']
                if item.get('Email'):
                    vals['email'] = item['Email']
                if item.get('Website'):
                    vals['website'] = item['Website']
                if item.get('Tags'):
                    tags = item['Tags'].split(',')
                    tag_list = []
                    for tag in tags:
                        tag_list += [tag.strip()]
                    tag_ids = res_partner_category.search(
                        [('name', 'in', tag_list)]).ids
                    if not tag_ids:
                        tag_ids = []
                        for tag in tag_list:
                            tag_id = res_partner_category.create({
                                'name': tag
                            })
                            tag_ids += [tag_id.id]
                    if tag_ids:
                        vals['category_id'] = tag_ids
                if item.get('Salesperson'):
                    salesperson = res_users.search(
                        [('name', '=', item['Salesperson'])])
                    if not salesperson:
                        warning_msg += ("\nSalesperson (%s) not found!(row %d)"
                                        % (item['Salesperson'], row))
                    elif len(salesperson) > 1:
                        warning_msg += ("\nSalesperson not copied from row %d: "
                                        "Multiple Salespersons with name (%s) "
                                        "found!"
                                        % (row, item['Salesperson']))
                    else:
                        vals['user_id'] = salesperson.id
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
                                                "\n\t Multiple Partners with "
                                                "name (%s) found!"
                                                % item['Name'])
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
                                                "\n\tMultiple Partners with "
                                                "name (%s) found!"
                                                % item['Name'])
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
                                                "\n\tMultiple Partners with "
                                                "name (%s) found!"
                                                % item['Name'])
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
            msg = (("Created %d records.\nUpdated %d records"
                    % (created, updated)) + warning_msg)
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

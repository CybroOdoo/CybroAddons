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
import openpyxl
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

    def get_val(self, item, *keys, default=None):
        for key in keys:
            if item.get(key):
                return item.get(key)
        return default

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
                workbook = openpyxl.load_workbook(fp.name, data_only=True)
                sheet = workbook.active
            except:
                raise ValidationError(
                    "File not Valid.\n\nPlease check the "
                    "type and format of the file and try again!")
            rows = list(sheet.rows)
            headers = [cell.value for cell in rows[0]]
            data = []
            for row in rows[1:]:
                data += [{k: v.value for k, v in zip(headers, row)}]
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
                is_company = self.get_val(item, 'Is company? (y/n)', 'Is Company')
                if is_company in ['y', 'Y']:
                    vals['company_type'] = 'company'
                else:
                    vals['company_type'] = 'person'
                    related_company = self.get_val(item, 'Related Company', 'Parent Company')
                    if related_company:
                        rel_company = res_partner.search(
                            [('name', '=', related_company)])
                        vals['parent_id'] = rel_company.id
                    job_position = self.get_val(item, 'Job Position')
                    if job_position:
                        vals['function'] = job_position
                    title_name = self.get_val(item, 'Title')
                    if title_name:
                        title = res_partner_title.search(
                            [('name', '=', title_name)])
                        if not title:
                            title = res_partner_title.create({
                                'name': title_name
                            })
                        vals['title'] = title.id
                name = self.get_val(item, 'Name')
                if name:
                    vals['name'] = name
                street = self.get_val(item, 'Street')
                if street:
                    vals['street'] = street
                street2 = self.get_val(item, 'Street2')
                if street2:
                    vals['street2'] = street2
                city = self.get_val(item, 'City')
                if city:
                    vals['city'] = city
                state_vals = {}
                country_name = self.get_val(item, 'Country')
                if country_name:
                    country = res_country.search(
                        [('name', '=', country_name)])
                    vals['country_id'] = state_vals['country_id'] = country.id
                state_name = self.get_val(item, 'State')
                if state_name:
                    country_state = res_country_state.search(
                        [('name', '=', state_name)])
                    if not country_state:
                        state_vals['name'] = state_vals['code'] = state_name
                        country_state = res_country_state.create(state_vals)
                    vals['state_id'] = country_state.id
                zip_val = self.get_val(item, 'Zip')
                if zip_val:
                    vals['zip'] = zip_val
                tax_id = self.get_val(item, 'Tax ID')
                if tax_id:
                    vals['vat'] = tax_id
                phone = self.get_val(item, 'Phone')
                if phone:
                    vals['phone'] = phone
                mobile = self.get_val(item, 'Mobile')
                if mobile:
                    vals['mobile'] = mobile
                email = self.get_val(item, 'Email')
                if email:
                    vals['email'] = email
                website = self.get_val(item, 'Website')
                if website:
                    vals['website'] = website
                tags_val = self.get_val(item, 'Tags')
                if tags_val:
                    tags = tags_val.split(',')
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
                salesperson_name = self.get_val(item, 'Salesperson')
                if salesperson_name:
                    salesperson = res_users.search(
                        [('name', '=', salesperson_name)])
                    if not salesperson:
                        warning_msg += ("\nSalesperson (%s) not found!(row %d)"
                                        % (salesperson_name, row))
                    elif len(salesperson) > 1:
                        warning_msg += ("\nSalesperson not copied from row %d: "
                                        "Multiple Salespersons with name (%s) "
                                        "found!"
                                        % (row, salesperson_name))
                    else:
                        vals['user_id'] = salesperson.id
                # --- UPDATE LOGIC ---
                if self.method == 'create_update':
                    if self.update_by == 'name':
                        if name:
                            partner = res_partner.search([('name', '=', name)])
                            if not partner:
                                res_partner.create(vals)
                                created += 1
                            elif len(partner) > 1:
                                error_msg += row_not_import_msg + (
                                        "\n\tMultiple Partners with name "
                                        "(%s) found!" % name)
                                continue
                            else:
                                partner.write(vals)
                                updated += 1
                        else:
                            error_msg += row_not_import_msg + (
                                "\n\tName missing!")
                            continue
                    if self.update_by == 'email':
                        if email:
                            partner = res_partner.search([('email', '=', email)])
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
                                                % name)
                                        continue
                                    else:
                                        partner.write(vals)
                                        updated += 1
                            elif len(partner) > 1:
                                error_msg += row_not_import_msg + (
                                        "\n\tMultiple Partners with Email "
                                        "(%s) found!" % email)
                                continue
                            else:
                                partner.write(vals)
                                updated += 1
                        else:
                            error_msg += row_not_import_msg + (
                                "\n\tEmail missing!")
                            continue
                    if self.update_by == 'phone':
                        if phone:
                            partner = res_partner.search([('phone', '=', phone)])
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
                                                % name)
                                        continue
                                    else:
                                        partner.write(vals)
                                        updated += 1
                            elif len(partner) > 1:
                                error_msg += row_not_import_msg + (
                                        "\n\tMultiple Partners with Phone "
                                        "(%s) found!" % phone)
                                continue
                            else:
                                partner.write(vals)
                                updated += 1
                        else:
                            error_msg += row_not_import_msg + (
                                "\n\tPhone missing!")
                            continue
                    if self.update_by == 'mobile':
                        if mobile:
                            partner = res_partner.search([('mobile', '=', mobile)])
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
                                                % name)
                                        continue
                                    else:
                                        partner.write(vals)
                                        updated += 1
                            elif len(partner) > 1:
                                error_msg += row_not_import_msg + (
                                        "\n\tMultiple Partners with Mobile "
                                        "(%s) found!" % mobile)
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
        return False

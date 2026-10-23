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
from .import_utils import get_file_content, read_csv_data, read_xlsx_data
from odoo import fields, models
from odoo.exceptions import ValidationError


class ImportPartner(models.TransientModel):
    """ Model for import partners """
    _name = 'import.partner'
    _description = 'Partner Import'

    file_type = fields.Selection(
        selection=[('csv', 'CSV File'), ('xlsx', 'XLSX File')],
        string='Import File Type', default='xlsx', help="Type of the file to import")
    method = fields.Selection(
        selection=[('create_update', 'Create or Update Customer/Vendor'),
                   ('create', 'Create Customer/Vendor')],
        string='Import Method', default='create_update',
        help="Create new partners only, or also update existing ones")
    update_by = fields.Selection(selection=[('name', 'Name'),
                                            ('email', 'Email'),
                                            ('phone', 'Phone')],
                                 default='name',
                                 help="Partner field used to match existing partners")
    is_customer = fields.Boolean(help="Is Customer")
    is_vendor = fields.Boolean(help="Is Vendor")
    file_upload = fields.Binary(string="Upload File",
                                help="File to import")

    def action_import_partner(self):
        """Creating Partner record using uploaded xl/csv files"""
        res_partner = self.env['res.partner'].with_context(no_vat_validation=True)
        res_users = self.env['res.users']
        res_country_state = self.env['res.country.state']
        res_country = self.env['res.country']
        res_partner_category = self.env['res.partner.category']
        items = []
        if self.file_type == 'csv':
            try:
                items = read_csv_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the "
                               "type and format of the file and try again!"))
        if self.file_type == 'xlsx':
            try:
                items = read_xlsx_data(get_file_content(self))
            except Exception:
                raise ValidationError(
                    self.env._("File not valid.\n\nPlease check the "
                               "type and format of the file and try again!"))
        row = 0
        created = 0
        updated = 0
        error_msg = ""
        warning_msg = ""
        if items:
            for item in items:
                row += 1
                vals = {}
                row_not_import_msg = self.env._("\nRow %(rn)s not imported.", rn=row)
                if item.get('Is company? (y/n)') in ['y', 'Y']:
                    vals['is_company'] = True
                else:
                    vals['is_company'] = False
                    if item.get('Related Company'):
                        rel_company = res_partner.search(
                            [('name', '=', item['Related Company'])], limit=1)
                        if rel_company:
                            vals['parent_id'] = rel_company.id
                    if item.get('Job Position'):
                        vals['function'] = item['Job Position']
                name = item.get('Name') or item.get('Complete Name')
                if name:
                    vals['name'] = str(name).strip()
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
                        warning_msg += (self.env._("\nSalesperson (%(salesperson)s) not found! (row %(row)d)", salesperson=item['Salesperson'], row=row))
                    elif len(salesperson) > 1:
                        warning_msg += (self.env._("\nSalesperson not copied from row %(row)d: Multiple Salespersons with name (%(salesperson)s) found!", row=row, salesperson=item['Salesperson']))
                    else:
                        vals['user_id'] = salesperson.id
                try:
                    if self.method == 'create_update':
                        if self.update_by == 'name':
                            name = item.get('Name') or item.get('Complete Name')
                            if name:
                                partner = res_partner.search([('name', '=',
                                                               name)])
                                if not partner:
                                    res_partner.create(vals)
                                    created += 1
                                elif len(partner) > 1:
                                    error_msg += row_not_import_msg + (
                                            self.env._("\n\tMultiple Partners with name "
                                            "(%s) found!", name))
                                    continue
                                else:
                                    partner.write(vals)
                                    updated += 1
                            else:
                                error_msg += row_not_import_msg + (
                                    self.env._("\n\tName missing!"))
                                continue
                        if self.update_by == 'email':
                            if item.get('Email'):
                                partner = res_partner.search([('email', '=',
                                                               item['Email'])])
                                if not partner:
                                    if not vals.get('name'):
                                        error_msg += row_not_import_msg + (
                                            self.env._("\n\tName missing!"))
                                        continue
                                    else:
                                        partner = res_partner.search(
                                            [('name', '=', vals['name'])])
                                        if not partner:
                                            res_partner.create(vals)
                                            created += 1
                                        elif len(partner) > 1:
                                            error_msg += row_not_import_msg + (
                                                    self.env._("\n\t Multiple Partners with "
                                                    "name (%s) found!", name))
                                            continue
                                        else:
                                            partner.write(vals)
                                            updated += 1
                                elif len(partner) > 1:
                                    error_msg += row_not_import_msg + (
                                            self.env._("\n\tMultiple Partners with Email "
                                            "(%s) found!", item['Email']))
                                    continue
                                else:
                                    partner.write(vals)
                                    updated += 1
                            else:
                                error_msg += row_not_import_msg + (
                                    self.env._("\n\tEmail missing!"))
                                continue
                        if self.update_by == 'phone':
                            if item.get('Phone'):
                                partner = res_partner.search([('phone', '=',
                                                               item['Phone'])])
                                if not partner:
                                    if not vals.get('name'):
                                        error_msg += row_not_import_msg + (
                                            self.env._("\n\tName missing!"))
                                        continue
                                    else:
                                        partner = res_partner.search(
                                            [('name', '=', vals['name'])])
                                        if not partner:
                                            res_partner.create(vals)
                                            created += 1
                                        elif len(partner) > 1:
                                            error_msg += row_not_import_msg + (
                                                    self.env._("\n\tMultiple Partners with "
                                                    "name (%s) found!", name))
                                            continue
                                        else:
                                            partner.write(vals)
                                            updated += 1
                                elif len(partner) > 1:
                                    error_msg += row_not_import_msg + (
                                            self.env._("\n\tMultiple Partners with Phone "
                                            "(%s) found!", item['Phone']))
                                    continue
                                else:
                                    partner.write(vals)
                                    updated += 1
                            else:
                                error_msg += row_not_import_msg + (
                                    self.env._("\n\tPhone missing!"))
                                continue
                    elif self.method == 'create':
                        if vals.get('name'):
                            res_partner.create(vals)
                            created += 1
                        else:
                            error_msg += row_not_import_msg + (
                                self.env._("\n\tName missing!"))
                            continue
                except Exception as e:
                    error_msg += row_not_import_msg + self.env._("\n\t%(e)s", e=e)
                    continue
            if error_msg:
                error_msg = self.env._("\n\n⚠ Warning ⚠") + error_msg
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
            msg = ((self.env._("Created %(created)d records.\nUpdated %(updated)d records", created=created, updated=updated)) + warning_msg)
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

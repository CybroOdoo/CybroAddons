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
import io

from openpyxl.reader.excel import load_workbook

from odoo import Command, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class UserImport(models.TransientModel):
    """Import User with access right"""
    _name = 'user.import'
    _description = 'User Import'

    file = fields.Binary(string="Upload File", help='Upload the file here')

    def _find_user_type_group(self, user_type):
        """ Resolve user type input string to the corresponding res.groups record """
        if not user_type:
            return self.env['res.groups']

        normalized = user_type.strip().lower()
        mapping = {
            'internal user': 'base.group_user',
            'internal': 'base.group_user',
            'user': 'base.group_user',
            'role / user': 'base.group_user',
            'user types / internal user': 'base.group_user',
            'portal': 'base.group_portal',
            'portal user': 'base.group_portal',
            'role / portal': 'base.group_portal',
            'user types / portal': 'base.group_portal',
            'public': 'base.group_public',
            'public user': 'base.group_public',
            'role / public': 'base.group_public',
            'user types / public': 'base.group_public',
        }
        if normalized in mapping:
            group = self.env.ref(mapping[normalized], raise_if_not_found=False)
            if group:
                return group

        return self.env['res.groups'].search([
            '|', ('full_name', '=ilike', user_type), ('name', '=ilike', user_type),
        ], limit=1)

    def import_file(self):
        """ function to import user from xlsx file """
        if self:
            try:
                file_data = self.file.content

                book = load_workbook(io.BytesIO(file_data))
                sheet = book.active

            except Exception as e:
                raise ValidationError(
                    _("Please choose the correct file: %s") % str(e)
                )
            startline = True
            for i in range(1, sheet.max_row + 1):
                if startline:
                    startline = False
                    continue

                line = [cell.value for cell in sheet[i]]  # Get values in the row
                if not any(cell is not None and str(cell).strip() != '' for cell in line):
                    continue

                res_lang = self.env['res.lang']
                res_groups = self.env['res.groups']
                res_company = self.env['res.company']
                language = str(line[2] or '').strip()
                company_name = str(line[3] or '').strip()
                user_type = str(line[4] or '').strip()
                groups_text = str(line[5] or '').strip()
                technical_settings_text = str(line[6] or '').strip()

                if not language or not res_lang.search([
                    ('code', '=', language), ('active', '=', True),
                ]):
                    raise ValidationError(_("Language %s is not active") % (
                        language or _("(empty)")))

                company = False
                if company_name:
                    company = res_company.search([
                        '|', ('name', '=ilike', company_name), ('display_name', '=ilike', company_name),
                    ], limit=1)
                    if not company:
                        raise ValidationError(_("Company %s does not exist") % company_name)

                user_type_group = self._find_user_type_group(user_type) if user_type else False

                if not user_type or not user_type_group:
                    raise ValidationError(_("Invalid User Type %s") % (
                        user_type or _("(empty)")))

                groups = [group.strip() for group in groups_text.split(',') if group.strip()]
                access_right = []
                invalid_groups = []
                for group_name in groups:
                    grp = res_groups.search([
                        '|', ('full_name', '=ilike', group_name), ('name', '=ilike', group_name),
                    ], limit=1)
                    if grp:
                        access_right.append(grp.id)
                    else:
                        invalid_groups.append(group_name)

                if invalid_groups:
                    raise ValidationError(_("Invalid groups %s") % (
                        " ".join(invalid_groups)))

                tech_settings = [
                    setting.strip() for setting in technical_settings_text.split(',')
                    if setting.strip()
                ]
                tech_rights = []
                if tech_settings:
                    tech_rights = res_groups.search([
                        '|', ('name', 'in', tech_settings), ('full_name', 'in', tech_settings),
                    ]).ids
                group_ids = list(set([user_type_group.id] + access_right + tech_rights))

                if not line[0]:
                    raise ValidationError(_('Please enter the user name.'))

                user_vals = {
                    'name': line[0],
                    'login': line[1],
                    'lang': language,
                    'group_ids': [Command.set(group_ids)],
                }
                if company:
                    user_vals['company_id'] = company.id
                    user_vals['company_ids'] = [Command.set([company.id])]

                self.env['res.users'].create([user_vals])

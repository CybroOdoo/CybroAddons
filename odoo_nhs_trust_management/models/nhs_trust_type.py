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
from odoo import models, fields, api

class NhsTrustType(models.Model):
    _name = 'nhs.trust.type'
    _description = 'NHS Trust Type'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Name', 
        required=True,
        translate=True,
        index='trigram',
        help="Display name (e.g. 'Acute Trust', 'Mental Health Trust'). "
             "Translatable so multi-language deployments can localise."
    )
    code = fields.Char(
        string='Code', 
        required=True, 
        index=True,
        help="Unique short code (e.g. 'ACUTE', 'MH', 'SCO-TERR'). "
             "Used for CSV imports and Excel exports — keep stable."
    )
    sequence = fields.Integer(
        string='Sequence', 
        default=10,
        help="Display order in the dropdown. Lower numbers appear first. "
             "Use multiples of 5 to allow insertions."
    )
    health_system = fields.Selection([
        ('nhs_england', 'NHS England Only'),
        ('nhs_scotland', 'NHS Scotland Only'),
        ('both', 'Both Health Systems'),
    ], 
        string='Health System Applicability', 
        required=True, 
        default='both', 
        index=True,
        help="Filters the dropdown on the Trust form so users only see "
             "types applicable to the Trust's health system."
    )
    description = fields.Text(
        string='Description',
        help="Long-form description shown in the type configuration form. Helps administrators choose the right type."
    )
    active = fields.Boolean(
        string='Active', 
        default=True,
        help="Archive flag."
    )


    _code_unique = models.Constraint(
        'unique(code)',
        'The NHS Trust Type code must be unique!',
    )

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if 'name' not in default:
            for ttype, vals in zip(self, vals_list):
                vals['name'] = self.env._("%s (copy)", ttype.name)
        if 'code' not in default:
            for ttype, vals in zip(self, vals_list):
                base_code = ttype.code or ''
                new_code = base_code
                count = 1
                while self.env['nhs.trust.type'].search_count([('code', '=', new_code)]):
                    new_code = f"{base_code}_{count}"
                    count += 1
                vals['code'] = new_code
        return vals_list

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

class NhsIcs(models.Model):
    _name = 'nhs.ics'
    _description = 'NHS Integrated Care System (ICS)'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Name', 
        required=True, 
        index=True,
        help="Full statutory name (e.g. 'Frimley ICS')."
    )
    code = fields.Char(
        string='ODS Code', 
        required=True, 
        index=True,
        help="Unique short code."
    )
    icb_id = fields.Many2one(
        'nhs.icb', 
        string='Integrated Care Board (ICB)', 
        required=True, 
        ondelete='cascade', 
        index=True,
        help="Parent ICB. ondelete='cascade' — if the ICB is deleted, the ICS goes too."
    )
    region_id = fields.Many2one(
        'nhs.region', 
        string='NHS Region', 
        related='icb_id.region_id', 
        store=True, 
        index=True,
        help="Related to icb_id.region_id, stored. Lets users group ICSs by region in list views."
    )
    description = fields.Text(
        string='Description',
        help="Free-text description of the ICS's footprint and member organisations."
    )
    active = fields.Boolean(
        string='Active', 
        default=True,
        help="Archive flag."
    )


    _code_unique = models.Constraint(
        'unique(code)',
        'The ICS ODS code must be unique!',
    )

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if 'name' not in default:
            for ics, vals in zip(self, vals_list):
                vals['name'] = self.env._("%s (copy)", ics.name)
        if 'code' not in default:
            for ics, vals in zip(self, vals_list):
                base_code = ics.code or ''
                new_code = base_code
                count = 1
                while self.env['nhs.ics'].search_count([('code', '=', new_code)]):
                    new_code = f"{base_code}_{count}"
                    count += 1
                vals['code'] = new_code
        return vals_list

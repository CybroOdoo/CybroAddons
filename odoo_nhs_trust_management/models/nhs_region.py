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

class NhsRegion(models.Model):
    _name = 'nhs.region'
    _description = 'NHS Region'
    _order = 'health_system, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Name', 
        required=True,
        translate=True,
        index='trigram',
        help="Full region name (e.g. 'North East and Yorkshire'). Used in the breadcrumb on Trust forms."
    )
    code = fields.Char(
        string='Code', 
        required=True, 
        index=True,
        help="Short region code (e.g. 'NEY' for England, 'SCO-N' for Scotland). "
             "Must be unique. Used in Excel exports and the PDF profile header."
    )
    health_system = fields.Selection([
        ('nhs_england', 'NHS England'),
        ('nhs_scotland', 'NHS Scotland'),
    ], 
        string='Health System', 
        required=True, 
        default='nhs_england', 
        index=True,
        help="Selection: 'nhs_england' or 'nhs_scotland'. Default: 'nhs_england'. "
             "Drives downstream filtering — a region only appears in the dropdown when the Trust's health_system matches."
    )
    trust_count = fields.Integer(
        string='Trusts Count', 
        compute='_compute_trust_count',
        help="Live count of Trusts attached to this region. Displayed on the stat button in the region form."
    )
    active = fields.Boolean(
        string='Active', 
        default=True,
        help="Standard Odoo archive flag. Archived regions remain on existing records but disappear from new dropdowns."
    )


    _code_unique = models.Constraint(
        'unique(code)',
        'The NHS Region code must be unique!',
    )

    @api.depends('health_system')
    def _compute_trust_count(self):
        # Efficiently compute count of trusts per region using _read_group
        trust_data = self.env['nhs.trust']._read_group(
            [('region_id', 'in', self.ids)],
            ['region_id'],
            ['__count']
        )
        mapped_data = {region.id: count for region, count in trust_data if region}
        for region in self:
            region.trust_count = mapped_data.get(region.id, 0)

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if 'name' not in default:
            for region, vals in zip(self, vals_list):
                vals['name'] = self.env._("%s (copy)", region.name)
        if 'code' not in default:
            for region, vals in zip(self, vals_list):
                base_code = region.code or ''
                new_code = base_code
                count = 1
                while self.env['nhs.region'].search_count([('code', '=', new_code)]):
                    new_code = f"{base_code}_{count}"
                    count += 1
                vals['code'] = new_code
        return vals_list

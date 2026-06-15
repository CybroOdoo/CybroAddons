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
from odoo.exceptions import ValidationError


class NhsTrustDepartment(models.Model):
    _name = 'nhs.trust.department'
    _description = 'NHS Trust Department'
    _order = 'site_id, name'

    name = fields.Char(
        string='Department Name',
        required=True,
        help="Department name."
    )
    code = fields.Char(
        string='Department Code',
        help="Optional internal department code used by the Trust's own systems (PAS/ESR/ledger codes)."
    )
    site_id = fields.Many2one(
        'nhs.trust.site',
        string='Parent Site',
        required=True,
        ondelete='cascade',
        index=True,
        help="Parent site. ondelete='cascade'."
    )
    trust_id = fields.Many2one(
        'nhs.trust',
        string='Trust',
        related='site_id.trust_id',
        store=True,
        index=True,
        help="Related to site_id.trust_id, stored for security rules and reporting filters."
    )
    department_type = fields.Selection([
        ('clinical', 'Clinical'),
        ('corporate', 'Corporate'),
        ('support', 'Support'),
        ('research', 'Research'),
    ],
        string='Department Type',
        required=True,
        default='clinical',
        help="Clinical = direct patient care. Corporate = HR/Finance/IT. "
             "Support = Pharmacy/Pathology/Estates. Research = R&D, trials."
    )
    specialty_id = fields.Many2one(
        'nhs.trust.specialty',
        string='Primary Specialty',
        help="Primary clinical specialty (for clinical departments)."
    )
    head_of_department_id = fields.Many2one(
        'res.partner',
        string='Head of Department',
        help="Departmental clinical or operational lead."
    )
    staff_count = fields.Integer(
        string='Staff Count',
        default=0,
        help="Headcount or FTE — the choice is per the Trust's convention."
             " Document which one in your data entry standards."
    )
    phone = fields.Char(
        string='Phone',
        help="Department-level contact details."
    )
    email = fields.Char(
        string='Email',
        help="Department-level contact details."
    )
    description = fields.Text(
        string='Description',
        help="Free-text description."
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Archive flag."
    )

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if 'name' not in default:
            for dept, vals in zip(self, vals_list):
                vals['name'] = "%s (copy)" % dept.name
        return vals_list

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'site_id' in vals and vals['site_id']:
                site = self.env['nhs.trust.site'].browse(vals['site_id'])
                if site.trust_id.state == 'dissolved':
                    raise ValidationError("You cannot create a department under a dissolved trust!")
        return super().create(vals_list)

    def write(self, vals):
        if 'site_id' in vals and vals['site_id']:
            site = self.env['nhs.trust.site'].browse(vals['site_id'])
            if site.trust_id.state == 'dissolved':
                raise ValidationError("You cannot link a department to a site of a dissolved trust!")
        for record in self:
            if record.site_id.trust_id.state == 'dissolved':
                raise ValidationError("You cannot modify a department belonging to a dissolved trust!")
        return super().write(vals)

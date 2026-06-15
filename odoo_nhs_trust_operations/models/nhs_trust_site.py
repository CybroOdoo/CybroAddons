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
from odoo.exceptions import UserError, ValidationError


class NhsTrustSpecialty(models.Model):
    _name = 'nhs.trust.specialty'
    _description = 'NHS Clinical Specialty'
    _order = 'name'

    name = fields.Char(
        string='Specialty Name',
        required=True,
        translate=True,
        help="Specialty name (e.g. 'Cardiology', 'Trauma & Orthopaedics', 'Maternity'). Translatable."
    )
    code = fields.Char(
        string='NHS Code',
        required=True,
        help="NHS Data Dictionary specialty code (e.g. '320' for Cardiology, '110' for T&O). Must be unique across all specialties."
    )
    description = fields.Text(
        string='Description',
        help="Short description of what the specialty covers."
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Archive flag."
    )

    _name_unique = models.Constraint(
        'unique(name)',
        'Specialty name must be unique across the NHS system!',
    )
    _code_unique = models.Constraint(
        'unique(code)',
        'Specialty code must be unique across the NHS system!',
    )

    @api.constrains('name', 'code')
    def _check_name_code_unique(self):
        for rec in self:
            if self.search_count([('name', '=', rec.name), ('id', '!=', rec.id)]) > 0:
                raise ValidationError(
                    'Specialty name "%s" already exists. Each specialty name must be unique across the NHS system.' % rec.name
                )
            if self.search_count([('code', '=', rec.code), ('id', '!=', rec.id)]) > 0:
                raise ValidationError(
                    'NHS Code "%s" already exists. Each specialty code must be unique across the NHS system.' % rec.code
                )

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if 'name' not in default:
            for specialty, vals in zip(self, vals_list):
                vals['name'] = "%s (copy)" % specialty.name
        if 'code' not in default:
            for specialty, vals in zip(self, vals_list):
                base_code = specialty.code or ''
                new_code = base_code
                count = 1
                while self.env['nhs.trust.specialty'].search_count([('code', '=', new_code)]):
                    new_code = f"{base_code}-{count}"
                    count += 1
                vals['code'] = new_code
        return vals_list


class NhsTrustSite(models.Model):
    _name = 'nhs.trust.site'
    _description = 'NHS Trust Site / Hospital'
    _inherit = ['mail.thread']
    _order = 'trust_id, name'

    name = fields.Char(
        string='Site Name',
        required=True,
        tracking=True,
        help="Site name (e.g. 'The Royal London Hospital', 'Whipps Cross University Hospital')."
    )
    code = fields.Char(
        string='ODS Sub-Code',
        help="ODS sub-code for the site (e.g. 'RNJ12' is a sub-code of trust RNJ)."
             " Used in datasets that drill below trust level."
    )
    trust_id = fields.Many2one(
        'nhs.trust',
        string='Parent Trust',
        required=True,
        ondelete='cascade',
        index=True,
        help="Parent Trust. ondelete='cascade' — deleting the trust cascades to sites."
    )
    site_type = fields.Selection([
        ('acute_hospital', 'Acute Hospital'),
        ('teaching_hospital', 'Teaching Hospital'),
        ('community_hospital', 'Community Hospital'),
        ('mental_health_unit', 'Mental Health Unit'),
        ('clinic', 'Clinic'),
        ('community_centre', 'Community Centre'),
        ('ambulance_station', 'Ambulance Station'),
        ('admin_office', 'Admin Office'),
        ('other', 'Other'),
    ],
        string='Site Type',
        required=True,
        default='acute_hospital',
        help="Drives filtering and reporting. Teaching hospitals are typically the "
             "larger university-affiliated sites with research and training roles."
    )

    # Address
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    county = fields.Char(string='County')
    zip = fields.Char(string='Postcode')
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        default=lambda self: self.env.ref('base.uk', raise_if_not_found=False),
    )
    phone = fields.Char(
        string='Phone',
        help="Site main phone — rendered with phone widget."
    )
    email = fields.Char(
        string='Email',
        help="Site general email."
    )

    # GPS
    latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
        help="GPS latitude in decimal degrees (e.g. 51.5176 for London Hospital). "
             "Reserved for a future map view. 7 decimals = ~11mm precision."
    )
    longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
        help="GPS longitude (e.g. -0.0598 for London Hospital)."
    )

    site_manager_id = fields.Many2one(
        'res.partner',
        string='Site Manager',
        help="Person responsible for site-level operations (typically a General Manager or Site Director)."
    )

    # A&E
    has_ae_department = fields.Boolean(
        string='Has A&E Department',
        default=False,
        help="Tick if the site has an A&E / Emergency Department. Drives the red 'A&E' badge on kanban cards."
    )
    ae_type = fields.Selection([
        ('type1', 'Type 1 – Major / Consultant-led 24h A&E'),
        ('type2', 'Type 2 – Single Specialty A&E'),
        ('type3', 'Type 3 – Minor Injury Unit / Urgent Care Centre'),
        ('type4', 'Type 4 – Walk-in Centre / Minor Injury Unit'),
    ],
        string='A&E Type',
        help="Select the Accident & Emergency (A&E) service type available at this site."
             "This field is applicable only if the site has an A&E department."
    )

    # Capacity
    bed_capacity = fields.Integer(
        string='Bed Capacity',
        default=0,
        help="Total available overnight beds at this site. Summed up to Trust.total_bed_capacity."
    )
    icu_bed_capacity = fields.Integer(
        string='ICU Bed Capacity',
        default=0,
        help="Intensive Care Unit (Level 3 critical care) beds. Subset of bed_capacity."
    )
    operating_theatres = fields.Integer(
        string='Operating Theatres',
        default=0,
        help="Number of operating theatres on site."
    )
    opening_hours = fields.Char(
        string='Opening Hours',
        help="Free-text description (e.g. '24/7', 'Mon-Fri 08:00-18:00'). "
             "Not structured because patterns vary widely."
    )

    # Relationships
    specialty_ids = fields.Many2many(
        'nhs.trust.specialty',
        string='Clinical Specialties',
        help="Clinical specialties offered at this site. Helps patients and commissioners find the right site."
    )
    department_ids = fields.One2many(
        'nhs.trust.department',
        'site_id',
        string='Departments',
        help="Departments based at this site (Acute Medicine, Pharmacy, Radiology, etc.)."
    )
    department_count = fields.Integer(
        string='Department Count',
        compute='_compute_department_count',
        help="Count for the stat button."
    )
    notes = fields.Text(
        string='Notes',
        help="Free-text operational notes."
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Archive flag — archive a site rather than delete it to preserve historical data."
    )

    @api.depends('department_ids')
    def _compute_department_count(self):
        for site in self:
            site.department_count = len(site.department_ids)

    def action_view_departments(self):
        self.ensure_one()
        return {
            'name': 'Departments',
            'type': 'ir.actions.act_window',
            'res_model': 'nhs.trust.department',
            'view_mode': 'list,form',
            'domain': [('site_id', '=', self.id)],
            'context': {'default_site_id': self.id, 'default_trust_id': self.trust_id.id},
        }

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if 'name' not in default:
            for site, vals in zip(self, vals_list):
                vals['name'] = "%s (copy)" % site.name
        return vals_list

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'trust_id' in vals and vals['trust_id']:
                trust = self.env['nhs.trust'].browse(vals['trust_id'])
                if trust.state == 'dissolved':
                    raise ValidationError("You cannot create a site under a dissolved trust!")
        return super().create(vals_list)

    def write(self, vals):
        if 'trust_id' in vals and vals['trust_id']:
            trust = self.env['nhs.trust'].browse(vals['trust_id'])
            if trust.state == 'dissolved':
                raise ValidationError("You cannot link a site to a dissolved trust!")
        for record in self:
            if record.trust_id.state == 'dissolved':
                raise ValidationError("You cannot modify a site belonging to a dissolved trust!")
        return super().write(vals)

    def unlink(self):
        for site in self:
            if site.department_ids:
                raise UserError(f"You cannot delete Site '{site.name}' because it has associated departments. "
                                f"Please remove or relocate all departments first.")
        return super(NhsTrustSite, self).unlink()

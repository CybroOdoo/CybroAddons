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


class NhsWelshLhb(models.Model):
    """Represent a Welsh Local Health Board (LHB)."""
    _name = 'nhs.welsh.lhb'
    _inherit = ['mail.thread']
    _description = 'NHS Wales Local Health Board'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        help="Full statutory name e.g. 'Aneurin Bevan University Health Board'.",
    )
    name_cy = fields.Char(
        string='Welsh Name (Cymraeg)',
        help="Welsh-language name stored separately for bilingual reports.",
    )
    code = fields.Char(
        string='ODS Code',
        required=True,
        index=True,
        size=3,
        help="Official ODS code for the LHB (e.g. '7A6'). 3 characters starting with 7A.",
    )
    short_name = fields.Char(
        string='Short Name',
        help="Short display name (e.g. 'Aneurin Bevan UHB'). Shown in kanban cards and narrow columns.",
    )
    region_id = fields.Many2one(
        'nhs.region',
        string='Region',
        required=True,
        domain=[('health_system', '=', 'nhs_wales')],
        help="Should always point at the Wales region.",
    )
    lhb_type = fields.Selection([
        ('university', 'University Health Board'),
        ('teaching', 'Teaching Health Board'),
    ], string='LHB Type', required=True, default='university',
        help="Six of the seven LHBs use the University prefix. Powys uses Teaching Health Board.",
    )
    population_served = fields.Integer(
        string='Population Served',
        help="Resident population the LHB plans services for (ONS mid-year estimate).",
    )
    area_served_km2 = fields.Integer(
        string='Area Served (km²)',
        help="Geographic area covered in km².",
    )
    headquarters_address = fields.Text(
        string='HQ Address',
        help="Free-text HQ address.",
    )
    website = fields.Char(
        string='Website',
        help="Public LHB website URL.",
    )
    chair_id = fields.Many2one(
        'res.partner',
        string='Chair',
        help="LHB Chair.",
    )
    chief_executive_id = fields.Many2one(
        'res.partner',
        string='Chief Executive',
        tracking=True,
        help="LHB Chief Executive / Accountable Officer.",
    )
    trust_ids = fields.One2many(
        'nhs.trust',
        'welsh_lhb_id',
        string='Trusts',
        help="All trust records whose welsh_lhb_id points to this LHB.",
    )
    trust_count = fields.Integer(
        string='Trust Count',
        compute='_compute_trust_count',
        help="Number of linked trust records.",
    )
    established_date = fields.Date(
        string='Established Date',
        help="Date the LHB was legally established.",
    )
    active = fields.Boolean(
        default=True,
        string='Active',
        help="Set to False to archive the record.",
    )

    _code_uniq = models.Constraint('unique(code)', 'The LHB ODS code must be unique!')
    _name_uniq = models.Constraint('unique(name)', 'The LHB name must be unique!')

    @api.depends('trust_ids')
    def _compute_trust_count(self):
        """Compute the number of associated trusts for the LHB."""
        for rec in self:
            rec.trust_count = len(rec.trust_ids)

    @api.constrains('code')
    def _check_code_format(self):
        """Validate the LHB ODS code format."""
        for rec in self:
            if rec.code and (len(rec.code) != 3 or not rec.code.upper().startswith('7A')):
                raise ValidationError(
                    "LHB ODS code must be 3 characters starting with '7A' (e.g. '7A6')."
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to enforce uppercase on the ODS code."""
        for vals in vals_list:
            if 'code' in vals and vals['code']:
                vals['code'] = vals['code'].upper()
        return super().create(vals_list)

    def write(self, vals):
        """Override write to enforce uppercase on the ODS code."""
        if 'code' in vals and vals['code']:
            vals['code'] = vals['code'].upper()
        return super().write(vals)

    def action_view_trusts(self):
        """Return an action to open the list of trusts under this LHB."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Trusts',
            'res_model': 'nhs.trust',
            'view_mode': 'list,form',
            'domain': [('welsh_lhb_id', '=', self.id)],
            'context': {'default_welsh_lhb_id': self.id, 'default_health_system': 'nhs_wales'},
        }


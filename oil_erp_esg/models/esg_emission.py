# -*- coding: utf-8 -*-
#############################################################################
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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EsgEmission(models.Model):
    """
    Records Greenhouse Gas (GHG) emissions across different scopes and sources.
    Calculates CO2 equivalent (CO2e) using Global Warming Potential (GWP) factors.
    """
    _name = 'oil.esg.emission'
    _description = 'GHG Emission Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference',
                       required=True,
                       copy=False,
                       default=lambda self: self.env[
                           'ir.sequence'].next_by_code('oil.esg.emission'),
                       help="Enter the reference."
                       )
    date = fields.Date(string='Date',
                       required=True,
                       default=fields.Date.today,
                       tracking=True,
                       help="Select the date for date.")
    site_id = fields.Many2one('oil.esg.site',
                              string='Site / Facility',
                              required=True,
                              tracking=True,
                              help="Select the site or Facility.")
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=lambda self: self.env.company,
                                 help="Select the company."
                                 )
    business_segment = fields.Selection(
        related='site_id.business_segment',
        string='Business Segment',
        store=True,
        readonly=True,
        help="The business segment of the associated site.")

    source = fields.Selection([
        ('combustion', 'Stationary Combustion'),
        ('flaring', 'Flaring'),
        ('venting', 'Venting'),
        ('fugitive', 'Fugitive Emissions'),
        ('transport', 'Mobile / Transport'),
        ('process', 'Process Emissions'),
        ('grid_power', 'Grid Electricity'),
        ('steam', 'Purchased Steam'),
        ('other', 'Other'),
    ], string='Emission Source', required=True, tracking=True,
        help="Choose the emission Source.")

    scope = fields.Selection([
        ('scope1', 'Scope 1 — Direct'),
        ('scope2', 'Scope 2 — Indirect Energy'),
        ('scope3', 'Scope 3 — Value Chain'),
    ], string='GHG Scope', required=True, tracking=True,
        help="Choose the gHG Scope.")

    gas_type = fields.Selection([
        ('co2', 'CO₂ — Carbon Dioxide'),
        ('ch4', 'CH₄ — Methane'),
        ('n2o', 'N₂O — Nitrous Oxide'),
        ('hfc', 'HFCs — Hydrofluorocarbons'),
        ('pfc', 'PFCs — Perfluorocarbons'),
        ('sf6', 'SF₆ — Sulphur Hexafluoride'),
        ('nf3', 'NF₃ — Nitrogen Trifluoride'),
        ('mixed', 'Mixed GHG'),
    ], string='GHG Type', required=True, default='co2',
        help="Choose the gHG Type.")

    quantity = fields.Float(string='Quantity (tonnes)',
                            required=True,
                            digits=(16, 4),
                            help="Enter the quantity (tonnes).")
    gwp_factor = fields.Float(string='GWP Factor',
                              default=1.0,
                              help='Global Warming Potential factor to convert to CO2e')
    quantity_co2e = fields.Float(string='tCO₂e',
                                 compute='_compute_co2e',
                                 store=True,
                                 digits=(16, 4),
                                 help="Enter the tCO₂e.")

    activity_data = fields.Float(string='Activity Data',
                                 digits=(16, 4),
                                 help='Raw activity data (e.g. fuel consumed in litres)')
    activity_unit = fields.Selection([
        ('litres', 'Litres'),
        ('m3', 'm³'),
        ('kwh', 'kWh'),
        ('gj', 'GJ'),
        ('tonnes', 'Tonnes'),
        ('boe', 'BOE'),
        ('nm3', 'Nm³'),
    ], string='Activity Unit',
        help="Choose the activity Unit.")

    emission_factor = fields.Float(string='Emission Factor', digits=(16, 6),
                                   help="Enter the emission Factor.")
    emission_factor_unit = fields.Char(string='EF Unit',
                                       help='e.g. kgCO2e/litre')

    period_month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'),
        ('04', 'April'), ('05', 'May'), ('06', 'June'),
        ('07', 'July'), ('08', 'August'), ('09', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string='Month', compute='_compute_period', store=True,
        help="Choose the month.")
    period_year = fields.Char(string='Year', compute='_compute_period',
                              store=True, help="Enter the year.")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('verified', 'Verified'),
        ('flagged', 'Flagged'),
    ], string='Status', default='draft', tracking=True,
        help="Choose the status.")

    verified_by = fields.Many2one('res.users', string='Verified By',
                                  help="Select the verified By.")
    verified_date = fields.Date(string='Verified On',
                                help="Select the date for verified On.")
    notes = fields.Text(string='Notes / Remarks',
                        help="Enter the notes or Remarks.")
    attachment_ids = fields.Many2many('ir.attachment',
                                      string='Supporting Documents',
                                      help="Lists the supporting Documents.")

    @api.depends('quantity', 'gwp_factor')
    def _compute_co2e(self):
        """
        Calculates the CO2 equivalent weight by multiplying quantity by the GWP factor.
        """
        for rec in self:
            rec.quantity_co2e = rec.quantity * rec.gwp_factor

    @api.depends('date')
    def _compute_period(self):
        """
        Extracts the month and year from the emission record date for reporting.
        """
        for rec in self:
            if rec.date:
                rec.period_month = rec.date.strftime('%m')
                rec.period_year = rec.date.strftime('%Y')
            else:
                rec.period_month = False
                rec.period_year = False

    @api.constrains('quantity')
    def _check_quantity(self):
        """
        Ensures that the emission quantity recorded is not a negative value.
        """
        for rec in self:
            if rec.quantity < 0:
                raise ValidationError('Emission quantity cannot be negative.')

    def action_submit(self):
        """
        Submits the emission record for internal verification.
        """
        self.write({'state': 'submitted'})

    def action_verify(self):
        """
        Verifies the emission data and records the verifier and verification date.
        """
        self.write({
            'state': 'verified',
            'verified_by': self.env.uid,
            'verified_date': fields.Date.today(),
        })

    def action_flag(self):
        """
        Flags the record for review if anomalies or errors are suspected.
        """
        self.write({'state': 'flagged'})

    def action_reset_draft(self):
        """
        Resets the record status to 'Draft' for editing.
        """
        self.write({'state': 'draft'})

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


class EsgEnergy(models.Model):
    """
    Maintains records of energy consumption and production at field sites.
    Tracks renewable vs non-renewable usage and calculates energy intensity per BOE.
    """
    _name = 'oil.esg.energy'
    _description = 'Energy Consumption Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                       default=lambda self: self.env[
                           'ir.sequence'].next_by_code('oil.esg.energy'),
                       help="Enter the reference.")
    date = fields.Date(string='Date', required=True, default=fields.Date.today,
                       tracking=True, help="Select the date for date.")
    site_id = fields.Many2one('oil.esg.site', string='Site / Facility',
                              required=True, tracking=True,
                              help="Select the site or Facility.")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 help="Select the company id.")
    business_segment = fields.Selection(
        related='site_id.business_segment',
        string='Business Segment',
        store=True,
        readonly=True,
        help="The business segment of the associated site.")

    energy_source = fields.Selection([
        ('natural_gas', 'Natural Gas'),
        ('diesel', 'Diesel / HFO'),
        ('petrol', 'Petrol / Gasoline'),
        ('lpg', 'LPG'),
        ('coal', 'Coal'),
        ('grid_elec', 'Grid Electricity'),
        ('solar', 'Solar PV'),
        ('wind', 'Wind'),
        ('hydro', 'Hydropower'),
        ('biomass', 'Biomass'),
        ('steam', 'Purchased Steam'),
        ('other', 'Other'),
    ], string='Energy Source', required=True, tracking=True,
        help="Choose the energy Source.")

    is_renewable = fields.Boolean(string='Renewable?',
                                  compute='_compute_renewable', store=True,
                                  help="Enable this when renewable? applies.")

    energy_type = fields.Selection([
        ('consumed', 'Energy Consumed'),
        ('produced', 'Energy Produced'),
        ('sold', 'Energy Sold'),
    ], string='Type', default='consumed', required=True,
        help="Choose the type.")

    quantity_gj = fields.Float(string='Energy (GJ)', required=True,
                               digits=(16, 4), help="Enter the energy (GJ).")
    quantity_kwh = fields.Float(string='Energy (kWh)', compute='_compute_kwh',
                                store=True, digits=(16, 4),
                                help="Enter the energy (kWh).")

    production_boe = fields.Float(string='Production (BOE)', digits=(16, 4),
                                  help='Associated production volume for intensity calculation')
    energy_intensity = fields.Float(string='Intensity (GJ/BOE)',
                                    compute='_compute_intensity',
                                    store=True, digits=(16, 6),
                                    help="Enter the intensity (GJ/BOE).")

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
        ('logged', 'Logged'),
        ('verified', 'Verified'),
    ], string='Status', default='draft', tracking=True,
        help="Choose the status.")

    notes = fields.Text(string='Notes', help="Enter the notes.")

    RENEWABLE_SOURCES = {'solar', 'wind', 'hydro', 'biomass'}

    @api.depends('energy_source')
    def _compute_renewable(self):
        """
        Determines if the selected energy source is categorized as renewable.
        """
        for rec in self:
            rec.is_renewable = rec.energy_source in self.RENEWABLE_SOURCES

    @api.depends('quantity_gj')
    def _compute_kwh(self):
        """
        Converts the energy quantity from Gigajoules (GJ) to Kilowatt-hours (kWh).
        """
        for rec in self:
            rec.quantity_kwh = rec.quantity_gj * 277.778

    @api.depends('quantity_gj', 'production_boe')
    def _compute_intensity(self):
        """
        Calculates energy intensity as the ratio of energy consumed (GJ) to production (BOE).
        """
        for rec in self:
            if rec.production_boe:
                rec.energy_intensity = rec.quantity_gj / rec.production_boe
            else:
                rec.energy_intensity = 0.0

    @api.depends('date')
    def _compute_period(self):
        """
        Automatically sets the reporting month and year based on the record date.
        """
        for rec in self:
            if rec.date:
                rec.period_month = rec.date.strftime('%m')
                rec.period_year = rec.date.strftime('%Y')
            else:
                rec.period_month = False
                rec.period_year = False

    def action_log(self):
        """
        Moves the energy record to the 'Logged' state.
        """
        self.write({'state': 'logged'})

    def action_verify(self):
        """
        Marks the energy data as 'Verified'.
        """
        self.write({'state': 'verified'})

    def action_reset_draft(self):
        """
        Resets the energy record to 'Draft' status.
        """
        self.write({'state': 'draft'})

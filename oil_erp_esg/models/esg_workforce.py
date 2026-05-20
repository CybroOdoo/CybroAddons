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
from odoo.tools.translate import _


class EsgWorkforceSocial(models.Model):
    """
    Tracks workforce demographics, training, and community engagement KPIs.
    Calculates diversity ratios, training metrics, and grievance resolution rates.
    """
    _name = 'oil.esg.workforce'
    _description = 'Workforce & Social KPI Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc, date_to desc'

    name = fields.Char(string='Period Label', compute='_compute_period_fields',
                       store=True, readonly=True,
                       help="Auto-generated period label.")
    date_from = fields.Date(string='From Date', required=True,
                            tracking=True,
                            help="Start date of the reporting period.")
    date_to = fields.Date(string='To Date', required=True,
                          tracking=True,
                          help="End date of the reporting period.")
    period_month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'),
        ('04', 'April'), ('05', 'May'), ('06', 'June'),
        ('07', 'July'), ('08', 'August'), ('09', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string='Month', compute='_compute_period_fields', store=True, readonly=True,
        help="Derived from the reporting start date.")
    period_year = fields.Char(string='Year', compute='_compute_period_fields',
                              store=True, readonly=True,
                              help="Derived from the reporting start date.")
    site_id = fields.Many2one('oil.esg.site', string='Site / Facility',
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

    # Headcount
    total_employees = fields.Integer(string='Total Employees',
                                     help="Enter the total Employees.")
    local_employees = fields.Integer(string='Local Hires',
                                     help="Enter the local Hires.")
    contractor_count = fields.Integer(string='Contractors',
                                      help="Enter the contractors.")
    nationalities = fields.Integer(string='Nationalities Represented',
                                   help="Enter the nationalities Represented.")

    # Computed diversity metrics
    local_hire_ratio = fields.Float(string='Local Hire %',
                                    compute='_compute_diversity', store=True,
                                    help="Enter the local Hire %.")
    pay_gap_pct = fields.Float(string='Pay Gap %', digits=(5, 2),
                               help="Enter the pay Gap %.")

    # Training
    training_hours = fields.Float(string='Training Hours (Total)',
                                  help="Enter the training Hours (Total).")
    safety_training_hours = fields.Float(string='Safety Training Hours',
                                         help="Enter the safety Training Hours.")
    training_hrs_per_employee = fields.Float(string='Hrs/Employee',
                                             compute='_compute_training',
                                             store=True,
                                             help="Enter the hrs/Employee.")

    # Community
    community_investment = fields.Float(string='Community Investment ($)',
                                        help="Enter the community Investment ($).")
    beneficiaries = fields.Integer(string='Community Beneficiaries',
                                   help="Enter the community Beneficiaries.")
    grievances_total = fields.Integer(string='Total Grievances',
                                      help="Enter the total Grievances.")
    grievances_resolved = fields.Integer(string='Grievances Resolved',
                                         help="Enter the grievances Resolved.")
    grievance_resolution_rate = fields.Float(string='Resolution Rate %',
                                             compute='_compute_grievance',
                                             store=True,
                                             help="Enter the resolution Rate %.")

    notes = fields.Text(help="Enter the notes.")

    @api.depends('date_from', 'date_to')
    def _compute_period_fields(self):
        """
        Builds the reporting label and derived year/month values from the date range.
        """
        for rec in self:
            if rec.date_from:
                rec.period_year = rec.date_from.strftime('%Y')
                rec.period_month = rec.date_from.strftime('%m')
                if rec.date_to and rec.date_to != rec.date_from:
                    rec.name = _("%s to %s") % (
                        fields.Date.to_string(rec.date_from),
                        fields.Date.to_string(rec.date_to),
                    )
                else:
                    rec.name = fields.Date.to_string(rec.date_from)
            else:
                rec.period_year = False
                rec.period_month = False
                rec.name = False

    @api.constrains('date_from', 'date_to')
    def _check_period_range(self):
        """
        Ensures the reporting period end date is not earlier than the start date.
        """
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise ValidationError(
                    _("The To Date must be greater than or equal to the From Date.")
                )

    @api.depends('total_employees','local_employees')
    def _compute_diversity(self):
        """
        Calculates the percentage of local hires in the workforce.
        """
        for rec in self:
            rec.local_hire_ratio = (
                rec.local_employees / rec.total_employees * 100
                if rec.total_employees else 0.0)

    @api.depends('training_hours', 'total_employees')
    def _compute_training(self):
        """
        Calculates the average training hours per employee for the period.
        """
        for rec in self:
            rec.training_hrs_per_employee = (
                rec.training_hours / rec.total_employees
                if rec.total_employees else 0.0)

    @api.depends('grievances_total', 'grievances_resolved')
    def _compute_grievance(self):
        """
        Calculates the resolution rate for community grievances.
        """
        for rec in self:
            rec.grievance_resolution_rate = (
                rec.grievances_resolved / rec.grievances_total * 100
                if rec.grievances_total else 0.0)

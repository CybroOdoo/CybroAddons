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


class EsgWater(models.Model):
    """
    Tracks water usage, Produced Water management, and waste disposal.
    Also handles reporting for spills and other environmental discharge incidents.
    """
    _name = 'oil.esg.water'
    _description = 'Water & Waste Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False,
                       default=lambda self: self.env[
                           'ir.sequence'].next_by_code('oil.esg.water'),
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

    record_type = fields.Selection([
        ('water_withdrawal', 'Water Withdrawal'),
        ('water_discharge', 'Water Discharge'),
        ('water_recycled', 'Water Recycled / Reused'),
        ('produced_water', 'Produced Water'),
        ('spill', 'Spill / Discharge Incident'),
        ('waste_hazardous', 'Hazardous Waste'),
        ('waste_non_hazardous', 'Non-Hazardous Waste'),
    ], string='Record Type', required=True, tracking=True,
        help="Choose the record Type.")

    # Water fields
    volume_m3 = fields.Float(
        string='Volume (m³)',
        digits=(16, 4),
        help="Enter the volume (m³).")

    water_source = fields.Selection([
        ('surface', 'Surface Water'),
        ('groundwater', 'Groundwater'),
        ('seawater', 'Seawater'),
        ('municipal', 'Municipal / Treated'),
        ('produced', 'Produced Water'),
        ('rainwater', 'Rainwater'),
    ], string='Water Source',
        help="Choose the water Source.")

    is_recycled = fields.Boolean(string='Recycled/Reused?',
                                 help="Enable this when recycled/Reused? applies.")
    treatment_method = fields.Char(string='Treatment Method',
                                   help="Enter the treatment Method.")

    # Spill fields
    spill_medium = fields.Selection([
        ('soil', 'Soil / Land'),
        ('water', 'Water Body'),
        ('sea', 'Sea / Ocean'),
        ('air', 'Air'),
    ], string='Release Medium',
        help="Choose the release Medium."
    )
    spill_substance = fields.Char(string='Substance Released',
                                  help="Enter the substance Released.")
    is_contained = fields.Selection([
        ('yes', 'Fully Contained'),
        ('partial', 'Partially Contained'),
        ('no', 'Not Contained'),
    ], string='Contained?',
        help="Choose the contained?."
    )
    remediation_action = fields.Text(string='Remediation Action',
                                     help="Enter the remediation Action.")

    # Waste fields
    waste_type = fields.Char(string='Waste Type / Category',
                             help="Enter the waste Type or Category.")
    disposal_method = fields.Selection([
        ('recycled', 'Recycled'),
        ('recovered', 'Energy Recovery'),
        ('landfill', 'Landfill'),
        ('incineration', 'Incineration'),
        ('treatment', 'Treatment'),
        ('injection', 'Deep Well Injection'),
        ('other', 'Other'),
    ], string='Disposal Method',
        help="Choose the disposal Method."
    )
    quantity_tonnes = fields.Float(string='Quantity (tonnes)', digits=(16, 4),
                                   help="Enter the quantity (tonnes).")

    period_month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'),
        ('04', 'April'), ('05', 'May'), ('06', 'June'),
        ('07', 'July'), ('08', 'August'), ('09', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string='Month', compute='_compute_period', store=True,
        help="Choose the month."
    )
    period_year = fields.Char(string='Year', compute='_compute_period',
                              store=True, help="Enter the year.")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open / Investigating'),
        ('closed', 'Closed'),
        ('flagged', 'Flagged'),
    ], string='Status', default='draft', tracking=True,
        help="Choose the status.")

    responsible_id = fields.Many2one('res.users', string='Responsible Person',
                                     help="Select the responsible Person.")
    notes = fields.Text(string='Notes / Remarks',
                        help="Enter the notes or Remarks.")
    attachment_ids = fields.Many2many('ir.attachment',
                                      string='Supporting Documents',
                                      help="Lists the supporting Documents.")

    @api.depends('date')
    def _compute_period(self):
        """
        Sets the reporting month and year based on the record date.
        """
        for rec in self:
            if rec.date:
                rec.period_month = rec.date.strftime('%m')
                rec.period_year = rec.date.strftime('%Y')
            else:
                rec.period_month = False
                rec.period_year = False

    def action_open(self):
        """
        Moves the record to 'Open' status, typically for spill investigations.
        """
        self.write({'state': 'open'})

    def action_close(self):
        """
        Closes the water or waste record.
        """
        self.write({'state': 'closed'})

    def action_flag(self):
        """
        Flags the entry for data verification or follow-up.
        """
        self.write({'state': 'flagged'})

    def action_reset_draft(self):
        """
        Resets the record to 'Draft' status.
        """
        self.write({'state': 'draft'})

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


class EsgInitiative(models.Model):
    """
    Manages long-term ESG initiatives and decarbonisation projects.
    Tracks progress, budget utilization, and KPI improvements against baselines.
    """
    _name = 'oil.esg.initiative'
    _description = 'ESG Initiative & Decarbonisation Target'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'state, name'

    name = fields.Char(string='Initiative Name', required=True, tracking=True,
                       help="Enter the initiative Name.")
    description = fields.Text(string='Description',
                              help="Enter the description.")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 help="Select the company id.")

    category = fields.Selection([
        ('environment', 'Environment'),
        ('energy', 'Energy'),
        ('emissions', 'Emissions / Decarbonisation'),
        ('water', 'Water'),
        ('waste', 'Waste'),
        ('biodiversity', 'Biodiversity'),
        ('social', 'Social'),
        ('safety', 'Safety'),
        ('governance', 'Governance'),
        ('community', 'Community'),
    ], string='ESG Category', required=True, tracking=True,
        help="Choose the eSG Category.")

    pillar = fields.Selection([
        ('E', 'Environmental'),
        ('S', 'Social'),
        ('G', 'Governance'),
    ], string='ESG Pillar', required=True, tracking=True,
        help="Choose the eSG Pillar.")

    segment = fields.Selection([
        ('upstream', 'Upstream'),
        ('midstream', 'Midstream'),
        ('downstream', 'Downstream'),
        ('corporate', 'Corporate'),
        ('all', 'All Segments'),
    ], string='Business Segment', default='all',
        help="Choose the business Segment.")

    owner_id = fields.Many2one('res.users', string='Initiative Owner',
                               tracking=True,
                               help="Select the initiative Owner.")
    site_ids = fields.Many2many('oil.esg.site', string='Applicable Sites',
                                help="Lists the applicable Sites.")

    start_date = fields.Date(string='Start Date',
                             help="Select the date for start Date.")
    target_date = fields.Date(string='Target / Due Date', tracking=True,
                              help="Select the date for target or Due Date.")
    completion_date = fields.Date(string='Actual Completion',
                                  help="Select the date for actual Completion.")

    progress = fields.Float(string='Progress (%)', default=0.0, digits=(5, 2),
                            tracking=True, help="Enter the progress (%).")
    budget = fields.Float(string='Budget ($)', help="Enter the budget ($).")
    actual_spend = fields.Float(string='Actual Spend ($)',
                                help="Enter the actual Spend ($).")

    kpi_baseline = fields.Float(string='Baseline Value',
                                help="Enter the baseline Value.")
    kpi_target = fields.Float(string='Target Value',
                              help="Enter the target Value.")
    kpi_current = fields.Float(string='Current Value',
                               help="Enter the current Value.")
    kpi_unit = fields.Char(string='KPI Unit', help='e.g. tCO2e, GJ, m³')

    state = fields.Selection([
        ('idea', 'Idea'),
        ('approved', 'Approved'),
        ('inprogress', 'In Progress'),
        ('onhold', 'On Hold'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='idea', tracking=True,
        help="Choose the status.")

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
        ('2', 'Very Important'),
        ('3', 'Critical'),
    ], string='Priority', default='0',
        help="Choose the priority.")

    milestone_ids = fields.One2many('oil.esg.initiative.milestone',
                                    'initiative_id', string='Milestones',
                                    help="Lists the milestones.")
    notes = fields.Text(string='Notes', help="Enter the notes.")
    attachment_ids = fields.Many2many('ir.attachment', string='Documents',
                                      help="Lists the documents.")

    # Computed
    budget_used_pct = fields.Float(string='Budget Used %',
                                   compute='_compute_budget_pct', store=True,
                                   help="Enter the budget Used %.")
    milestone_count = fields.Integer(compute='_compute_milestone_count',
                                     help="Enter the milestone count.")
    milestone_done_count = fields.Integer(compute='_compute_milestone_count',
                                          help="Enter the milestone done count.")

    @api.depends('budget', 'actual_spend')
    def _compute_budget_pct(self):
        """
        Calculates the percentage of the budget that has been spent.
        """
        for rec in self:
            rec.budget_used_pct = (
                rec.actual_spend / rec.budget * 100 if rec.budget else 0.0)

    @api.depends('milestone_ids', 'milestone_ids.done')
    def _compute_milestone_count(self):
        """
        Counts total milestones and those already completed for the initiative.
        """
        for rec in self:
            rec.milestone_count = len(rec.milestone_ids)
            rec.milestone_done_count = len(rec.milestone_ids.filtered('done'))

    def action_approve(self):
        """
        Sets the initiative state to 'Approved' for execution.
        """
        self.write({'state': 'approved'})

    def action_start(self):
        """
        Sets the initiative state to 'In Progress'.
        """
        self.write({'state': 'inprogress'})

    def action_hold(self):
        """
        Temporarily pauses the initiative.
        """
        self.write({'state': 'onhold'})

    def action_done(self):
        """
        Marks the initiative as successfully completed and sets progress to 100%.
        """
        self.write({'state': 'done', 'progress': 100.0,
                    'completion_date': fields.Date.today()})

    def action_cancel(self):
        """
        Cancels the initiative.
        """
        self.write({'state': 'cancelled'})

    def action_reset(self):
        """
        Resets the initiative back to 'Idea' stage.
        """
        self.write({'state': 'idea'})


class EsgInitiativeMilestone(models.Model):
    """
    Represents a specific target or milestone within an ESG initiative.
    """
    _name = 'oil.esg.initiative.milestone'
    _description = 'ESG Initiative Milestone'
    _order = 'due_date'

    initiative_id = fields.Many2one('oil.esg.initiative', string='Initiative',
                                    required=True, ondelete='cascade',
                                    help="Select the initiative.")
    name = fields.Char(string='Milestone', required=True,
                       help="Enter the milestone.")
    due_date = fields.Date(string='Due Date',
                           help="Select the date for due Date.")
    done = fields.Boolean(string='Completed?',
                          help="Enable this when completed? applies.")
    completion_date = fields.Date(string='Completed On',
                                  help="Select the date for completed On.")
    notes = fields.Char(string='Notes', help="Enter the notes.")

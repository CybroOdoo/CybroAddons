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


class NhsTrustOperations(models.Model):
    """Extends nhs.trust with operational fields: sites, CQC, financials, workforce."""
    _inherit = 'nhs.trust'

    # ── CQC (England only)
    cqc_provider_id = fields.Char(
        string='CQC Provider ID',
        help="Care Quality Commission registered provider ID (e.g. '1-101677898')."
             " England only — hidden for Scotland."
    )
    cqc_registration_status = fields.Selection([
        ('pending', 'Pending Registration'),
        ('registered', 'Registered'),
        ('conditions', 'Registered with Conditions'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
        ('not_applicable', 'Not Applicable'),
    ],
        string='CQC Registration Status',
        compute='_compute_latest_cqc',
        store=True,
        tracking=True,
        help="CQC Registration status computed from the latest inspection record (or 'not_applicable' for Scotland)."
    )
    latest_cqc_status = fields.Selection([
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('active', 'Active'),
    ],
        string='Latest CQC Inspection Status',
        compute='_compute_latest_cqc',
        store=True,
        tracking=True,
        help="The workflow state of the latest CQC inspection."
    )


    # ── Sites & Departments
    site_ids = fields.One2many(
        'nhs.trust.site',
        'trust_id',
        string='Sites',
        help="All sites belonging to the trust (hospitals, clinics, ambulance stations, "
             "admin buildings). Populated when Sites are created."
    )
    site_count = fields.Integer(
        string='Site Count',
        compute='_compute_site_count',
        help="Count for stat button."
    )
    department_count = fields.Integer(
        string='Department Count',
        compute='_compute_ops_department_count',
        help="Sum of departments across all sites. Computed via site_ids.department_ids."
    )

    # ── Workforce
    total_workforce = fields.Integer(
        string='Total Workforce (FTE)',
        help="Total full-time-equivalent staff. Manually maintained — should match the latest NHS workforce statistics return."
    )

    # ── Bed Capacity
    total_bed_capacity = fields.Integer(
        string='Total Bed Capacity',
        compute='_compute_total_bed_capacity',
        store=True,
        help="Total available beds across all sites. Computed as SUM(site_ids.bed_capacity)."
             " If manual_bed_capacity is set, that value overrides the computed sum."
    )
    manual_bed_capacity = fields.Integer(
        string='Manual Bed Capacity Override',
        default=0,
        help="Override value for total_bed_capacity. Leave at 0 to use the computed sum from sites."
    )

    # ── Financials
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.ref('base.GBP', raise_if_not_found=False),
        required=True,
        help="Defaults to GBP. Required for the Monetary fields. Hidden by default since UK NHS is always GBP."
    )
    annual_budget = fields.Monetary(
        string='Annual Budget',
        currency_field='currency_id',
        tracking=True,
        help="Total operating budget for the financial year. Tracked on chatter so budget changes are auditable."
    )
    annual_income = fields.Monetary(
        string='Annual Income',
        currency_field='currency_id',
        help="Actual / forecast income for the year. Includes NHS commissioning income, "
             "private patient income, other operating income."
    )
    annual_expenditure = fields.Monetary(
        string='Annual Expenditure',
        currency_field='currency_id',
        help="Actual / forecast operating expenditure."
    )
    surplus_deficit = fields.Monetary(
        string='Surplus / Deficit',
        currency_field='currency_id',
        compute='_compute_surplus_deficit',
        store=True,
        help="Auto-computed as annual_income − annual_expenditure. Positive = surplus (green), negative = deficit (red)."
    )
    capital_allocation = fields.Monetary(
        string='Capital Allocation (CDEL)',
        currency_field='currency_id',
        help="Capital Departmental Expenditure Limit allocation for the year. Used for estates / equipment investment."
    )
    pfi_obligations = fields.Monetary(
        string='PFI Obligations',
        currency_field='currency_id',
        help="Outstanding Private Finance Initiative obligations. PFI is a procurement"
             " model where a private consortium funds and operates NHS estate "
             "and the Trust pays a unitary charge for 25–30 years."
    )
    financial_year = fields.Char(
        string='Financial Year',
        help="Free-text label for the FY (e.g. '2025/26'). Defaulted on create."
    )

    # ── CQC Inspection History ──────────────────────────────────────────────
    cqc_inspection_ids = fields.One2many(
        'nhs.trust.cqc.inspection',
        'trust_id',
        string='CQC Inspections',
        help="Full CQC inspection history. England only."
    )
    latest_cqc_rating = fields.Selection([
        ('outstanding', 'Outstanding'),
        ('good', 'Good'),
        ('requires_improvement', 'Requires Improvement'),
        ('inadequate', 'Inadequate'),
        ('not_rated', 'Not Rated'),
    ],
        string='Latest CQC Rating',
        compute='_compute_latest_cqc',
        store=True,
        tracking=True,
        help="Overall rating of the most recent inspection (by inspection_date). Stored for filtering & grouping."
    )
    latest_cqc_date = fields.Date(
        string='Latest CQC Date',
        compute='_compute_latest_cqc',
        store=True,
        help="Date of the most recent CQC inspection. Used in dashboards and the directory export."
    )

    # ── Computes ────────────────────────────────────────────────────────────

    @api.depends('site_ids')
    def _compute_site_count(self):
        for trust in self:
            trust.site_count = len(trust.site_ids)

    @api.depends('site_ids.department_ids')
    def _compute_ops_department_count(self):
        for trust in self:
            trust.department_count = sum(len(s.department_ids) for s in trust.site_ids)

    @api.depends('site_ids.bed_capacity', 'manual_bed_capacity')
    def _compute_total_bed_capacity(self):
        for trust in self:
            if trust.manual_bed_capacity:
                trust.total_bed_capacity = trust.manual_bed_capacity
            else:
                trust.total_bed_capacity = sum(trust.site_ids.mapped('bed_capacity'))

    @api.depends('annual_income', 'annual_expenditure')
    def _compute_surplus_deficit(self):
        for trust in self:
            trust.surplus_deficit = (trust.annual_income or 0.0) - (trust.annual_expenditure or 0.0)

    @api.depends('cqc_inspection_ids.overall_rating', 'cqc_inspection_ids.inspection_date', 'cqc_inspection_ids.cqc_registration_status', 'cqc_inspection_ids.state', 'health_system')
    def _compute_latest_cqc(self):
        for trust in self:
            if trust.health_system == 'nhs_scotland':
                trust.latest_cqc_rating = False
                trust.latest_cqc_date = False
                trust.cqc_registration_status = 'not_applicable'
                trust.latest_cqc_status = False
                continue
            inspections = trust.cqc_inspection_ids.filtered('inspection_date').sorted(
                key=lambda r: r.inspection_date, reverse=True
            )
            if inspections:
                trust.latest_cqc_status = inspections[0].state
                trust.cqc_registration_status = inspections[0].cqc_registration_status
                active_inspections = inspections.filtered(lambda r: r.state == 'active')
                if active_inspections:
                    trust.latest_cqc_rating = active_inspections[0].overall_rating
                    trust.latest_cqc_date = active_inspections[0].inspection_date
                else:
                    trust.latest_cqc_rating = False
                    trust.latest_cqc_date = False
            else:
                trust.latest_cqc_rating = False
                trust.latest_cqc_date = False
                trust.cqc_registration_status = 'pending'
                trust.latest_cqc_status = False


    # ── Action Methods ──────────────────────────────────────────────────────

    def action_view_sites(self):
        self.ensure_one()
        return {
            'name': 'Sites',
            'type': 'ir.actions.act_window',
            'res_model': 'nhs.trust.site',
            'view_mode': 'list,form',
            'domain': [('trust_id', '=', self.id)],
            'context': {'default_trust_id': self.id},
        }

    def action_view_departments(self):
        self.ensure_one()
        return {
            'name': 'Departments',
            'type': 'ir.actions.act_window',
            'res_model': 'nhs.trust.department',
            'view_mode': 'list,form',
            'domain': [('trust_id', '=', self.id)],
            'context': {'default_trust_id': self.id},
        }

    def action_view_cqc_inspections(self):
        self.ensure_one()
        return {
            'name': 'CQC Inspections',
            'type': 'ir.actions.act_window',
            'res_model': 'nhs.trust.cqc.inspection',
            'view_mode': 'list,form',
            'domain': [('trust_id', '=', self.id)],
            'context': {'default_trust_id': self.id},
        }

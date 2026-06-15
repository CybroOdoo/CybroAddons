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

RATING_SELECTION = [
    ('outstanding', 'Outstanding'),
    ('good', 'Good'),
    ('requires_improvement', 'Requires Improvement'),
    ('inadequate', 'Inadequate'),
    ('not_rated', 'Not Rated'),
]


class NhsTrustCqcInspection(models.Model):
    _name = 'nhs.trust.cqc.inspection'
    _description = 'CQC Inspection Record'
    _inherit = ['mail.thread']
    _order = 'inspection_date desc'
    _rec_name = 'display_name'

    trust_id = fields.Many2one(
        'nhs.trust',
        string='Trust',
        required=True,
        ondelete='cascade',
        index=True,
        domain="[('health_system', '=', 'nhs_england')]",
        help="Parent trust. ondelete='cascade'."
    )
    inspection_date = fields.Date(
        string='Inspection Date',
        required=True,
        help="Date the inspection took place (or the report was published — choose a convention and stick to it)."
    )
    inspection_type = fields.Selection([
        ('comprehensive', 'Comprehensive'),
        ('focused', 'Focused'),
        ('responsive', 'Responsive'),
        ('thematic', 'Thematic'),
        ('follow_up', 'Follow-Up'),
    ],
        string='Inspection Type',
        required=True,
        default='comprehensive',
        help="Comprehensive = full assessment across all KLOEs (typical 3–5 year cycle)."
             " Focused = targeted at specific concerns. Responsive = triggered by intelligence "
             "(whistleblowing, mortality alerts). Thematic = cross-provider review on a specific topic."
             " Follow-up = revisit after enforcement action."
    )
    inspector_lead = fields.Char(
        string='Lead Inspector',
        help="Lead inspector name from the CQC report. Free-text — not"
             " linked to res.partner because CQC inspectors are not Trust contacts."
    )

    # KLOE Ratings — defined once via RATING_SELECTION constant
    overall_rating = fields.Selection(
        RATING_SELECTION,
        string='Overall Rating',
        required=True,
        default='not_rated',
        tracking=True,
        help="The headline rating shown on CQC's public profile of the provider. Drives Trust.latest_cqc_rating."
    )
    safe_rating = fields.Selection(
        RATING_SELECTION,
        string='Safe',
        help="Safe KLOE: 'Are services safe?' — covers safeguarding, incident reporting, medicines, infection control."
    )
    effective_rating = fields.Selection(
        RATING_SELECTION,
        string='Effective',
        help="Effective KLOE: 'Are services effective?' — evidence-based care, outcomes,"
             " multidisciplinary working, consent."
    )
    caring_rating = fields.Selection(
        RATING_SELECTION,
        string='Caring',
        help="Caring KLOE: 'Are services caring?' — dignity, compassion, emotional support, "
             "involvement of patients & families."
    )
    responsive_rating = fields.Selection(
        RATING_SELECTION,
        string='Responsive',
        help="Responsive KLOE: 'Are services responsive to people's needs?' — access, waiting times,"
             " complaints, individual needs."
    )
    well_led_rating = fields.Selection(
        RATING_SELECTION,
        string='Well-Led',
        help="Well-Led KLOE: 'Are services well-led?' — leadership, governance, culture, "
             "learning & improvement. Often the bellwether KLOE."
    )

    report_url = fields.Char(
        string='CQC Report URL',
        help="URL to the published CQC report on cqc.org.uk. Rendered with url widget."
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
        required=True,
        default='registered',
        help="CQC Registration status resulting from this inspection."
    )
    cqc_provider_id = fields.Char(
        related='trust_id.cqc_provider_id',
        string='CQC Provider ID',
        readonly=True,
        help="CQC Provider ID of the selected Trust."
    )
    report_attachment_ids = fields.Many2many(
        'ir.attachment',
        'nhs_cqc_inspection_attachment_rel',
        'inspection_id',
        'attachment_id',
        string='Report Attachments',
        help="Local attachments (PDF report, action plan, board response). Many2many because the same "
             "report may be attached to multiple inspections during follow-up."
    )
    next_inspection_due = fields.Date(
        string='Next Inspection Due',
        help="Anticipated next inspection date — used in the calendar view for forward planning."
    )
    findings_summary = fields.Html(
        string='Findings Summary',
        help="Rich-text summary of findings — typically copy-pasted key sections from the CQC report executive summary."
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help="Auto-built label '<Trust short_name> - <inspection_date> - <rating>'."
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Archive flag."
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('active', 'Active'),
    ],
        string='Status',
        required=True,
        default='draft',
        tracking=True,
        help="Workflow state of this inspection record: Draft -> Under Review -> Active."
    )

    @api.depends('trust_id', 'trust_id.short_name', 'trust_id.name', 'inspection_date', 'overall_rating')
    def _compute_display_name(self):
        rating_map = dict(RATING_SELECTION)
        for rec in self:
            trust_name = rec.trust_id.short_name or rec.trust_id.name or ''
            date_str = str(rec.inspection_date) if rec.inspection_date else ''
            rating_label = rating_map.get(rec.overall_rating, '') if rec.overall_rating else ''
            rec.display_name = f"{trust_name} — {date_str} — {rating_label}"

    def action_submit(self):
        for rec in self:
            rec.state = 'under_review'

    def action_approve(self):
        for rec in self:
            rec.state = 'active'

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.constrains('inspection_date', 'next_inspection_due')
    def _check_dates(self):
        for rec in self:
            if rec.next_inspection_due and rec.inspection_date:
                if rec.next_inspection_due <= rec.inspection_date:
                    raise ValidationError(
                        'Next inspection due date must be after the inspection date.'
                    )

    @api.constrains('trust_id')
    def _check_trust_id(self):
        for rec in self:
            if rec.trust_id and rec.trust_id.health_system != 'nhs_england':
                raise ValidationError(
                    'CQC Inspections are only applicable for England Trusts. Scotland Trusts are not eligible.'
                )

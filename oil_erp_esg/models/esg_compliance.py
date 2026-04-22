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


class EsgCompliance(models.Model):
    """
    Manages ESG regulatory compliance frameworks and audit findings.
    Tracks compliance status against standards like GHG Protocol, TCFD, and ISO certificates.
    """
    _name = 'oil.esg.compliance'
    _description = 'ESG Regulatory Compliance & Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'deadline_date, name'

    name = fields.Char(string='Framework / Regulation', required=True,
                       tracking=True, help="Enter the framework or Regulation.")
    code = fields.Char(string='Code / Reference',
                       help="Enter the code or Reference.")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 help="Select the company id.")
    business_segment = fields.Selection([
        ('upstream', 'Upstream'),
        ('midstream', 'Midstream'),
        ('downstream', 'Downstream'),
        ('corporate', 'Corporate'),
        ('all', 'All Segments'),
    ], string='Business Segment', default='all',
        help="The business segment this compliance framework applies to.")

    framework_type = fields.Selection([
        ('ghg_protocol', 'GHG Protocol'),
        ('ipieca', 'IPIECA / API'),
        ('tcfd', 'TCFD'),
        ('eu_taxonomy', 'EU Taxonomy'),
        ('osha_psm', 'OSHA PSM'),
        ('iso_14001', 'ISO 14001'),
        ('iso_50001', 'ISO 50001'),
        ('iso_45001', 'ISO 45001'),
        ('sdg', 'UN SDGs'),
        ('gri', 'GRI Standards'),
        ('sasb', 'SASB'),
        ('local_reg', 'Local Regulation'),
        ('other', 'Other'),
    ], string='Framework Type', required=True,
        help="Choose the framework Type."
    )

    scope_description = fields.Char(string='Scope',
                                    help='e.g. Scope 1,2,3 / Oil & Gas Sector')
    auditor = fields.Char(string='Auditor / Certifier',
                          help="Enter the auditor or Certifier.")
    responsible_id = fields.Many2one('res.users', string='Internal Owner',
                                     tracking=True,
                                     help="Select the internal Owner.")

    status = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_review', 'In Review'),
        ('compliant', 'Compliant'),
        ('gap', 'Gap / Non-Conformance'),
        ('expired', 'Expired'),
    ], string='Compliance Status', default='not_started', tracking=True,
        help="Choose the compliance Status."
    )

    deadline_date = fields.Date(string='Next Deadline', tracking=True,
                                help="Select the date for next Deadline.")
    last_audit_date = fields.Date(string='Last Audit Date',
                                  help="Select the date for last Audit Date.")
    next_audit_date = fields.Date(string='Next Audit Date',
                                  help="Select the date for next Audit Date.")
    certificate_expiry = fields.Date(string='Certificate Expiry',
                                     help="Select the date for certificate Expiry.")

    findings_critical = fields.Integer(string='Critical Findings', default=0,
                                       help="Enter the critical Findings.")
    findings_major = fields.Integer(string='Major Findings', default=0,
                                    help="Enter the major Findings.")
    findings_minor = fields.Integer(string='Minor Findings', default=0,
                                    help="Enter the minor Findings.")
    findings_open = fields.Integer(string='Open Findings',
                                   compute='_compute_findings_open', store=True,
                                   help="Enter the open Findings.")

    description = fields.Text(string='Description / Requirements',
                              help="Enter the description or Requirements.")
    gap_description = fields.Text(string='Gap / Non-Conformance Description',
                                  help="Enter the gap or Non-Conformance Description.")
    action_plan = fields.Text(string='Action Plan',
                              help="Enter the action Plan.")
    notes = fields.Text(string='Notes', help="Enter the notes.")
    attachment_ids = fields.Many2many('ir.attachment',
                                      string='Documents / Certificates',
                                      help="Lists the documents or Certificates.")

    @api.depends('findings_critical', 'findings_major', 'findings_minor')
    def _compute_findings_open(self):
        """
        Calculates the total number of open audit findings (Critical + Major + Minor).
        """
        for rec in self:
            rec.findings_open = rec.findings_critical + rec.findings_major + rec.findings_minor

    def action_set_compliant(self):
        """
        Sets the compliance status to 'Compliant'.
        """
        self.write({'status': 'compliant'})

    def action_set_review(self):
        """
        Sets the compliance status to 'In Review' for internal or external audit.
        """
        self.write({'status': 'in_review'})

    def action_set_gap(self):
        """
        Sets the compliance status to 'Gap' to indicate non-conformance.
        """
        self.write({'status': 'gap'})

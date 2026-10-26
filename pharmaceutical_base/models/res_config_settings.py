# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """Configuration settings for the Pharmaceutical ERP module, allowing toggling of major features."""
    _inherit = 'res.config.settings'

    module_pharma_vendor_qualification = fields.Boolean(
        string='Enable Vendor Qualification',
        help='Manage Approved Vendor Lists (AVL), questionnaire portal, and PO enforcement.',
    )
    module_pharma_capa_deviation = fields.Boolean(
        string='Enable CAPA & Deviation Management',
        help='Manage CAPA and deviations linked with quality and manufacturing workflows.',
    )
    module_pharma_trend_monitoring = fields.Boolean(
        string='Enable Trend Monitoring (Out of Trend)',
        help='Flag results that pass their specification but fall outside the '
             'normal range QA approved for a watched parameter, with a trend chart.',
    )
    module_pharma_sop_training = fields.Boolean(
        string='Enable SOP & Training Management',
        help='Track SOP lifecycles, training records, and training-gated BMR step sign-offs.',
    )
    module_pharma_traceability_coa = fields.Boolean(
        string='Enable Traceability, CoA & Audit Trail',
        help='Enable Certificate of Analysis (CoA), batch genealogy, and audit trail.',
    )
    module_pharma_equipment_maintenance = fields.Boolean(
        string='Enable Equipment Qualification & Maintenance',
        help='GMP equipment register with qualification, calibration and '
             'cleaning, QA-verified maintenance, and equipment checks on '
             'manufacturing orders and QC results.',
    )
    module_pharma_retention_sample = fields.Boolean(
        string='Enable Retention Samples',
        help='Keep a reserve sample register for released batches: withdrawals, '
             'periodic examination and approved disposal.',
    )
    # GMP locations, stored per company on res.company.
    pharma_rejected_location_id = fields.Many2one(
        related='company_id.pharma_rejected_location_id',
        readonly=False,
        string='Rejected Location',
        help='Location where QC-rejected material is automatically moved.',
    )
    pharma_enforce_storage_class = fields.Boolean(
        related='company_id.pharma_enforce_storage_class',
        readonly=False,
        string='Enforce Storage Class',
        help='Restrict material transfers to locations matching their assigned Storage Class.',
    )
    # Qualification / passing scores, stored per company on res.company.
    pharma_vendor_approval_percentage = fields.Float(
        related='company_id.pharma_vendor_approval_percentage',
        readonly=False,
        string='Vendor Qualification Approval (%)',
        help='Minimum audit score (%) required for vendor approval.',
    )
    pharma_training_passing_score = fields.Float(
        related='company_id.pharma_training_passing_score',
        readonly=False,
        string='SOP Training Passing Score (%)',
        help='Minimum assessment score (%) required to pass SOP training.',
    )
    # Premium add-ons, always listed in Settings; the toggle installs them.
    module_pharma_device_capture = fields.Boolean(
        string='Device Capture',
        help='Installs the paid Device Capture add-on.',
    )

    def set_values(self):
        """Block an out-of-range score while its module toggle is enabled, then save."""
        if self.module_pharma_vendor_qualification and not 0 < self.pharma_vendor_approval_percentage <= 100:
            raise ValidationError(self.env._(
                'The Vendor Qualification Approval Percentage must be greater '
                'than zero and at most 100 when Vendor Qualification is enabled.'))
        if self.module_pharma_sop_training and not 0 < self.pharma_training_passing_score <= 100:
            raise ValidationError(self.env._(
                'The SOP Training Passing Score must be greater than zero '
                'and at most 100 when SOP & Training Management is enabled.'))
        return super().set_values()

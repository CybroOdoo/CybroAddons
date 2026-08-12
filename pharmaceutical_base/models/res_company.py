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

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class ResCompany(models.Model):
    """Adds the GMP rejected-material location configuration to the company."""
    _inherit = 'res.company'

    def _auto_init(self):
        """Ensure the pharma columns exist on res_company before any ORM query runs."""
        # button_install() reads res.company before the schema pass runs, so a
        # registry knowing these fields while the table lacks the columns fails
        # any install/upgrade with 'column ... does not exist'. Creating them
        # up-front breaks that chicken-and-egg. Keep every pharma column on
        # res_company listed here — a partial list leaves the same trap open.
        self.env.cr.execute("""
            ALTER TABLE res_company
            ADD COLUMN IF NOT EXISTS pharma_rejected_location_id INTEGER;
        """)
        return super()._auto_init()

    pharma_rejected_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Rejected Location',
        domain="[('usage', '=', 'internal')]",
        help='Location where QC-rejected material is automatically moved.',
    )

    pharma_enforce_storage_class = fields.Boolean(
        string='Enforce Storage Class',
        default=False,
        help='Restrict material transfers to locations matching their assigned Storage Class.',
    )

    pharma_vendor_approval_percentage = fields.Float(
        string='Vendor Qualification Approval (%)',
        default=70.0,
        help='Minimum audit score (%) required for vendor approval.',
    )
    pharma_training_passing_score = fields.Float(
        string='SOP Training Passing Score (%)',
        default=80.0,
        help='Minimum assessment score (%) required to pass SOP training.',
    )

    @api.constrains('pharma_rejected_location_id')
    def _check_pharma_locations(self):
        """Ensure the configured Rejected location is an internal location."""
        for company in self:
            location = company.pharma_rejected_location_id
            if location and location.usage != 'internal':
                raise ValidationError(_(
                    "The Rejected Location must be an internal location."))

    @api.constrains(
        'pharma_vendor_approval_percentage',
        'pharma_training_passing_score',
    )
    def _check_pharma_scores(self):
        """Keep the qualification and passing scores within 0-100, never zero."""
        for company in self:
            scores = [
                ('Vendor Qualification Approval Percentage',
                 company.pharma_vendor_approval_percentage),
                ('SOP Training Passing Score',
                 company.pharma_training_passing_score),
            ]
            for label, score in scores:
                if not 0 < score <= 100:
                    raise ValidationError(_(
                        "The %s must be greater than 0 and at most 100.", label))

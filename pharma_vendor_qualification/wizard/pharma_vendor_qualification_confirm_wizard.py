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
from odoo import fields, models


class PharmaVendorQualificationConfirmWizard(models.TransientModel):
    """Wizard confirmation dialog when audit score is below required score."""
    _name = 'pharma.vendor.qualification.confirm.wizard'
    _description = 'Vendor Qualification Confirmation Wizard'

    qualification_ids = fields.Many2many(
        comodel_name='pharma.vendor.qualification',
        relation='pharma_vq_confirm_wizard_rel',
        column1='wizard_id',
        column2='qualification_id',
        string='Vendor Qualifications',
        required=True,
        help='Qualifications whose audit score is below the pass mark.',
    )
    message = fields.Text(
        default=lambda self: self.env._('The audit score is below the pass mark. Mark the vendor as Not Qualified?'),
        readonly=True,
    )

    def action_confirm_disqualify(self):
        """Confirm disqualification and proceed to mark vendor as Not Qualified."""
        self.ensure_one()
        return self.qualification_ids.with_context(confirm_not_qualified=True).action_approve()

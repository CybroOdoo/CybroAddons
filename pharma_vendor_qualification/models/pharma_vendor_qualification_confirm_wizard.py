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


class PharmaVendorQualificationConfirmWizard(models.TransientModel):
    """Wizard confirmation dialog when audit score is below required score."""
    _name = 'pharma.vendor.qualification.confirm.wizard'
    _description = 'Vendor Qualification Confirmation Wizard'

    qualification_id = fields.Many2one(
        comodel_name='pharma.vendor.qualification',
        string='Vendor Qualification',
        required=True,
        ondelete='cascade',
    )

    message = fields.Text(
        string='Message',
        default='Audit score is below required score. Mark vendor as Not Qualified?',
        readonly=True,
    )

    def action_confirm_disqualify(self):
        """Confirm disqualification and proceed to mark vendor as Not Qualified."""
        self.ensure_one()
        return self.qualification_id.with_context(confirm_not_qualified=True).action_approve()

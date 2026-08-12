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


class PharmaBMRStep(models.Model):
    """Adds the SOP link and training-gated operator sign-off to a BMR step."""
    _inherit = 'pharma.bmr.step'

    sop_id = fields.Many2one(
        comodel_name='pharma.sop',
        string='Linked SOP',
        domain="[('status', '=', 'effective')]",
        ondelete='set null',
        help='If set, the operator must have current (passed) training for this SOP '
             'before signing off. Only Effective SOPs can be linked.',
    )

    def action_operator_sign(self):
        """Enforce SOP training clearance before the core operator sign-off."""
        for step in self:
            if step.sop_id and step.status == 'pending' and not step.operator_signed_on:
                step._check_sop_training(step.sop_id)
        return super().action_operator_sign()

    def _check_sop_training(self, sop):
        """Verify the user has passed, non-expired training for the given SOP."""
        self.env['pharma.training'].check_training_clearance(
            self.env.user.id,
            sop_ids=[sop.id],
        )

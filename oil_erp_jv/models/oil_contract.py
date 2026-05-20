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

from odoo import fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError


class OilContract(models.Model):
    """Extends oil.contract to link a JV Agreement."""
    _inherit = 'oil.contract'

    jv_agreement_id = fields.Many2one(
        'oil.jv.agreement',
        string='JV Agreement',
        domain="[('state', '=', 'active')]",
        help="Joint Operating Agreement associated with this contract.")

    def _compute_expiry_warning(self):
        """Extend to also warn when JV agreement is expired."""
        super()._compute_expiry_warning()
        for record in self:
            warnings = []
            if record.expiry_warning:
                warnings.append(record.expiry_warning)
            if (record.jv_agreement_id
                    and record.jv_agreement_id.state == 'expired'):
                warnings.append(
                    _("JV Agreement '%s' has expired.",
                      record.jv_agreement_id.name))
            record.expiry_warning = (
                '\n'.join(warnings) if warnings else False)

    def action_confirm(self):
        """Extend to check JV agreement is active before confirming."""
        self.ensure_one()
        if (self.jv_agreement_id
                and self.jv_agreement_id.state != 'active'):
            raise UserError(
                _("Cannot confirm: JV Agreement '%s' is not active.",
                  self.jv_agreement_id.name))
        return super().action_confirm()

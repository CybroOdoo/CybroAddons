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

from odoo import models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class PharmaBmrStep(models.Model):
    """Adds the deviation/CAPA gate to BMR step supervisor sign-off."""
    _inherit = 'pharma.bmr.step'

    def _check_open_deviations_capas(self):
        """Block supervisor sign-off while the batch has open deviations or CAPAs."""
        for step in self:
            open_deviations = self.env['pharma.deviation'].search([
                ('batch_id', '=', step.bmr_id.production_id.id),
                ('status', '!=', 'closed')
            ])
            if open_deviations:
                raise UserError(_('Cannot sign — there are open Deviations for this batch:\n%s') % ', '.join(open_deviations.mapped('name')))

            open_capas = self.env['pharma.capa'].search([
                ('deviation_id.batch_id', '=', step.bmr_id.production_id.id),
                ('status', '!=', 'closed')
            ])
            if open_capas:
                raise UserError(_('Cannot sign — there are open CAPAs for this batch:\n%s') % ', '.join(open_capas.mapped('name')))

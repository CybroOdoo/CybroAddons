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


class PharmaPremiumFeature(models.Model):
    """Lets the Preventive Action dialog start preventive CAPAs on their
    action plan when the add-on is not installed."""
    _inherit = 'pharma.premium.feature'

    def action_start_capa_with_action_plan(self):
        """Start the preventive CAPAs the dialog was opened for, on their
        action plan, as the Preventive Action add-on is not installed."""
        capas = self.env['pharma.capa'].browse(
            self.env.context.get('pharma_capa_start_ids') or []).exists()
        capas.with_context(pharma_preventive_acknowledged=True).action_start()
        return {'type': 'ir.actions.act_window_close'}

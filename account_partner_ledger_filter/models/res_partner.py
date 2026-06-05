# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import models


class ResPartner(models.Model):
    """Extends the res.partner model to add custom functionality."""
    _inherit = "res.partner"

    def get_wizard(self):
        """Get the wizard action to open the partner ledger report wizard.
        This method is used to obtain the wizard action that opens the
        partner ledger report wizard for the selected partner(s).
        Returns:The wizard action dictionary."""
        res = self.env["ir.actions.actions"].sudo()._for_xml_id(
            "base_accounting_kit.action_partner_leadger")
        res['context'] = {
            'create': True,
            'default_partner_ids': self._context['active_ids'],
        }
        return res

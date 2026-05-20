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
from typing import Any
from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError


class ProductionWizard(models.TransientModel):
    """Extend the production wizard to also create royalty lines."""

    _inherit = 'production.wizard'

    royalty_id = fields.Many2one(
        comodel_name='oil.royalty',
        string='Royalty',
        domain="[('state', '=', 'draft'), ('lease_id.state', '=', 'active')]",
        help='Select an existing draft royalty to append production lines to. '
             'Leave empty to skip royalty line creation.',
    )

    # ── onchange ──────────────────────────────────────────────────────────────

    @api.onchange('royalty_id')
    def _onchange_royalty_id(self) -> dict[str, dict[str, Any]] | None:
        """Warn the user if the chosen royalty's lease doesn't match the task's project."""
        if not self.royalty_id or not self.task_id:
            return
        # Optional soft-warning — surface it as a user-visible info message.
        project = self.task_id.project_id
        if project and hasattr(project, 'lease_id'):
            if project.lease_id and project.lease_id != self.royalty_id.lease_id:
                return {
                    'warning': {
                        'title': _('Lease Mismatch'),
                        'message': _(
                            "The selected royalty belongs to lease '%s', "
                            "but the well's project is linked to lease '%s'. "
                            "Proceed only if this is intentional.",
                            self.royalty_id.lease_id.display_name,
                            project.lease_id.display_name,
                        ),
                    }
                }

    # ── action ────────────────────────────────────────────────────────────────

    def action_confirm(self) -> dict:
        """
        Call the original action_confirm (creates stock.picking),
        then create oil.royalty.line records for every wizard line
        when a royalty has been selected.
        """
        # 1. Run the original stock-picking logic.
        result = super().action_confirm()

        # 2. Create royalty lines if a royalty was chosen.
        if self.royalty_id:
            self._create_royalty_lines()

        return result

    def _create_royalty_lines(self) -> None:
        """
        For each production wizard line, create an oil.royalty.line
        linked to self.royalty_id.
        """
        self.ensure_one()

        if self.royalty_id.state != 'draft':
            raise UserError(
                _("Royalty lines can only be added to a royalty in 'Draft' state. "
                  "The selected royalty '%s' is in state '%s'.",
                  self.royalty_id.name,
                  self.royalty_id.state)
            )

        if not self.line_ids:
            return

        RoyaltyLine = self.env['oil.royalty.line']
        period_date = self.production_date
        well_name = self.task_id.display_name or ''

        for wiz_line in self.line_ids:
            description = '[%s] %s' % (well_name, wiz_line.product_id.display_name)
            RoyaltyLine.create([{
                'royalty_id': self.royalty_id.id,
                'product_id': wiz_line.product_id.id,
                'description': description,
                'date': period_date,
                'production_volume': wiz_line.produced_qty,
                'unit_price': wiz_line.rate,
                # gross_revenue and royalty_amount are computed+stored
                # on oil.royalty.line; no need to set them here.
            }])

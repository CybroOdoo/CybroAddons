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


class MrpRoutingWorkcenter(models.Model):
    """Links a routing operation to the approved SOP describing how it runs."""
    _inherit = 'mrp.routing.workcenter'

    allowed_sop_ids = fields.Many2many(
        comodel_name='pharma.sop',
        compute='_compute_allowed_sop_ids',
        string='Allowed SOPs',
    )

    sop_id = fields.Many2one(
        comodel_name='pharma.sop',
        string='Linked SOP',
        required=True,
        domain="[('id', 'in', allowed_sop_ids)]",
        help='Approved SOP detailing how this routing operation must be executed. '
             'Filtered by Effective status and matching Work Center.',
    )

    @api.depends('workcenter_id')
    def _compute_allowed_sop_ids(self):
        """Computes effective, active SOPs strictly matching the selected Work Center (or unassigned SOPs if no Work Center)."""
        Sop = self.env['pharma.sop']
        for rec in self:
            if rec.workcenter_id:
                domain = [
                    ('status', '=', 'effective'),
                    ('active', '=', True),
                    ('workcenter_id', '=', rec.workcenter_id.id),
                ]
            else:
                domain = [
                    ('status', '=', 'effective'),
                    ('active', '=', True),
                    ('workcenter_id', '=', False),
                ]
            rec.allowed_sop_ids = Sop.search(domain)

    @api.onchange('workcenter_id')
    def _onchange_workcenter_id_clear_sop(self):
        """Recomputes allowed SOPs and clears sop_id if incompatible with the new Work Center."""
        self._compute_allowed_sop_ids()
        if self.sop_id and self.sop_id not in self.allowed_sop_ids:
            self.sop_id = False

    @api.onchange('sop_id')
    def _onchange_sop_id_set_workcenter(self):
        """Auto-sets workcenter_id if an SOP with an assigned Work Center is selected and workcenter_id is empty."""
        if self.sop_id and self.sop_id.workcenter_id and not self.workcenter_id:
            self.workcenter_id = self.sop_id.workcenter_id
            self._compute_allowed_sop_ids()

    @api.constrains('sop_id', 'workcenter_id')
    def _check_sop_workcenter(self):
        """Ensure linked SOP is Effective, active, and strictly matches the operation Work Center."""
        for rec in self:
            if rec.sop_id:
                if rec.sop_id.status != 'effective' or not rec.sop_id.active:
                    raise ValidationError(_(
                        "The selected SOP '%s' is not Effective or has been archived and cannot be used in manufacturing operations.",
                        rec.sop_id.display_name or rec.sop_id.name
                    ))
                if rec.workcenter_id and rec.sop_id.workcenter_id != rec.workcenter_id:
                    raise ValidationError(_(
                        "The selected SOP '%(sop)s' belongs to Work Center '%(sop_wc)s', "
                        "which does not match the operation Work Center '%(op_wc)s'.",
                        sop=rec.sop_id.display_name or rec.sop_id.name,
                        sop_wc=rec.sop_id.workcenter_id.display_name if rec.sop_id.workcenter_id else _("None"),
                        op_wc=rec.workcenter_id.display_name,
                    ))
                elif not rec.workcenter_id and rec.sop_id.workcenter_id:
                    raise ValidationError(_(
                        "The selected SOP '%(sop)s' is specific to Work Center '%(sop_wc)s'. "
                        "Please select Work Center '%(sop_wc)s' on the operation.",
                        sop=rec.sop_id.display_name or rec.sop_id.name,
                        sop_wc=rec.sop_id.workcenter_id.display_name,
                    ))


class MrpProduction(models.Model):
    """Backfills the operation SOP onto each generated BMR step."""
    _inherit = 'mrp.production'

    def action_create_bmr(self):
        """Executes the action_create_bmr operation."""
        res = super().action_create_bmr()
        for production in self:
            if not production.bom_id or not production.bom_id.operation_ids:
                continue
            bmr = production.bmr_ids[:1]
            if not bmr:
                continue
            for step in bmr.step_ids:
                operation = production.bom_id.operation_ids.filtered(
                    lambda op: op.sequence == step.sequence
                    and op.name == step.description
                )[:1]
                if operation and operation.sop_id:
                    step.sop_id = operation.sop_id.id
        return res

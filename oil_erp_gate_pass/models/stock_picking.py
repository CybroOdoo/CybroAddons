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

from odoo import api, fields, models
from odoo.tools.translate import _


class StockPicking(models.Model):
    """
    Extends 'stock.picking' to link transfers with gate passes and provide
    navigation between them.
    """
    _inherit = "stock.picking"

    gate_pass_ids = fields.One2many("oil.gate.pass", "picking_id",
                                    string="Gate Passes",
                                    help="Gate passes created from this stock transfer.")
    gate_pass_count = fields.Integer(string="Gate Pass Count",
                                     compute="_compute_gate_pass_count",
                                     help="Number of gate passes linked to this transfer.")

    @api.depends("gate_pass_ids")
    def _compute_gate_pass_count(self):
        """Calculates the number of gate passes associated with this picking."""
        for picking in self:
            picking.gate_pass_count = len(picking.gate_pass_ids)

    def action_open_create_gate_pass_wizard(self):
        """Opens a wizard to create a new gate pass for this picking."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Gate Pass"),
            "res_model": "oil.gate.pass.create.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_picking_id": self.id},
        }

    def action_view_gate_passes(self):
        """
        Returns an action to view the gate passes linked to this picking.
        If there is only one, it opens in form view; otherwise, it opens in list view.
        """
        self.ensure_one()
        action = self.env.ref("oil_erp_gate_pass.action_oil_gate_pass").read()[0]
        action["domain"] = [("picking_id", "=", self.id)]
        if len(self.gate_pass_ids) == 1:
            action.update({
                "view_mode": "form",
                "res_id": self.gate_pass_ids.id,
            })
        return action

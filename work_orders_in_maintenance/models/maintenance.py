# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3)
#    (https://www.gnu.org/licenses/lgpl-3.0-standalone.html).
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
################################################################################
from odoo import api, fields, models


class MaintenanceRequest(models.Model):
    """Extend 'maintenance.request' with work orders and material requests."""

    _inherit = "maintenance.request"

    material_request_id = fields.Many2one(
        "material.request",
        help="Material request linked to this maintenance request.",
    )
    material_request_ids = fields.One2many(
        "material.request",
        "maintenance_request_id",
        string="Material Requests",
        help="Material requests of this maintenance request.",
    )
    work_order_ids = fields.One2many(
        "maintenance.work",
        "maintenance_request_id",
        string="Work Order Records",
        help="Work orders of this maintenance request.",
    )
    is_material_request = fields.Boolean(
        copy=False,
        help="Flag indicating if a material request was created.",
    )
    is_create_work_order = fields.Boolean(
        string="Can Create Work Order",
        compute="_compute_create_order_request",
        help="Flag indicating if a work order can be created.",
    )
    is_material_work_order = fields.Boolean(
        string="Can Create Material Request",
        compute="_compute_create_order_request",
        help="Flag indicating if a material request can be created.",
    )
    work_order_count = fields.Integer(
        string="Work Orders",
        compute="_compute_work_order_count",
        help="Number of work orders linked to this maintenance request.",
    )
    material_request_count = fields.Integer(
        string="Material Requests Count",
        compute="_compute_material_request_count",
        help="Number of material requests linked to this maintenance request.",
    )

    @api.depends("stage_id", "material_request_ids.state")
    def _compute_create_order_request(self):
        """Decide which buttons are available from the stage and materials."""
        in_progress = self.env.ref("maintenance.stage_1", raise_if_not_found=False)
        closed = self.env["maintenance.stage"]
        for xml_id in ("maintenance.stage_3", "maintenance.stage_0"):
            closed |= self.env.ref(xml_id, raise_if_not_found=False) or closed
        for record in self:
            first_request = record.material_request_ids[:1]
            record.is_create_work_order = bool(
                first_request.is_product_received
                and record.stage_id not in closed
            )
            record.is_material_work_order = bool(
                in_progress and record.stage_id == in_progress
            )

    @api.depends("work_order_ids")
    def _compute_work_order_count(self):
        """Compute the number of work orders."""
        for record in self:
            record.work_order_count = len(record.work_order_ids)

    @api.depends("material_request_ids")
    def _compute_material_request_count(self):
        """Compute the number of material requests."""
        for record in self:
            record.material_request_count = len(record.material_request_ids)

    def _get_records_action(self, name, model, records):
        """Return an action listing the records, or opening a single one."""
        action = {
            "name": name,
            "type": "ir.actions.act_window",
            "res_model": model,
            "domain": [("maintenance_request_id", "=", self.id)],
        }
        if len(records) == 1:
            action.update({"view_mode": "form", "res_id": records.id})
        else:
            action["view_mode"] = "list,form"
        return action

    def action_view_work_orders(self):
        """Open the work orders linked to this maintenance request."""
        self.ensure_one()
        return self._get_records_action(
            self.env._("Work Orders"), "maintenance.work", self.work_order_ids
        )

    def action_view_material_requests(self):
        """Open the material requests linked to this maintenance request."""
        self.ensure_one()
        return self._get_records_action(
            self.env._("Material Requests"),
            "material.request",
            self.material_request_ids,
        )

    def action_main_create_work_order(self):
        """Move the request to 'In Progress' and open a new work order form."""
        self.ensure_one()
        stage = self.env.ref("maintenance.stage_1", raise_if_not_found=False)
        if stage:
            self.stage_id = stage
        return {
            "name": self.env._("Work Order"),
            "view_mode": "form",
            "res_model": "maintenance.work",
            "view_id": self.env.ref(
                "work_orders_in_maintenance.maintenance_work_order_wizard_view_form"
            ).id,
            "type": "ir.actions.act_window",
            "context": {
                "default_maintenance_request_id": self.id,
                "default_equipment_id": self.equipment_id.id,
            },
            "target": "new",
        }

    def action_create_material_request(self):
        """Open a new material request form for this maintenance request."""
        self.ensure_one()
        self.is_material_request = True
        return {
            "name": self.env._("Material Request"),
            "view_mode": "form",
            "res_model": "material.request",
            "view_id": self.env.ref(
                "work_orders_in_maintenance.material_request_wizard_view_form"
            ).id,
            "type": "ir.actions.act_window",
            "context": {
                "default_maintenance_request_id": self.id,
                "default_equipment_id": self.equipment_id.id,
            },
            "target": "new",
        }

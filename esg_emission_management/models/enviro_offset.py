# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from __future__ import annotations

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EnviroOffset(models.Model):
    _name = "enviro.offset"
    _description = "Enviro Offset Credit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "purchase_date desc, id desc"
    _check_company_auto = True

    name = fields.Char(required=True, tracking=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    provider = fields.Char(tracking=True)
    project_name = fields.Char(tracking=True)
    project_type = fields.Selection(
        selection=[
            ("reforestation", "Reforestation"),
            ("renewable", "Renewable Energy"),
            ("methane", "Methane Capture"),
            ("efficiency", "Efficiency"),
            ("other", "Other"),
        ],
        default="other",
        required=True,
        tracking=True,
    )
    vintage_year = fields.Integer()
    certificate_number = fields.Char(copy=False, tracking=True)
    purchase_date = fields.Date(default=fields.Date.context_today, tracking=True)
    tonnes = fields.Float(string="Credits tCO2e", required=True, tracking=True)
    retired_tonnes = fields.Float(string="Retired tCO2e", tracking=True)
    available_tonnes = fields.Float(compute="_compute_available_tonnes", store=True)
    state = fields.Selection(
        selection=[
            ("available", "Available"),
            ("partially_retired", "Partially Retired"),
            ("retired", "Retired"),
            ("cancelled", "Cancelled"),
        ],
        default="available",
        required=True,
        tracking=True,
    )
    attachment_ids = fields.Many2many("ir.attachment", string="Certificates")
    notes = fields.Text()

    @api.depends("tonnes", "retired_tonnes")
    def _compute_available_tonnes(self) -> None:
        for offset in self:
            offset.available_tonnes = max(offset.tonnes - offset.retired_tonnes, 0.0)

    @api.constrains("tonnes", "retired_tonnes", "vintage_year")
    def _check_values(self) -> None:
        for offset in self:
            if offset.tonnes <= 0:
                raise ValidationError("Offset credits must be greater than zero.")
            if offset.retired_tonnes < 0 or offset.retired_tonnes > offset.tonnes:
                raise ValidationError("Retired tonnes must be between zero and purchased tonnes.")
            if offset.vintage_year and offset.vintage_year < 1900:
                raise ValidationError("Enter a valid vintage year.")

    def action_retire_all(self) -> None:
        for offset in self:
            offset.write({"retired_tonnes": offset.tonnes, "state": "retired"})

    def action_update_state(self) -> None:
        for offset in self:
            if offset.retired_tonnes >= offset.tonnes:
                offset.state = "retired"
            elif offset.retired_tonnes:
                offset.state = "partially_retired"
            else:
                offset.state = "available"

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


class EnviroInitiative(models.Model):
    _name = "enviro.initiative"
    _description = "ESG Reduction Initiative"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_date desc, id desc"
    _check_company_auto = True

    name = fields.Char(required=True, tracking=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    responsible_id = fields.Many2one("res.users", default=lambda self: self.env.user, tracking=True)
    category = fields.Selection(
        selection=[
            ("efficiency", "Efficiency"),
            ("renewable", "Renewable Energy"),
            ("fleet", "Fleet"),
            ("travel", "Travel"),
            ("waste", "Waste"),
            ("procurement", "Procurement"),
            ("other", "Other"),
        ],
        default="efficiency",
        required=True,
        tracking=True,
    )
    start_date = fields.Date(default=fields.Date.context_today, tracking=True)
    end_date = fields.Date(tracking=True)
    expected_saving_tonnes = fields.Float(string="Expected Saving tCO2e", tracking=True)
    actual_saving_tonnes = fields.Float(string="Actual Saving tCO2e", tracking=True)
    progress = fields.Float(default=0.0, tracking=True)
    state = fields.Selection(
        selection=[
            ("planned", "Planned"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        default="planned",
        required=True,
        tracking=True,
    )
    notes = fields.Text()

    @api.constrains("progress", "expected_saving_tonnes", "actual_saving_tonnes")
    def _check_values(self) -> None:
        for initiative in self:
            if initiative.progress < 0 or initiative.progress > 100:
                raise ValidationError("Progress must be between 0 and 100.")
            if initiative.expected_saving_tonnes < 0 or initiative.actual_saving_tonnes < 0:
                raise ValidationError("Savings must be zero or greater.")

    def action_start(self) -> None:
        self.write({"state": "in_progress"})

    def action_done(self) -> None:
        self.write({"state": "done", "progress": 100})

    def action_cancel(self) -> None:
        self.write({"state": "cancelled"})

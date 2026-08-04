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

from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    enviro_emission_record_ids = fields.One2many("enviro.emission.record", "account_move_id", string="Enviro Emission Records")
    enviro_emission_record_count = fields.Integer(compute="_compute_enviro_emission_record_count")
    reporting_period_id = fields.Many2one(
        "enviro.reporting.period",
        string="Reporting Period",
        compute="_compute_reporting_period",
        store=True,
        readonly=False,
        domain="[('company_id', '=', company_id), ('state', '=', 'open')]",
    )

    @api.depends("invoice_date", "company_id")
    def _compute_reporting_period(self):
        for move in self:
            if move.reporting_period_id:
                continue  # never overwrite a manually chosen period
            date = move.invoice_date or fields.Date.context_today(move)
            move.reporting_period_id = self.env["enviro.reporting.period"].search([
                ("company_id", "=", move.company_id.id),
                ("state", "=", "open"),
                ("date_start", "<=", date),
                ("date_end", ">=", date),
            ], limit=1)

    def _compute_enviro_emission_record_count(self) -> None:
        for move in self:
            move.enviro_emission_record_count = len(move.enviro_emission_record_ids)

    def _create_enviro_emission_records_from_rules(self):
        EsgRecord = self.env["enviro.emission.record"].sudo()
        FactorRule = self.env["enviro.factor.rule"].sudo()
        created_records = EsgRecord.browse()
        for move in self:
            for line in move.invoice_line_ids.filtered(lambda aml: aml.display_type == "product" and aml.quantity):
                existing = EsgRecord.search([("account_move_line_id", "=", line.id)], limit=1)
                if existing:
                    continue
                rule = FactorRule._find_factor_for_line(line)
                factor = rule.factor_id
                if not factor:
                    continue
                vals = {
                    "name": line.name or move.name or _("Accounting Emission"),
                    "company_id": move.company_id.id,
                    "date": move.invoice_date or move.date or fields.Date.context_today(self),
                    "factor_id": factor.id,
                    "enviro_activity_type_id": rule.activity_type_id.id,
                    "quantity": abs(line.quantity) or 1.0,
                    "uom_id": line.product_uom_id.id if line.product_uom_id else (factor.uom_id.id if factor.uom_id else False),
                    "currency_id": line.currency_id.id or move.currency_id.id,
                    "amount": abs(line.price_subtotal),
                    "source_type": "invoice" if move.is_invoice() else "journal",
                    "account_move_id": move.id,
                    "account_move_line_id": line.id,
                    "reporting_period_id": move.reporting_period_id.id if move.reporting_period_id else False,
                    "state": "logged",
                    "notes": _("Generated from %(move)s.", move=move.name or move.display_name),
                }
                created_records |= EsgRecord.create(vals)
        return created_records

    def action_post(self):
        result = super().action_post()
        self.filtered(lambda move: move.move_type in ("in_invoice", "in_refund"))._create_enviro_emission_records_from_rules()
        return result

    def action_generate_enviro_emission_records(self) -> dict:
        created_records = self._create_enviro_emission_records_from_rules()
        if not created_records:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": "warning",
                    "title": _("No ESG Records Created"),
                    "message": _("No eligible invoice lines matched a factor rule, or records already exist for those lines."),
                    "sticky": False,
                },
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("Generated Enviro Emission Records"),
            "res_model": "enviro.emission.record",
            "view_mode": "list,form",
            "domain": [("id", "in", created_records.ids)],
        }

    def action_view_enviro_emission_records(self) -> dict:
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Enviro Emission Records"),
            "res_model": "enviro.emission.record",
            "view_mode": "list,form,kanban,pivot,graph",
            "domain": [("account_move_id", "=", self.id)],
            "context": {"default_account_move_id": self.id, "default_source_type": "invoice"},
        }

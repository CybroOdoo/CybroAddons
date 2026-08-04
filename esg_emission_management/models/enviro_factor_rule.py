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
from odoo.exceptions import ValidationError


class EnviroFactorRule(models.Model):
    _name = "enviro.factor.rule"
    _description = "Enviro Factor Assignment Rule"
    _order = "sequence, id"
    _check_company_auto = True

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    factor_id = fields.Many2one(
        "enviro.emission.factor",
        required=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
    )
    activity_type_id = fields.Many2one("enviro.activity.type")
    product_id = fields.Many2one("product.product", string="Product")
    partner_id = fields.Many2one("res.partner", string="Vendor/Partner")
    account_id = fields.Many2one("account.account", string="Account", check_company=True)

    @api.constrains("product_id", "partner_id", "account_id")
    def _check_any_condition(self) -> None:
        for rule in self:
            if not (rule.product_id or rule.partner_id or rule.account_id):
                raise ValidationError(
                    _("An assignment rule needs at least one product, partner, or account condition.")
                )

    @api.model
    def _find_factor_for_line(self, line):
        rules = self.search([
            ("active", "=", True),
            "|",
            ("company_id", "=", False),
            ("company_id", "=", line.company_id.id),
        ])
        candidates = self.browse()
        for rule in rules:
            if rule.product_id and rule.product_id != line.product_id:
                continue
            if rule.partner_id and rule.partner_id != line.partner_id:
                continue
            if rule.account_id and rule.account_id != line.account_id:
                continue
            candidates |= rule
        return max(
            candidates,
            key=lambda rule: bool(rule.product_id) + bool(rule.partner_id) + bool(rule.account_id),
            default=self.browse(),
        )

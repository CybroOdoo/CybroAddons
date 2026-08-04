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

from odoo import fields, models


class EnviroActivityType(models.Model):
    _name = "enviro.activity.type"
    _description = "Enviro Activity Type"
    _order = "scope, sequence, name"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    scope = fields.Selection(
        selection=[
            ("scope1", "Direct (Scope 1)"),
            ("scope2", "Indirect Energy (Scope 2)"),
            ("scope3", "Other Indirect (Scope 3)"),
        ],
        string="Reporting Class",
        required=True,
        default="scope1",
    )
    category = fields.Selection(
        selection=[
            ("energy", "Energy"),
            ("fleet", "Fleet"),
            ("travel", "Travel"),
            ("waste", "Waste"),
            ("water", "Water"),
            ("procurement", "Procurement"),
            ("supplier", "Supplier"),
            ("offset", "Offset"),
            ("other", "Other"),
        ],
        default="other",
        required=True,
    )
    description = fields.Text()

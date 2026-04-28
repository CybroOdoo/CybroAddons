# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Arjun S (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class IrUiMenu(models.Model):
    """Inherits the ir.ui.menu model to implement logic that identifies and
    removes menu items created through the Odoo Dynamic Dashboard module
    during uninstallation"""
    _inherit = "ir.ui.menu"

    is_from_dynamic_dashboard = fields.Boolean(string="From Dynamic Dashboard",
                                               help="This menu is created from "
                                                    "dynamic dashboard")

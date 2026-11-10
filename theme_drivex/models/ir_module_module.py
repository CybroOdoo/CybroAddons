# -*- coding: utf-8 -*-
#############################################################################
#
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
from odoo import models


class IrModuleModule(models.Model):
    """Remove the DriveX menus and views when the theme is unloaded."""
    _inherit = "ir.module.module"

    def _theme_unload(self, website):
        """Remove the DriveX website menus and views of the theme."""
        res = super()._theme_unload(website)
        for module in self:
            if module.name != "theme_drivex":
                continue
            self.env["website.menu"].search(
                [("url", "in", ["/fleet", "/services", "/about"])]).unlink()
            self.env["ir.ui.view"].search(
                [("key", "ilike", "theme_drivex")]).unlink()
        return res

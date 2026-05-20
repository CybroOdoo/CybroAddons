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

from odoo import models


class ResConfigSettings(models.TransientModel):
    """Adds manufacturing setup options to system settings."""
    _inherit = 'res.config.settings'

    def set_values(self):
        """
        Overrides set_values to auto-enable MRP-related features (by-products,
        work order dependencies) when the Oil Manufacturing module is enabled.
        """
        if self.module_oil_erp_manufacturing:
            self.group_mrp_byproducts = True
            self.group_mrp_workorder_dependencies = True
        super().set_values()

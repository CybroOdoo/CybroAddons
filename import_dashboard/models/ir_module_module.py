# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class Uninstall(models.Model):
    """ Inheriting the ir module for setting fields as false if any of the
        modules are uninstalled """
    _inherit = 'ir.module.module'

    def button_uninstall(self):
        """ When a module is uninstalled set the corresponding boolean field
            to False """
        if self.name == 'mrp':
            self.env['ir.config_parameter'].sudo().set_param(
                "import_dashboard.import_bom",
                False)
        if self.name == 'point_of_sale':
            self.env['ir.config_parameter'].sudo().set_param(
                "import_dashboard.import_pos",
                False)
        if self.name == 'hr_attendance':
            self.env['ir.config_parameter'].sudo().set_param(
                "import_dashboard.import_attendance", False)
        if self.name == 'sale_management':
            self.env['ir.config_parameter'].sudo().set_param(
                "import_dashboard.import_sale",
                False)
        if self.name == 'purchase':
            self.env['ir.config_parameter'].sudo().set_param(
                "import_dashboard.import_purchase_order", False)
            self.env['ir.config_parameter'].sudo().set_param(
                "import_vendor_pricelist", False)
        if self.name == 'account':
            self.env['ir.config_parameter'].sudo().set_param(
                "import_dashboard.import_invoice",
                False)
            self.env['ir.config_parameter'].sudo().set_param(
                "import_dashboard.import_payment",
                False)
        if self.name == 'project':
            self.env['ir.config_parameter'].sudo().set_param(
                "import_dashboard.import_task",
                False)
        if self.name == 'product':
            self.env['ir.config_parameter'].sudo().set_param(
                "import_dashboard.import_product_template", False)
        return super().button_uninstall()

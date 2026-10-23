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
#############################################################################
from odoo import models


class IrModuleModule(models.Model):
    """ Model for inherit and add feature to method 'button_uninstall' """
    _inherit = 'ir.module.module'

    def button_uninstall(self):
        """When a module is uninstalled set
        the corresponding boolean field to False"""
        icp = self.env['ir.config_parameter'].sudo()
        module_param_map = {
            'mrp': ['import_dashboard.import_bom'],
            'point_of_sale': ['import_dashboard.import_pos'],
            'hr_attendance': ['import_dashboard.import_attendance'],
            'sale_management': ['import_dashboard.import_sale'],
            'purchase': ['import_dashboard.import_purchase_order', 'import_dashboard.import_vendor_pricelist'],
            'account': ['import_dashboard.import_invoice', 'import_dashboard.import_payment'],
            'project': ['import_dashboard.import_task'],
            'product': ['import_dashboard.import_product_template'],
        }
        for module in self:
            params = module_param_map.get(module.name, [])
            for param in params:
                icp.set_bool(param, False)
        return super().button_uninstall()

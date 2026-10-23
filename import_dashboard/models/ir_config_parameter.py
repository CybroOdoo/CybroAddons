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
from odoo import api, models
from odoo.exceptions import ValidationError


class IrConfigParameter(models.Model):
    """ Model for storing configuration parameters. """
    _inherit = 'ir.config_parameter'

    def _check_module_prerequisites(self, key, value):
        """Check required modules before allowing import flags to be enabled"""
        if not value or value in ('False', '0', 0):
            return

        module_checks = {
            'import_dashboard.import_bom': 'mrp',
            'import_dashboard.import_pos': 'point_of_sale',
            'import_dashboard.import_sale': 'sale_management',
            'import_dashboard.import_attendance': 'hr_attendance',
            'import_dashboard.import_purchase_order': 'purchase',
            'import_dashboard.import_vendor_pricelist': 'purchase',
            'import_dashboard.import_invoice': 'account',
            'import_dashboard.import_payment': 'account',
            'import_dashboard.import_task': 'project',
            'import_dashboard.import_product_template': 'product',
        }

        required_module = module_checks.get(key)
        if required_module:
            module = self.env['ir.module.module'].search([('name', '=', required_module)], limit=1)
            if not module or module.state != 'installed':
                module_name = (module.shortdesc if module else False) or required_module
                raise ValidationError(
                    self.env._("You must install the '%s' module to enable this import.", module_name)
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_module_prerequisites(vals.get('key'), vals.get('value'))
        return super().create(vals_list)

    def write(self, vals):
        if 'value' in vals:
            for record in self:
                key = vals.get('key', record.key)
                self._check_module_prerequisites(key, vals['value'])
        return super().write(vals)

    @api.model
    def check_user_group(self):
        """Return current import permissions for the dashboard"""
        icp = self.env['ir.config_parameter'].sudo()

        def _b(key):
            return icp.get_bool(key, False)

        return {
            'bill_of_material': _b('import_dashboard.import_bom'),
            'pos': _b('import_dashboard.import_pos'),
            'import_attendance': _b('import_dashboard.import_attendance'),
            'import_payment': _b('import_dashboard.import_payment'),
            'import_task': _b('import_dashboard.import_task'),
            'import_sale': _b('import_dashboard.import_sale'),
            'import_purchase': _b('import_dashboard.import_purchase_order'),
            'import_product_template': _b('import_dashboard.import_product_template'),
            'import_partner': _b('import_dashboard.import_partner'),
            'import_invoice': _b('import_dashboard.import_invoice'),
            'import_pricelist': _b('import_dashboard.import_pricelist'),
            'import_vendor_pricelist': _b('import_dashboard.import_vendor_pricelist'),
        }

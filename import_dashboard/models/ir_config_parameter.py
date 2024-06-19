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
from odoo import api, models, _
from odoo.exceptions import ValidationError


class IrConfigParameter(models.Model):
    """ Model for storing configuration parameters. """
    _inherit = 'ir.config_parameter'

    @api.model
    def create(self, vals_list):
        """For checking the necessary modules are installed"""
        if vals_list.get('key') == 'import_bom':
            if vals_list['value']:
                check = self.env["ir.module.module"].search(
                    [('name', '=', 'mrp')])
                if check.state == 'uninstalled':
                    vals_list['value'] = False
                    raise ValidationError(_('The module is not found. Please '
                                          'make sure you have it installed'))
                else:
                    pass
        if vals_list.get('key') == 'import_pos':
            if vals_list['value']:
                check = self.env["ir.module.module"].search(
                    [('name', '=', 'point_of_sale')])
                if check.state == 'uninstalled':
                    vals_list['value'] = False
                    raise ValidationError(_('The module is not found. Please '
                                            'make sure you have it installed'))
                else:
                    pass
        if vals_list.get('key') == 'import_sale':
            if vals_list['value']:
                check = self.env["ir.module.module"].search(
                    [('name', '=', 'sale_management')])
                if check.state == 'uninstalled':
                    vals_list['value'] = False
                    raise ValidationError(_('The module is not found. Please '
                                          'make sure you have it installed'))
                else:
                    pass
        if vals_list.get('key') == 'import_attendance':
            if vals_list['value']:
                check = self.env["ir.module.module"].search(
                    [('name', '=', 'hr_attendance')])
                if check.state == 'uninstalled':
                    vals_list['value'] = False
                    raise ValidationError(_('The module is not found. Please '
                                          'make sure you have it installed'))
                else:
                    pass
        if vals_list.get('key') == 'import_purchase_order':
            if vals_list['value']:
                check = self.env["ir.module.module"].search(
                    [('name', '=', 'purchase')])
                if check.state == 'uninstalled':
                    vals_list['value'] = False
                    raise ValidationError(_('The module is not found. Please '
                                          'make sure you have it installed'))
                else:
                    pass
        if vals_list.get('key') == 'import_vendor_pricelist':
            if vals_list['value']:
                check = self.env["ir.module.module"].search(
                    [('name', '=', 'purchase')])
                if check.state == 'uninstalled':
                    vals_list['value'] = False
                    raise ValidationError(_('The module is not found. Please '
                                          'make sure you have it installed'))
                else:
                    pass
        if vals_list.get('key') == 'import_invoice':
            if vals_list['value']:
                check = self.env["ir.module.module"].search(
                    [('name', '=', 'account')])
                if check.state == 'uninstalled':
                    vals_list['value'] = False
                    raise ValidationError(_('The module is not found. Please '
                                          'make sure you have it installed'))
                else:
                    pass
        if vals_list.get('key') == 'import_payment':
            if vals_list['value']:
                check = self.env["ir.module.module"].search(
                    [('name', '=', 'account')])
                if check.state == 'uninstalled':
                    vals_list['value'] = False
                    raise ValidationError(_('The module is not found. Please '
                                          'make sure you have it installed'))
                else:
                    pass
        if vals_list.get('key') == 'import_task':
            if vals_list['value']:
                check = self.env["ir.module.module"].search(
                    [('name', '=', 'project')])
                if check.state == 'uninstalled':
                    vals_list['value'] = False
                    raise ValidationError(_('The module is not found. Please '
                                          'make sure you have it installed'))
                else:
                    pass
        if vals_list.get('key') == 'import_product_template ':
            if vals_list['value']:
                check = self.env["ir.module.module"].search(
                    [('name', '=', 'product')])
                if check.state == 'uninstalled':
                    vals_list['value'] = False
                    raise ValidationError(_('The module is not found. Please '
                                          'make sure you have it installed'))
                else:
                    pass
        return super(IrConfigParameter, self).create(vals_list)

    @api.model
    def check_user_group(self):
        """For enabling the corresponding tiles in the dashboard """
        bill_of_material = self.env['ir.config_parameter'].sudo().get_param(
            "import_bom")
        pos = self.env['ir.config_parameter'].sudo().get_param("import_pos")
        import_attendance = self.env['ir.config_parameter'].sudo().get_param(
            "import_attendance")
        import_payment = self.env['ir.config_parameter'].sudo().get_param(
            "import_payment")
        import_task = self.env['ir.config_parameter'].sudo().get_param(
            "import_task")
        import_sale = self.env['ir.config_parameter'].sudo().get_param(
            "import_sale")
        import_purchase = self.env['ir.config_parameter'].sudo().get_param(
            "import_purchase_order")
        import_product_template = self.env[
            'ir.config_parameter'].sudo().get_param("import_product_template")
        import_partner = self.env['ir.config_parameter'].sudo().get_param(
            "import_partner")
        import_invoice = self.env['ir.config_parameter'].sudo().get_param(
            "import_invoice")
        import_pricelist = self.env['ir.config_parameter'].sudo().get_param(
            "import_pricelist")
        import_vendor_pricelist = self.env[
            'ir.config_parameter'].sudo().get_param("import_vendor_pricelist")
        return {
            'bill_of_material': bill_of_material,
            'pos': pos,
            'import_attendance': import_attendance,
            'import_payment': import_payment,
            'import_task': import_task,
            'import_sale': import_sale,
            'import_purchase': import_purchase,
            'import_product_template': import_product_template,
            'import_partner': import_partner,
            'import_invoice': import_invoice,
            'import_pricelist': import_pricelist,
            'import_vendor_pricelist': import_vendor_pricelist,
        }

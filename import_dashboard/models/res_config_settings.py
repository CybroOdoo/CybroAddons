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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    """ Model for enable import options in settings. """
    _inherit = 'res.config.settings'

    import_bom = fields.Boolean(default=False,
        help='For importing bom files', string="Import BoM")
    import_pos = fields.Boolean(default=False,
        help='For importing pos', string="Import POS")
    import_attendance = fields.Boolean(
        string="Import Attendance", help='For importing attendance', default=False)
    import_payment = fields.Boolean(
        string="Import Payment", help='For importing payments')
    import_task = fields.Boolean(
        string="Import Task", default=False, help='For importing tasks')
    import_sale = fields.Boolean(
        string="Import Sale", help='For importing sales orders', default=False)
    import_purchase_order = fields.Boolean(default=False
        , string="Import Purchase Order", help='For importing purchase orders')
    import_product_template = fields.Boolean(
        string="Import Product Template", help='For importing Products',
        default=False)
    import_partner = fields.Boolean(
        string="Import Partner", help='For importing partners', default=False)
    import_entry = fields.Boolean(
        string="Import Journal Entries", help='For importing Journal Entries', default=False)
    import_pricelist = fields.Boolean(
        string="Import Pricelist", help='For importing price lists', default=False)
    import_vendor_pricelist = fields.Boolean(
        string="Import Vendor Pricelist", default=False,
        help='For importing vendor price lists')

    @api.model
    def get_values(self):
        """Getting the values of the corresponding importing items"""
        res = super(ResConfigSettings, self).get_values()
        res['import_bom'] = self.env[
            'ir.config_parameter'].sudo().get_param('import_bom')
        res['import_pos'] = self.env[
            'ir.config_parameter'].sudo().get_param('import_pos')
        res['import_attendance'] = self.env[
            'ir.config_parameter'].sudo().get_param('import_attendance')
        res['import_payment'] = self.env[
            'ir.config_parameter'].sudo().get_param('import_payment')
        res['import_task'] = self.env[
            'ir.config_parameter'].sudo().get_param('import_task')
        res['import_sale'] = self.env[
            'ir.config_parameter'].sudo().get_param('import_sale')
        res['import_purchase_order'] = self.env[
            'ir.config_parameter'].sudo().get_param('import_purchase_order')
        res['import_product_template'] = self.env[
            'ir.config_parameter'].sudo().get_param('import_product_template')
        res['import_partner'] = self.env[
            'ir.config_parameter'].sudo().get_param('import_partner')
        res['import_entry'] = self.env[
            'ir.config_parameter'].sudo().get_param('import_entry')
        res['import_pricelist'] = self.env[
            'ir.config_parameter'].sudo().get_param('import_pricelist')
        res['import_vendor_pricelist'] = self.env[
            'ir.config_parameter'].sudo().get_param('import_vendor_pricelist')
        return res

    def _check_installation(self):
        """A function to check if the selected modules from Res Config Settings are all installed"""
        uninstalled_list = []
        if self.import_bom:
            check = self.env["ir.module.module"].search(
                [('name', '=', 'mrp')])
            if check.state == 'uninstalled':
                uninstalled_list.append('Manufacturing')
        if self.import_pos:
            check = self.env["ir.module.module"].search(
                [('name', '=', 'point_of_sale')])
            if check.state == 'uninstalled':
                uninstalled_list.append('Point of Sale')
        if self.import_sale:
            check = self.env["ir.module.module"].search(
                [('name', '=', 'sale_management')])
            if check.state == 'uninstalled':
                uninstalled_list.append('Sales')
        if self.import_attendance:
            check = self.env["ir.module.module"].search(
                [('name', '=', 'hr_attendance')])
            if check.state == 'uninstalled':
                uninstalled_list.append('Attendances')
        if self.import_purchase_order:
            check = self.env["ir.module.module"].search(
                [('name', '=', 'purchase')])
            if check.state == 'uninstalled':
                uninstalled_list.append('Purchase')
        if self.import_vendor_pricelist:
            check = self.env["ir.module.module"].search(
                [('name', '=', 'purchase')])
            if check.state == 'uninstalled':
                uninstalled_list.append('Purchase')
        if self.import_entry:
            check = self.env["ir.module.module"].search(
                [('name', '=', 'account')])
            if check.state == 'uninstalled':
                uninstalled_list.append('Invoicing')
        if self.import_payment:
            check = self.env["ir.module.module"].search(
                [('name', '=', 'account')])
            if check.state == 'uninstalled':
                uninstalled_list.append('Invoicing')
        if self.import_task:
            check = self.env["ir.module.module"].search(
                [('name', '=', 'project')])
            if check.state == 'uninstalled':
                uninstalled_list.append('Project')
        if self.import_product_template :
            check = self.env["ir.module.module"].search(
                [('name', '=', 'product')])
            if check.state == 'uninstalled':
                uninstalled_list.append('Product')
        if uninstalled_list:
            raise UserError(_(f"The following modules are not installed."
                              f"Please make sure installation before continuing:\n{', '.join(set(uninstalled_list))}"))

    @api.model
    def set_values(self):
        """Setting the values of the corresponding importing items"""
        self._check_installation()
        self.env['ir.config_parameter'].sudo().set_param(
            'import_bom', self.import_bom)
        self.env['ir.config_parameter'].sudo().set_param(
            'import_pos', self.import_pos)
        self.env['ir.config_parameter'].sudo().set_param(
            'import_attendance', self.import_attendance)
        self.env['ir.config_parameter'].sudo().set_param(
            'import_payment', self.import_payment)
        self.env['ir.config_parameter'].sudo().set_param(
            'import_task', self.import_task)
        self.env['ir.config_parameter'].sudo().set_param(
            'import_sale', self.import_sale)
        self.env['ir.config_parameter'].sudo().set_param(
            'import_purchase_order', self.import_purchase_order)
        self.env['ir.config_parameter'].sudo().set_param(
            'import_product_template', self.import_product_template)
        self.env['ir.config_parameter'].sudo().set_param(
            'import_partner', self.import_partner)
        self.env['ir.config_parameter'].sudo().set_param(
            'import_entry', self.import_entry)
        self.env['ir.config_parameter'].sudo().set_param(
            'import_pricelist', self.import_pricelist)
        self.env['ir.config_parameter'].sudo().set_param(
            'import_vendor_pricelist', self.import_vendor_pricelist)
        super(ResConfigSettings, self).set_values()

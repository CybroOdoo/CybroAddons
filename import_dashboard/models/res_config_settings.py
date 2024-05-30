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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """ Model for enable import options in settings. """
    _inherit = 'res.config.settings'

    import_bom = fields.Boolean(
        config_parameter='import_dashboard.import_bom', default=False,
        help='For importing bom files', string="Import BoM")
    import_pos = fields.Boolean(
        config_parameter='import_dashboard.import_pos', default=False,
        help='For importing pos', string="Import POS")
    import_attendance = fields.Boolean(
        string="Import Attendance", help='For importing attendance',
        config_parameter='import_dashboard.import_attendance', default=False)
    import_payment = fields.Boolean(
        string="Import Payment", help='For importing payments',
        default=False, config_parameter='import_dashboard.import_payment')
    import_task = fields.Boolean(
        string="Import Task", default=False, help='For importing tasks',
        config_parameter='import_dashboard.import_task', )
    import_sale = fields.Boolean(
        string="Import Sale", help='For importing sales orders',
        config_parameter='import_dashboard.import_sale', default=False)
    import_purchase_order = fields.Boolean(
        config_parameter='import_dashboard.import_purchase_order', default=False
        , string="Import Purchase Order", help='For importing purchase orders')
    import_product_template = fields.Boolean(
        string="Import Product Template", help='For importing Products',
        config_parameter='import_dashboard.import_product_template',
        default=False)
    import_partner = fields.Boolean(
        string="Import Partner", help='For importing partners', default=False,
        config_parameter='import_dashboard.import_partner')
    import_invoice = fields.Boolean(
        string="Import Invoices", help='For importing invoices', default=False,
        config_parameter='import_dashboard.import_invoice')
    import_pricelist = fields.Boolean(
        string="Import Pricelist", help='For importing price lists',
        config_parameter='import_dashboard.import_pricelist', default=False)
    import_vendor_pricelist = fields.Boolean(
        string="Import Vendor Pricelist", default=False,
        config_parameter='import_dashboard.import_vendor_pricelist',
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
        res['import_invoice'] = self.env[
            'ir.config_parameter'].sudo().get_param('import_invoice')
        res['import_pricelist'] = self.env[
            'ir.config_parameter'].sudo().get_param('import_pricelist')
        res['import_vendor_pricelist'] = self.env[
            'ir.config_parameter'].sudo().get_param('import_vendor_pricelist')
        return res

    @api.model
    def set_values(self):
        """Setting the values of the corresponding importing items"""
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
            'import_invoice', self.import_invoice)
        self.env['ir.config_parameter'].sudo().set_param(
            'import_pricelist', self.import_pricelist)
        self.env['ir.config_parameter'].sudo().set_param(
            'import_vendor_pricelist', self.import_vendor_pricelist)
        super(ResConfigSettings, self).set_values()

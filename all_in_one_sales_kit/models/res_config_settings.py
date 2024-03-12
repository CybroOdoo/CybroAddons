# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """ This is to add new fields to the settings.res.config.settings is
    inherited."""
    _inherit = 'res.config.settings'

    show_product_image_in_sale_report = fields.Boolean(
        string="Show Product Image", default=False,
        help="Enable Show Product Image")
    sale_document_approve = fields.Boolean(
        config_parameter='all_in_one_sales_kit.sale_document_approve',
        string="Sale Document Approval",
        help="Sale Approval")
    product_restriction = fields.Boolean(
        string='Out Of Stock Product Restriction',
        help='Enable Out Of Stock Product Restriction')
    check_stock = fields.Selection(
        [('on_hand_quantity', 'On Hand Quantity'),
         ('forecast_quantity', 'Forecast Quantity')], string="Based On",
        help='Choose the type of restriction')
    automate_invoice = fields.Boolean(
        string='Create Invoice', default=False,
        help="Create invoices for sales order")
    automate_validate_invoice = fields.Boolean(
        string='Validate Invoice', default=False,
        help="Automate validation of invoice")
    automate_print_invoices = fields.Boolean(
        string='Print Invoices', default=False,
        help="Print invoice from corresponding sales order")

    @api.model
    def set_values(self):
        """The function set_values() is to store the new fields values."""
        self.env['ir.config_parameter'].sudo().set_param(
            'sale_product_image.show_product_image_in_sale_report',
            self.show_product_image_in_sale_report)
        self.env['ir.config_parameter'].sudo().set_param(
            'sale_stock_restrict.product_restriction',
            self.product_restriction)
        self.env['ir.config_parameter'].sudo().set_param(
            'sale_stock_restrict.check_stock', self.check_stock)
        self.env['ir.config_parameter'].sudo().set_param(
            'automate_print_invoices', self.automate_print_invoices)
        self.env['ir.config_parameter'].sudo().set_param(
            'automate_invoice', self.automate_invoice)
        self.env['ir.config_parameter'].sudo().set_param(
            'automate_validate_invoice', self.automate_validate_invoice)
        res = super(ResConfigSettings, self).set_values()
        return res

    def get_values(self):
        """Show the new field values."""
        res = super(ResConfigSettings, self).get_values()
        ir_config_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            show_product_image_in_sale_report=ir_config_param(
                'sale_product_image.show_product_image_in_sale_report',
                self.show_product_image_in_sale_report),
            product_restriction=ir_config_param(
                'sale_stock_restrict.product_restriction'),
            check_stock=ir_config_param('sale_stock_restrict.check_stock'),
            automate_print_invoices=ir_config_param('automate_print_invoices'),
            automate_invoice=ir_config_param('automate_invoice'),
            automate_validate_invoice=ir_config_param(
                'automate_validate_invoice'),
        )
        return res

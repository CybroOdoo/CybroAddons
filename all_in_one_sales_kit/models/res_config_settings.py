# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """ This is to add new fields to the settings.res.config.settings is
    inherited."""
    _inherit = 'res.config.settings'

    show_product_image_in_sale_report = fields.Boolean(
        string="Show Product Image",
        config_parameter='sale_product_image.show_product_image_in_sale_report',
        help="Enable Show Product Image"
    )
    sale_document_approve = fields.Boolean(
        config_parameter='all_in_one_sales_kit.sale_document_approve',
        string="Sale Document Approval",
        help="Sale Approval"
    )
    product_restriction = fields.Boolean(
        string='Out Of Stock Product Restriction',
        config_parameter='sale_stock_restrict.product_restriction',
        help='Enable Out Of Stock Product Restriction'
    )
    check_stock = fields.Selection(
        [
            ('on_hand_quantity', 'On Hand Quantity'),
            ('forecast_quantity', 'Forecast Quantity')
        ],
        string="Based On",
        config_parameter='sale_stock_restrict.check_stock',
        help='Choose the type of restriction'
    )
    automate_invoice = fields.Boolean(
        string='Create Invoice',
        config_parameter='automate_invoice',
        help="Create invoices for sales order"
    )
    automate_validate_invoice = fields.Boolean(
        string='Validate Invoice',
        config_parameter='automate_validate_invoice',
        help="Automate validation of invoice"
    )
    automate_print_invoices = fields.Boolean(
        string='Print Invoices',
        config_parameter='automate_print_invoices',
        help="Print invoice from corresponding sales order"
    )

# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit the 'res_config_settings' model to add fields
    in the settings of the Sale and Purchase modules."""
    _inherit = 'res.config.settings'

    automate_purchase = fields.Boolean(
        string='Confirm RFQ', help="Automate confirmation for RFQ",
        config_parameter='automate_purchase')
    automate_print_bills = fields.Boolean(
        string='Print Bills', config_parameter="automate_print_bills",
        help="Print bill from corresponding purchase order")
    automate_sale = fields.Boolean(
        string='Confirm Quotation', config_parameter="automate_sale",
        help="Automate confirmation for quotation")
    automate_invoice = fields.Boolean(
        string='Create Invoice', config_parameter="automate_invoice",
        help="Create invoices for sales order")
    automate_validate_invoice = fields.Boolean(
        string='Validate Invoice', config_parameter="automate_validate_invoice",
        help="Automate validation of invoice")
    automate_print_invoices = fields.Boolean(
        string='Print Invoices', config_parameter="automate_print_invoices",
        help="Print invoice from corresponding sales order")

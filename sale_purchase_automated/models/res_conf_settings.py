# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nimisha Muralidhar (odoo@cybrosys.com)
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
#############################################################################

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    automate_purchase = fields.Boolean('Confirm RFQ', default=False, help="Automate confirmation for RFQ")
    automate_print_bills = fields.Boolean('Print Bills', default=False, help="Print bills of corresponding purchase order")
    automate_sale = fields.Boolean('Confirm Quotation', default=False, help="Automate confirmation for quotation")
    automate_invoice = fields.Boolean('Create Invoice', default=False, help="Create invoices for sale order")
    automate_validate_voice = fields.Boolean('Validate Invoice', default=False, help="Validate Invoices")
    automate_print_invoices = fields.Boolean('Print Invoices', default=False, help="Print invoices of corresponding sales order")


    @api.model
    def get_values(self):
        """get values from the fields"""
        res = super(ResConfigSettings, self).get_values()
        res.update(
            automate_purchase=self.env['ir.config_parameter'].sudo().get_param('automate_purchase'),
            automate_print_bills=self.env['ir.config_parameter'].sudo().get_param('automate_print_bills'),
            automate_print_invoices=self.env['ir.config_parameter'].sudo().get_param('automate_print_invoices'),
            automate_sale=self.env['ir.config_parameter'].sudo().get_param('automate_sale'),
            automate_invoice=self.env['ir.config_parameter'].sudo().get_param('automate_invoice'),
            automate_validate_voice=self.env['ir.config_parameter'].sudo().get_param('automate_validate_voice'),
        )
        return res

    def set_values(self):
        """Set values in the fields"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('automate_purchase', self.automate_purchase)
        self.env['ir.config_parameter'].sudo().set_param('automate_print_bills', self.automate_print_bills)
        self.env['ir.config_parameter'].sudo().set_param('automate_print_invoices', self.automate_print_invoices)
        self.env['ir.config_parameter'].sudo().set_param('automate_sale', self.automate_sale)
        self.env['ir.config_parameter'].sudo().set_param('automate_invoice', self.automate_invoice)
        self.env['ir.config_parameter'].sudo().set_param('automate_validate_voice', self.automate_validate_voice)
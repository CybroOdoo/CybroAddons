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
    """To set up notes in configuration"""
    _inherit = "res.config.settings"

    sale_notes = fields.Html(string='Notes', translate=True,
                             help="Notes displayed in sale reports.")
    purchase_notes = fields.Html(string='Notes', translate=True,
                                 help="Notes displayed in purchase reports.")
    delivery_notes = fields.Html(string='Notes', translate=True,
                                 help="Notes displayed in Delivery reports.")
    invoice_notes = fields.Html(string='Notes', translate=True,
                                help="Notes displayed in Invoice reports.")

    @api.model
    def get_values(self):
        """get the html notes default value from ir.config_parameter"""
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        sale_notes = params.get_param('sale_notes', default=False)
        purchase_notes = params.get_param('purchase_notes', default=False)
        delivery_notes = params.get_param('delivery_notes', default=False)
        invoice_notes = params.get_param('invoice_notes', default=False)
        res.update(
            sale_notes=sale_notes,
            purchase_notes=purchase_notes,
            delivery_notes=delivery_notes,
            invoice_notes=invoice_notes,
        )
        return res

    def set_values(self):
        """To set the html notes default value to ir.config_parameter"""
        res = super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            "sale_notes", self.sale_notes or False)
        self.env['ir.config_parameter'].sudo().set_param(
            "purchase_notes", self.purchase_notes or False)
        self.env['ir.config_parameter'].sudo().set_param(
            "delivery_notes", self.delivery_notes or False)
        self.env['ir.config_parameter'].sudo().set_param(
            "invoice_notes", self.invoice_notes or False)
        return res

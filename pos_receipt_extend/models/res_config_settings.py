# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    qr_code = fields.Boolean(string='Order QRCode')
    invoice_number = fields.Boolean()
    customer_details = fields.Boolean()
    customer_name = fields.Boolean()
    customer_address = fields.Boolean()
    customer_mobile = fields.Boolean()
    customer_phone = fields.Boolean()
    customer_email = fields.Boolean()
    customer_vat = fields.Boolean()

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('res.config.settings.customer_details',
                  int(self.customer_details))
        set_param('res.config.settings.customer_name',
                  int(self.customer_name))
        set_param('res.config.settings.customer_address',
                  int(self.customer_address))
        set_param('res.config.settings.customer_mobile',
                  int(self.customer_mobile))
        set_param('res.config.settings.customer_phone',
                  int(self.customer_phone))
        set_param('res.config.settings.customer_email',
                  int(self.customer_email))
        set_param('res.config.settings.customer_vat',
                  int(self.customer_vat))
        set_param('res.config.settings.qr_code',
                  int(self.qr_code))
        set_param('res.config.settings.invoice_number',
                  int(self.invoice_number))
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res['customer_details'] = int(
            get_param('res.config.settings.customer_details'))
        res['customer_name'] = int(
            get_param('res.config.settings.customer_name'))
        res['customer_address'] = int(
            get_param('res.config.settings.customer_address'))
        res['customer_mobile'] = int(
            get_param('res.config.settings.customer_mobile'))
        res['customer_phone'] = int(
            get_param('res.config.settings.customer_phone'))
        res['customer_email'] = int(
            get_param('res.config.settings.customer_email'))
        res['customer_vat'] = int(
            get_param('res.config.settings.customer_vat'))
        res['qr_code'] = int(
            get_param('res.config.settings.qr_code'))
        res['invoice_number'] = int(
            get_param('res.config.settings.invoice_number'))
        return res

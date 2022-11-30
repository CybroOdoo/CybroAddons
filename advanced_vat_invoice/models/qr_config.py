# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>))
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################

from odoo import fields, models, api


class QRCode(models.TransientModel):
    _inherit = 'res.config.settings'

    generate_qr = fields.Selection(
        [('automatically', 'Generate QR Code when invoice validate/post'), ('manually', 'Manually Generate')])
    is_qr = fields.Boolean("QR Code Generation Configuration")

    @api.model
    def get_values(self):
        res = super(QRCode, self).get_values()
        res.update(
            generate_qr=self.env['ir.config_parameter'].sudo().get_param('advanced_vat_invoice.generate_qr'),
            is_qr=self.env['ir.config_parameter'].sudo().get_param('advanced_vat_invoice.is_qr'),
        )
        return res

    def set_values(self):
        super(QRCode, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        generate_qr = self.generate_qr and self.generate_qr or False
        is_qr = self.is_qr and self.is_qr or False
        param.set_param('advanced_vat_invoice.generate_qr', generate_qr)
        param.set_param('advanced_vat_invoice.is_qr', is_qr)

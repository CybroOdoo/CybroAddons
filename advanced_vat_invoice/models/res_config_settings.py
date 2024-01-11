# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Athira P S (odoo@cybrosys.com)
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

###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Class foe adding qr code generation configuration"""
    _inherit = 'res.config.settings'

    generate_qr = fields.Selection(
        [('automatically', 'Generate QR Code when invoice validate/post'),
         ('manually', 'Manually Generate')], string="Generate",
        help="Select the way of generating QR code")
    is_qr = fields.Boolean(string="QR Code",
                           help="QR code Generation Configuration")

    @api.model
    def get_values(self):
        """Get the current configuration values."""
        res = super().get_values()
        res.update(
            generate_qr=self.env['ir.config_parameter'].sudo().get_param(
                'advanced_vat_invoice.generate_qr'),
            is_qr=self.env['ir.config_parameter'].sudo().get_param(
                'advanced_vat_invoice.is_qr'),
        )
        return res

    def set_values(self):
        """Set the configuration values."""
        super().set_values()
        param = self.env['ir.config_parameter'].sudo()
        generate_qr = self.generate_qr and self.generate_qr or False
        is_qr = self.is_qr and self.is_qr or False
        param.set_param('advanced_vat_invoice.generate_qr', generate_qr)
        param.set_param('advanced_vat_invoice.is_qr', is_qr)

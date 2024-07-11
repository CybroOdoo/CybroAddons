# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjana P V  (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
##############################################################################
from ast import literal_eval
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Extension of 'res.config.settings' for configuring delivery settings."""
    _inherit = 'res.config.settings'

    enable_delivery = fields.Boolean(string='Enable Order Types',
                                     help='This field is used to enable to set'
                                          'the order types in settings')
    delivery_methods = fields.Many2many('delivery.type',
                                        string='Order Types',
                                        help='Set the delivery methods')

    @api.model
    def get_values(self):
        """Get the values from settings."""
        res = super(ResConfigSettings, self).get_values()
        icp_sudo = self.env['ir.config_parameter'].sudo()
        partner_parameter = icp_sudo.get_param(
            'res.config.settings.enable_delivery')
        partner_parameters = icp_sudo.get_param(
            'res.config.settings.delivery_methods')
        res.update(enable_delivery=partner_parameter,
                   delivery_methods=[(6, 0, literal_eval(partner_parameters))
                                     ] if partner_parameters else False, )
        return res

    def set_values(self):
        """Set the values.The new values are stored in the configuration
        parameters."""
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'res.config.settings.enable_delivery', self.enable_delivery)
        self.env['ir.config_parameter'].sudo().set_param(
            'res.config.settings.delivery_methods',
            self.delivery_methods.ids)
        return res

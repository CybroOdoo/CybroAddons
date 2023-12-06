# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Jumana Haseen (odoo@cybrosys.com)
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
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    """This class inherits res.config.settings model and execute
    certain functions"""
    _inherit = 'res.config.settings'
    send_payslip_by_email = fields.Boolean(string="Automatic Send Payslip "
                                                  "By Mail", help="send "
                                                                  "payslip by"
                                                                  " email")

    @api.model
    def get_values(self):
        """This function retrieves configuration settings values"""
        res = super(ResConfigSettings, self).get_values()
        send_payslip_by_email = self.env[
            'ir.config_parameter'].sudo().get_param('send_payslip_by_email',
                                                    default=False)
        res.update(
            send_payslip_by_email=send_payslip_by_email)
        return res

    def set_values(self):
        """This function is used to set or update configuration values"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("send_payslip_"
                                                         "by_email",
                                                         self.send_payslip_by_email)

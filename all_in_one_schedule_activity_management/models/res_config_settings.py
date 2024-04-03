# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#     Author:Anjhana A K(<https://www.cybrosys.com>)
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
    _inherit = 'res.config.settings'

    notify_on_due_date = fields.Boolean('Notify on Due Date',
                                        help="Notify the due date",
                                        config_parameter="notify_on_due_date")
    notify_on_expiry = fields.Boolean('Notify on Expiry',
                                      help="Notify the Expiry date",
                                      config_parameter="notify_on_expiry")

    @api.model
    def get_values(self):
        """Returns a list of values for the given configuration fields"""
        res = super(ResConfigSettings, self).get_values()
        res['notify_on_due_date'] = self.env[
            'ir.config_parameter'].sudo().get_param('notify_on_due_date')
        res['notify_on_expiry'] = self.env[
            'ir.config_parameter'].sudo().get_param('notify_on_expiry')
        return res

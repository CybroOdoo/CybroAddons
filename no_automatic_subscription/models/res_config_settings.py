# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    """ Adding new fields to settings to stop the automatic subscription of
    customers """
    _inherit = 'res.config.settings'

    is_subscribe_recipients = fields.Boolean(string='Subscribe Recipients?',
                                             help="Do you want to subscribe the "
                                                  "recipients as followers")
    subscription_models_ids = fields.Many2many('ir.model',
                                               domain="[('is_mail_thread','=',True)]",
                                               related='company_id.subscription_models_ids',
                                               readonly=False,
                                               string='Subscription Models',
                                               help="The model you want to"
                                                    " restrict the subscription")

    @api.onchange('is_subscribe_recipients')
    def _onchange_is_subscribe_recipients(self):
        """ Onchange function to clear if is_subscribe_recipients is false """
        if not self.is_subscribe_recipients:
            self.subscription_models_ids = [fields.Command.clear()]

    @api.model
    def set_values(self):
        """ Sets the values that entered to the settings """
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'no_automatic_subscription.is_subscribe_recipients',
            self.is_subscribe_recipients)
        return res

    def get_values(self):
        """ Getting the values from the transient model """
        res = super(ResConfigSettings, self).get_values()
        with_user = self.env['ir.config_parameter'].sudo()
        subscribe_recipients = with_user.get_param(
            'no_automatic_subscription.is_subscribe_recipients')
        res.update(
            is_subscribe_recipients=subscribe_recipients,
        )
        return res

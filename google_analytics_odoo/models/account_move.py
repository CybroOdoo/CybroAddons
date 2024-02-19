# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul PI (<https://www.cybrosys.com>)
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
import requests
from odoo import models


class AccountMove(models.Model):
    """Extends the class  account moves by adding
        additional analytics tracking upon posting an invoice."""
    _inherit = 'account.move'

    def action_post(self):
        """Supering the function to send analytics data of invoice details.
            :return: Result of posting the account move."""
        res = super(AccountMove, self).action_post()
        enable_analytics = self.env[
            'ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.enable_analytics'),
        measurement_id = self.env['ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.measurement_id_analytics')
        api_secret = self.env['ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.api_secret')
        if enable_analytics:
            url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"
            data = {
                "client_id": str(self.partner_id.id),
                "events": [{
                    "name": "Invoices",
                    "params": {
                        "Number": self.name,
                        "Customer": self.partner_id.name,
                        "Amount": self.amount_total,
                    }
                }]
            }
            requests.post(url, json=data)
        return res

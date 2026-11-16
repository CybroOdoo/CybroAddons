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
#############################################################################
import logging
import requests
from odoo import models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    """Extends account moves by adding analytics tracking upon posting invoices."""
    _inherit = 'account.move'

    def action_post(self):
        """Sends Google Analytics event when invoices or bills are posted."""
        res = super().action_post()
        try:
            enable_analytics = self.env['ir.config_parameter'].sudo().get_str(
                'google_analytics_odoo.enable_analytics'
            )
            measurement_id = self.env['ir.config_parameter'].sudo().get_str(
                'google_analytics_odoo.measurement_id_analytics'
            )
            api_secret = self.env['ir.config_parameter'].sudo().get_str(
                'google_analytics_odoo.api_secret'
            )
            if enable_analytics and measurement_id and api_secret:
                url = (
                    f"https://www.google-analytics.com/mp/collect"
                    f"?measurement_id={measurement_id}&api_secret={api_secret}"
                )
                for move in self:
                    data = {
                        "client_id": str(move.partner_id.id),
                        "events": [{
                            "name": "Invoices",
                            "params": {
                                "Number": move.name,
                                "Customer": move.partner_id.name,
                                "Amount": move.amount_total,
                            }
                        }]
                    }
                    requests.post(url, json=data, timeout=5)
        except Exception as e:
            _logger.warning("Google Analytics Invoices posting error: %s", e)
        return res

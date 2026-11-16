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


class PurchaseOrder(models.Model):
    """Extends purchase orders by adding analytics tracking upon confirmation."""
    _inherit = 'purchase.order'

    def button_confirm(self):
        """Sends Google Analytics event when purchase orders are confirmed."""
        res = super().button_confirm()
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
                for po in self:
                    data = {
                        "client_id": str(po.partner_id.id),
                        "events": [{
                            "name": "Purchase_Order",
                            "params": {
                                "Number": po.name,
                                "Customer": po.partner_id.name,
                                "Amount": po.amount_total,
                            }
                        }]
                    }
                    requests.post(url, json=data, timeout=5)
        except Exception as e:
            _logger.warning("Google Analytics Purchase_Order confirmation error: %s", e)
        return res

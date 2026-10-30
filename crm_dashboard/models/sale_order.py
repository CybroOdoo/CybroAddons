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
from odoo import models


class SalesOrder(models.Model):
    """Extends sale order for overriding action confirm function"""
    _inherit = 'sale.order'

    def action_confirm(self):
        """Override the action_confirm method to change CRM Stage.
        Returns:
            dict: A dictionary containing the result of the original
            action_confirm method."""
        res = super().action_confirm()
        for order in self:
            if order.opportunity_id and order.team_id.crm_lead_state_id:
                order.opportunity_id.stage_id = order.team_id.crm_lead_state_id
        return res

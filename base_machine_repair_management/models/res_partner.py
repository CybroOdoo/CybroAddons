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


class ResPartner(models.Model):
    """This model inherits res.partner to show its repair requests."""
    _inherit = 'res.partner'

    def action_repair_requests(self):
        """Open the repair requests of the customer."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Machine Repair Requests',
            'view_mode': 'list',
            'res_model': 'machine.repair',
            'domain': [('customer_id', '=', self.id)],
            'context': "{'create': False}"
        }

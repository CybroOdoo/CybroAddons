"""Partners"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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
from odoo import models


class CustomerRepairRequests(models.Model):
    """This is used to return the partner's repair requests"""
    _inherit = 'res.partner'

    def action_repair_requests(self):
        """It returns the repair requests for the customers"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Machine Repair Requests',
            'view_mode': 'tree',
            'res_model': 'machine.repair',
            'domain': [('customer_id', '=', self.id)],
            'context': "{'create': False}"
        }

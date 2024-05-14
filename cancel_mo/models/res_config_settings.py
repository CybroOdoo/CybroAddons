# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V(<https://www.cybrosys.com>)
#
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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_cancel_inventory_moves = fields.Boolean(string="Cancel Inventory Moves",
                                               help="Whether to cancel the "
                                                    "inventory moves",
                                               config_parameter="cancel_mo"
                                                                ".is_cancel_inventory_moves")
    is_cancel_workorder = fields.Boolean(string="Cancel WorkOrder",
                                         help="Whether to cancel the work order",
                                         config_parameter="cancel_mo"
                                                          ".is_cancel_workorder")

    @api.onchange('is_cancel_inventory_moves', 'is_cancel_inventory_moves')
    def _onchange_cancel_mo(self):
        """Onchange function to write corresponding boolean fields in
        mrp_production"""
        mrp_orders = self.env['mrp.production'].search([('state', '=', 'done')])
        if self.is_cancel_inventory_moves:
            mrp_orders.write(
                {'cancel_inventory_moves': self.is_cancel_inventory_moves})
        if self.is_cancel_workorder:
            mrp_orders.write(
                {'cancel_workorder': self.is_cancel_workorder})

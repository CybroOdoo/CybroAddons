# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu K P (odoo@cybrosys.com)
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
###############################################################################
import logging
from odoo import api, fields, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    """Add new fields to configuration settings to Restrict stock warehouse
    for users."""
    _inherit = 'res.config.settings'

    group_user_warehouse_restriction = fields.Boolean(
        string="Restrict Stock Warehouse",
        implied_group='user_warehouse_restriction.'
                      'user_warehouse_restriction_group_user',
        help="Check if you want to restrict warehouse for users.")

    @api.onchange('group_user_warehouse_restriction')
    def _onchange_group_user_warehouse_restriction(self):
        """This method is triggered when the 'group_user_warehouse_restriction'
        field is changed. if it's true, assigns the current user as the
        allowed user of all existing warehouses."""
        rule = self.env.ref('user_warehouse_restriction.operation_type_rule_users', raise_if_not_found=False)
        if rule:
            rule.active = False
        try:
            warehouses = self.env['stock.warehouse'].search([])
            for warehouse in warehouses:
                if self.group_user_warehouse_restriction:
                    # Assign the current user to each warehouse
                    if not warehouse.user_ids:
                        warehouse.user_ids = [(6, 0, [self.env.user.id])]
                else:
                    # Clear the allowed users for each warehouse
                    warehouse.user_ids = [(5, 0, 0)]
        except AccessError as e:
            _logger.warning(f"Access error occurred: {e}")
        finally:
            if rule:
                rule.active = True

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

class PosConfig(models.Model):
    """
    Inherits pos.config to add restricted action configuration fields.
    """
    _inherit = 'pos.config'

    pos_restaurant_restriction = fields.Boolean(string="Restaurant Restriction", help="Enable restriction on some operations once the order has been sent to the kitchen")
    pos_orderline_quantity_update = fields.Boolean(string="Orderline Quantity Update", help="Require manager approval to update orderline quantity")
    pos_orderline_delete = fields.Boolean(string="Orderline Delete", help="Require manager approval to delete an orderline")
    pos_order_delete = fields.Boolean(string="Order Delete", help="Require manager approval to delete an order")
    pos_session_close = fields.Boolean(string="Session Close", help="Require manager approval to close the POS session")

    @api.model
    def _load_pos_data_read(self, records, config):
        """
        Extends loading process to include custom restriction fields in the POS frontend.
        """
        res = super()._load_pos_data_read(records, config)
        # Explicitly read our custom fields and update the result
        # This avoids breaking other fields if we used _load_pos_data_fields
        for record in res:
            config_rec = self.browse(record['id'])
            record.update({
                'pos_restaurant_restriction': config_rec.pos_restaurant_restriction,
                'pos_orderline_quantity_update': config_rec.pos_orderline_quantity_update,
                'pos_orderline_delete': config_rec.pos_orderline_delete,
                'pos_order_delete': config_rec.pos_order_delete,
                'pos_session_close': config_rec.pos_session_close,
            })
        return res

    @api.model
    def get_managers_for_approval(self, config_id):
        """
        Returns a list of managers (users in the POS Manager group) eligible for approvals.
        """
        config = self.browse(config_id)
        managers = []
        # Get users in POS Manager group
        pos_manager_group = self.env.ref('point_of_sale.group_pos_manager', raise_if_not_found=False)
        if pos_manager_group:
            for user in pos_manager_group.users:
                managers.append({'id': user.id, 'name': user.name})
        
        # Ensure Mitchell Admin is in the list
        if not any(m['name'] == 'Mitchell Admin' for m in managers):
            admin_user = self.env.ref('base.user_admin', raise_if_not_found=False)
            if admin_user:
                managers.append({'id': admin_user.id, 'name': admin_user.name})
        
        return managers

    @api.model
    def validate_manager_pin_for_restriction(self, config_id, manager_id, pin, action_type, product_id=False, old_qty=0.0, new_qty=0.0, order_ref=False):
        """
        Validates the manager's PIN for a restricted action and creates an audit log entry.
        """
        # We browse the manager (now a res.users record)
        manager = self.env['res.users'].browse(manager_id)
        if manager.exists() and manager.pos_security_pin == pin:
            # Create Log
            self.env['pos.action.log'].sudo().create({
                'user_id': self.env.user.id,
                'action_type': action_type,
                'approved_by': manager.id,
                'order_ref': order_ref,
                'product_id': product_id,
                'old_qty': old_qty,
                'new_qty': new_qty,
            })
            return {'approved': True}
        
        return {'approved': False}
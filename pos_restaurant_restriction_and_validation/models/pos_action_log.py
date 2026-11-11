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
from odoo import api, fields, models
from odoo.exceptions import UserError


class PosActionLog(models.Model):
    """
    Model to store logs of restricted actions performed in the Point of Sale.
    Tracks deletions and quantity updates that require manager approval.
    """
    _name = 'pos.action.log'
    _description = 'POS Restricted Action Log'
    _order = 'create_date desc'

    user_id = fields.Many2one(
        'res.users',
        help="The system user associated with this action"
    )
    cashier_name = fields.Char(
        string="Cashier",
        help="The cashier/employee who performed the restricted action"
    )
    action_type = fields.Selection([
        ('orderline_quantity_update', 'Quantity Updated'),
        ('orderline_delete', 'Orderline Deleted'),
        ('delete_order', 'Order Deleted'),
        ('session_close', 'Session Close'),
    ], help="The type of restricted action performed")
    approved_by = fields.Many2one(
        'res.users',
        help="The manager who approved this action"
    )
    order_ref = fields.Char(
        help="The POS order reference associated with this action"
    )
    product_id = fields.Many2one(
        'product.product',
        help="The product involved in the action (if applicable)"
    )
    old_qty = fields.Float("Old Quantity", help="The quantity before the update")
    new_qty = fields.Float("New Quantity", help="The quantity after the update")
    is_consumed = fields.Boolean(
        string="Consumed",
        default=False,
        readonly=True,
        help="Indicates whether this manager approval has been consumed"
    )

    def write(self, vals):
        """Prevents modification of audit log records."""
        if not self.env.su:
            raise UserError(self.env._("POS action audit logs cannot be modified."))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_superuser(self):
        """Prevents deletion of audit logs by non-superusers."""
        if not self.env.su:
            raise UserError(self.env._("POS action audit logs cannot be deleted."))

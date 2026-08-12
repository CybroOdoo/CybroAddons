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
from odoo import fields, models

class PosActionLog(models.Model):
    """
    Model to store logs of restricted actions performed in the Point of Sale.
    Tracks deletions and quantity updates that require manager approval.
    """
    _name = 'pos.action.log'
    _description = 'POS Restricted Action Log'
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', string="Employee", help="The employee who performed the restricted action")
    action_type = fields.Selection([
        ('orderline_quantity_update', 'Quantity Updated'),
        ('orderline_delete', 'Orderline Deleted'),
        ('delete_order', 'Order Deleted'),
        ('session_close', 'Session Close'),
    ], string="Action Type", help="The type of restricted action performed")
    approved_by = fields.Many2one('res.users', string="Approved By", help="The manager who approved this action")
    order_ref = fields.Char("Order Reference", help="The POS order reference associated with this action")
    product_id = fields.Many2one('product.product', string="Product", help="The product involved in the action (if applicable)")
    old_qty = fields.Float("Old Quantity", help="The quantity before the update")
    new_qty = fields.Float("New Quantity", help="The quantity after the update")
"""Home delivery for orders"""
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
from odoo import fields, models, _
from odoo import exceptions


class StockPicking(models.Model):
    """inheriting stock.picking to add additional fields"""
    _inherit = 'stock.picking'

    delivery_boy_id = fields.Many2one('hr.employee', string='Delivery Boy',
                                      help="delivery person")
    is_cancel_visibility = fields.Boolean(string='Cancel Button Visibility',
                                          default=False,
                                          help="cancel button visibility field")
    is_assign_visibility = fields.Boolean(string='Assign Button Visibility',
                                          default=False,
                                          help="assign button visibility field")
    is_broadcast_order = fields.Boolean(string='Broadcast Order',
                                        help="is it broadcast order or not")
    order_source = fields.Char(string='Source', default='sales',
                               help="order source")
    delivery_assign_date = fields.Date(string='Assign Date',
                                       help="Assigning date")
    delivery_state = fields.Selection(
        [('draft', 'Draft'), ('assigned', 'Assigned'),
         ('accept', 'Accept The Delivery'),
         ('picked', 'Picked'), ('reject', 'Reject The Delivery'),
         ('cancel', 'Canceled')],
        string='state', readonly=True, default='draft')
    payment_status = fields.Selection([('paid', 'Paid'), ('unpaid', 'Unpaid'),
                                       ], string='Payment Status',
                                      default='unpaid',
                                      help="payment status")
    distance = fields.Float(string='Distance', help="distance")
    reschedule_reason = fields.Text(string='Reschedule Reason',
                                    help="rescheduled reason")
    is_complete = fields.Boolean(default=False, string='Is Complete',
                                 help="Delivery complete status")

    def reset_to_draft(self):
        """Reset to draft"""
        self.delivery_state = 'draft'
        self.delivery_boy_id = False
        self.is_broadcast_order = False
        self.order_source = False
        self.delivery_assign_date = False
        self.distance = False
        self.payment_status = False
        self.is_complete = False

    def assign_delivery(self):
        """Assign delivery to the delivery person from order"""
        self.is_assign_visibility = True
        if len(self.delivery_boy_id):
            self.delivery_state = 'assigned'
        else:
            raise exceptions.ValidationError(_(
                "Please select a Delivery Person."
            ))

    def reschedule_delivery_person(self):
        """Reassigning the delivery person"""
        return {
            'res_model': 'delivery.person.reschedule',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_model_id': self.id}
        }

    def cancel_delivery(self):
        """Home delivery is cancelled and informing the customer by a mail"""
        self.delivery_state = 'cancel'
        self.is_cancel_visibility = True
        self.env.ref(
            'home_delivery_system.email_template_cancel_delivery_order').send_mail(
            self.id, force_send=True)

    def picking_delivery(self):
        """Changes the state while delivery is picked the person"""
        self.delivery_state = 'picked'
        self.env.ref(
            'home_delivery_system.email_template_cancel_delivery_picking').send_mail(
            self.id, force_send=True)

    def delivery_available(self):
        """Writing the state of delivery orders while the delivery is accept"""
        assigned_delivery_orders = self.env['stock.picking'].search(
            [('delivery_boy_id', '!=', False),
             ('delivery_boy_id.user_id', '=', self.env.user.id)])
        if len(assigned_delivery_orders) > 1:
            for rec in assigned_delivery_orders:
                rec.write({
                    'delivery_state': 'accept'
                })
        else:
            assigned_delivery_orders.write({
                'delivery_state': 'accept'
            })
        return True

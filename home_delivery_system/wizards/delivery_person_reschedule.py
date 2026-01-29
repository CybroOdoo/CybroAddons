# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj (odoo@cybrosys.com)
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
from odoo import fields, models


class DeliveryPersonReschedule(models.TransientModel):
    """Reassigning delivery person"""
    _name = 'delivery.person.reschedule'
    _description = 'Reschedule delivery person'

    delivery_boy_id = fields.Many2one('hr.employee', string='Delivery Boy',
                                      help="The person who deliver the goods",
                                      required=True)
    reschedule_reason = fields.Text(string='Reschedule Reason',
                                    help="Reason for re-assigning the person",
                                    required=True)

    def reschedule_action(self):
        """Reassigning the delivery person to the order"""
        self.env['stock.picking'].browse(
            self.env.context.get('params')['id']).write({
            'delivery_boy_id': self.delivery_boy_id,
            'reschedule_reason': self.reschedule_reason
        })

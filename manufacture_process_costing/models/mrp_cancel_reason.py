# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class MrpCancelReason(models.Model):
    """The class represents a new model mrp.cancel.reason"""
    _name = 'mrp.cancel.reason'
    _description = 'Mrp Cancel Reason'
    _rec_name = 'manufacturing_id'
    _order = "id desc"

    reason_for_cancel = fields.Text(
        string='Reason For Cancel',
        help='Provide a reason for the cancellation of the manufacturing order')
    manufacturing_id = fields.Many2one('mrp.production',
                                       required=True,
                                       string='Manufacture Order',
                                       help='Corresponding manufacturing order')
    date = fields.Datetime(
        string='Cancel Date', default=fields.Datetime.now(),
        help='The date and time of cancelling the manufacturing order')
    cancelled_by_id = fields.Many2one(
        'res.users',
        string='Cancelled By',
        default=lambda self: self.env.user.id,
        help='The corresponding user who is cancelling the order')

    def action_button_cancel(self):
        """Calls the function action_cancel() from mrp production"""
        self.manufacturing_id.action_cancel()

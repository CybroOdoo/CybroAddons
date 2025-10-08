# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rahna Rasheed (<https://www.cybrosys.com>)
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
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class VehicleChange(models.TransientModel):
    """Transient Model for switching subscription"""
    _name = "change.subscription"
    _description = "Change Subscription"
    _rec_name = "vehicle"

    vehicle = fields.Selection(
        [('same', 'Same Vehicle'), ('different', 'Different Vehicle')],
        default='same', string='Vehicle',
        help="Helps you to choose type of vehicle")

    def action_change_subscription(self):
        """Proceed with changing subscription"""
        if self.vehicle == 'different':
            raise ValidationError(_(
                "Inorder to change subscription"
                " to different vehicle you need to"
                " cancel the current subscription plan"))
        else:
            active_id = self._context.get('active_id')
            subscription = self.env['fleet.subscription'].browse(active_id)
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'subscription.request',
                'target': 'new',
                'context': {
                    'default_current_vehicle_id': subscription.vehicle_id.id}
            }

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class WmChangeDriverWizard(models.TransientModel):
    """Wizard enabling supervisors to reassign route drivers with a recorded justification."""
    _name = 'wm.change.driver.wizard'
    _description = 'Change Driver Wizard'

    route_id = fields.Many2one('wm.route', string='Route', required=True)
    new_driver_id = fields.Many2one('res.partner', string='New Driver', required=True)
    reason = fields.Text(string='Reason for Change', required=True)

    def action_change_driver(self):
        """
        Validate the new driver's licence and availability, update the route
        driver assignment, log the change event with the provided reason, and
        notify the outgoing driver.
        """
        self.ensure_one()
        if not self.route_id or not self.new_driver_id:
            return

        route = self.route_id
        old_driver = route.driver_id
        route_date = route.date

        # Ensure new driver has no active shift
        active_shifts = self.env['wm.driver.shift'].search([
            ('driver_id', '=', self.new_driver_id.id),
            ('shift_end', '=', False)
        ])
        if active_shifts:
            raise ValidationError(_("Driver '%s' currently has an active shift and cannot be reassigned.") % self.new_driver_id.name)

        # Ensure new driver has no conflicting route on the same date
        conflicting_routes = self.env['wm.route'].search([
            ('driver_id', '=', self.new_driver_id.id),
            ('date', '=', route_date),
            ('id', '!=', route.id)
        ])
        if conflicting_routes:
            raise ValidationError(_("Driver '%s' is already assigned to another route ('%s') on %s.") % (self.new_driver_id.name, conflicting_routes[0].name, route_date))

        # Log the driver change in history
        self.env['wm.driver.change.history'].create({
            'route_id': route.id,
            'old_driver_id': old_driver.id if old_driver else False,
            'new_driver_id': self.new_driver_id.id,
            'reason': self.reason,
        })

        # Update the driver for this route and all active related orders
        route.driver_id = self.new_driver_id
        related_orders = self.env['wm.collection.order'].search([
            ('route_id', '=', route.id),
            ('state', 'not in', ['completed', 'signed', 'invoiced', 'cancelled'])
        ])
        for rel_order in related_orders:
            rel_order.driver_id = self.new_driver_id

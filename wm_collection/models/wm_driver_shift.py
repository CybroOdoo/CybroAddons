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
from odoo import _, api, fields, models


class WMDriverShift(models.Model):
    """Tracks driver shift logs, operating hours, and route assignments for collection operations."""
    _name = 'wm.driver.shift'
    _description = 'Driver Shift'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'wm.audit.mixin']

    name = fields.Char(string='Reference', compute='_compute_name', store=True, tracking=True)
    driver_id = fields.Many2one('res.partner', string='Driver', required=True, tracking=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, tracking=True)
    shift_start = fields.Datetime(string='Shift Start', required=True, tracking=True)
    shift_end = fields.Datetime(string='Shift End', tracking=True)
    hours_driven = fields.Float(string='Hours Driven', compute='_compute_hours_driven')
    route_ids = fields.One2many('wm.route', 'shift_id', string='Collection Routes')
    route_count = fields.Integer(string='Route Count', compute='_compute_route_count')

    @api.depends('route_ids')
    def _compute_route_count(self):
        for record in self:
            record.route_count = len(record.route_ids)

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        """
        Auto-assign the vehicle's designated driver to the shift
        when a vehicle is selected.
        """
        self.driver_id = self.vehicle_id.driver_id if self.vehicle_id else False

    def action_view_routes(self):
        self.ensure_one()
        return {
            'name': _('Collection Routes'),
            'type': 'ir.actions.act_window',
            'res_model': 'wm.route',
            'view_mode': 'list,form',
            'domain': [('shift_id', '=', self.id)],
            'context': {'default_shift_id': self.id},
        }

    @api.depends('driver_id', 'shift_start')
    def _compute_name(self):
        """
        Auto-generate the shift display name from the driver name and date
        range, ensuring shift records have descriptive identifiers in list
        views and timesheets.
        """
        for record in self:
            if record.driver_id and record.shift_start:
                record.name = f"{record.driver_id.name} - {record.shift_start}"
            else:
                record.name = 'New'

    @api.depends('shift_start', 'shift_end')
    def _compute_hours_driven(self):
        """
        Calculate total driving hours from shift start and end datetimes, used
        for driver performance reporting and overtime threshold monitoring.
        Not stored: open shifts are measured against the current time, which
        would freeze at the first computation if the value were stored.
        """
        for record in self:
            if record.shift_start and record.shift_end:
                delta = record.shift_end - record.shift_start
                record.hours_driven = delta.total_seconds() / 3600.0
            elif record.shift_start:
                delta = fields.Datetime.now() - record.shift_start
                record.hours_driven = delta.total_seconds() / 3600.0
            else:
                record.hours_driven = 0.0

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
from odoo.exceptions import UserError


class WmAddStatusLogWizard(models.TransientModel):
    """Wizard to record a stop status log entry for a collection order."""
    _name = 'wm.add.status.log.wizard'
    _description = 'Log Driver Stop Status'

    order_id = fields.Many2one(
        'wm.collection.order',
        string='Collection Order',
        required=True,
        readonly=True,
    )
    status = fields.Selection([
        ('en_route', 'En Route'),
        ('arrived', 'Arrived'),
        ('started', 'Started Work'),
        ('lifted', 'Lifted Container'),
        ('weighed', 'Weighed Waste'),
        ('completed', 'Completed Collection'),
        ('flagged', 'Flagged Issue'),
    ], string='Status Event', required=True, default='en_route')
    timestamp = fields.Datetime(
        string='Timestamp',
        required=True,
        default=fields.Datetime.now,
    )
    latitude = fields.Float(string='Latitude', digits=(10, 7))
    longitude = fields.Float(string='Longitude', digits=(10, 7))
    note = fields.Text(string='Driver Notes', help='Optional notes describing the progress or issue.')
    photo = fields.Binary(string='Photo Proof', attachment=True)

    @api.model
    def default_get(self, fields_list):
        """Auto-populate latitude and longitude from the vehicle's latest telematics position or collection point."""
        res = super().default_get(fields_list)
        order_id = res.get('order_id') or self.env.context.get('default_order_id')
        if order_id:
            order = self.env['wm.collection.order'].browse(order_id)
            if order.exists():
                lat, lng = self._get_default_location(order)
                if lat or lng:
                    res.setdefault('latitude', lat)
                    res.setdefault('longitude', lng)
        return res

    @api.onchange('order_id')
    def _onchange_order_id(self):
        """Update coordinates when collection order selection changes."""
        if self.order_id:
            lat, lng = self._get_default_location(self.order_id)
            if lat or lng:
                self.latitude = lat
                self.longitude = lng

    def _get_default_location(self, order):
        """Helper to get location from vehicle telematics event or collection point."""
        lat = 0.0
        lng = 0.0
        # 1. Try vehicle telematics latest position if available
        if order.vehicle_id and 'wm.telematics.event' in self.env:
            latest_event = self.env['wm.telematics.event'].sudo().search([
                ('vehicle_id', '=', order.vehicle_id.id),
                ('latitude', '!=', 0.0),
                ('longitude', '!=', 0.0),
            ], order='event_datetime desc, id desc', limit=1)
            if latest_event:
                lat = latest_event.latitude
                lng = latest_event.longitude

        # 2. Fall back to Collection Point coordinates
        if (not lat or not lng) and order.collection_point_id:
            lat = order.collection_point_id.latitude or 0.0
            lng = order.collection_point_id.longitude or 0.0

        return lat, lng

    def action_confirm(self):
        """Create the stop status log record and append it to the collection order."""
        self.ensure_one()
        if not self.order_id:
            raise UserError(_("No Collection Order selected."))

        self.env['wm.collection.order.status.log'].log_stop_event(
            order=self.order_id,
            status=self.status,
            driver=self.env.user,
            timestamp=self.timestamp,
            latitude=self.latitude or 0.0,
            longitude=self.longitude or 0.0,
            note=self.note or '',
            photo=self.photo or False,
        )
        return {'type': 'ir.actions.act_window_close'}

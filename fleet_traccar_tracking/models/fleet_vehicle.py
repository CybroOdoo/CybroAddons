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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import timedelta
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

KNOTS_TO_KMH = 1.852


class FleetVehicle(models.Model):
    """Extends fleet.vehicle with Traccar GPS tracking fields
       and position/trip synchronization methods."""
    _inherit = 'fleet.vehicle'

    activate_traccar = fields.Boolean(
        string='Activate Traccar',
        help='Enable GPS tracking for this vehicle via Traccar.',
    )
    traccar_unique_id = fields.Char(
        string='Device Identifier',
        help='uniqueId from Traccar (phone IMEI or custom string). Must match exactly.',
        index=True,
    )
    traccar_device_id = fields.Many2one(
        'fleet.traccar.device',
        string='Traccar Device',
        help='Linked Traccar device record.',
        ondelete='set null',
    )

    last_latitude = fields.Float(string='Device Latitude', digits=(10, 7), readonly=True)
    last_longitude = fields.Float(string='Device Longitude', digits=(10, 7), readonly=True)
    last_speed = fields.Float(string='Speed (km/h)', readonly=True)
    last_battery = fields.Float(string='Battery (%)', readonly=True)
    last_accuracy = fields.Float(string='Accuracy (m)', readonly=True)
    last_update = fields.Datetime(string='Last Trip Update', readonly=True)
    last_route_update = fields.Datetime(string='Last Route Update', readonly=True)

    current_status = fields.Selection([
        ('running', 'Running'),
        ('idle', 'Idle'),
        ('offline', 'Offline'),
    ], string='Is Online', default='offline', readonly=True)

    trip_count = fields.Integer(compute='_compute_trip_count', string='Trips')
    event_count = fields.Integer(compute='_compute_event_count', string='Events')
    position_count = fields.Integer(compute='_compute_position_count', string='Positions')

    def _compute_trip_count(self):
        """Compute the total number of trips linked to this vehicle."""
        Trip = self.env['fleet.traccar.trip']
        for rec in self:
            rec.trip_count = Trip.search_count([('vehicle_id', '=', rec.id)])

    def _compute_event_count(self):
        """Compute the total number of events linked to this vehicle."""
        Event = self.env['fleet.traccar.event']
        for rec in self:
            rec.event_count = Event.search_count([('vehicle_id', '=', rec.id)])

    def _compute_position_count(self):
        """Compute the total number of positions recorded for this vehicle."""
        Position = self.env['fleet.traccar.position']
        for rec in self:
            rec.position_count = Position.search_count([('vehicle_id', '=', rec.id)])

    def _get_traccar_config(self):
        """Fetch the Traccar configuration record.
            Raises UserError if no configuration is found."""
        config = self.env['fleet.traccar.config'].search([], limit=1)
        if not config:
            raise UserError(_('No Traccar configuration found. Please configure it under Fleet > Configuration > Traccar Configuration.'))
        return config

    def _resolve_traccar_device_id(self, config):
        """
        Return the integer Traccar device ID for this vehicle.
        Prefers traccar_device_id.traccar_id, falls back to looking up by unique_id.
        """
        self.ensure_one()
        if self.traccar_device_id and self.traccar_device_id.traccar_id:
            return self.traccar_device_id.traccar_id

        if self.traccar_unique_id:
            devices = config._api_get('/api/devices')
            for d in devices:
                if d.get('uniqueId') == self.traccar_unique_id:
                    # auto-link
                    dev = self.env['fleet.traccar.device'].search([('traccar_id', '=', d['id'])], limit=1)
                    if not dev:
                        dev = self.env['fleet.traccar.device'].create({
                            'name': d['name'],
                            'traccar_id': d['id'],
                            'unique_id': d['uniqueId'],
                        })
                    self.traccar_device_id = dev
                    return d['id']

        raise UserError(_('Vehicle "%s" has no Traccar device linked. Set "Device Identifier" and save.') % self.name)

    def action_refresh_location(self):
        """Fetch & update the latest GPS fix for this single vehicle."""
        self.ensure_one()
        config = self._get_traccar_config()
        device_int_id = self._resolve_traccar_device_id(config)
        positions = config._api_get('/api/positions', params={'deviceId': device_int_id})
        if not positions:
            raise UserError(_('No current position available for this device.'))
        self._process_position(positions[0])
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Location Updated'),
                'message': _('Position refreshed for %s.') % self.name,
                'type': 'success',
                'sticky': False,
            },
        }

    def action_view_current_location(self):
        """Open a map popup showing the vehicle's last known position."""
        self.ensure_one()
        if not self.last_latitude and not self.last_longitude:
            raise UserError(_('No location data available yet. Click "Refresh Location" first.'))
        config = self._get_traccar_config()
        if config.map_provider == 'google' and config.google_maps_api_key:
            map_url = (
                f'https://www.google.com/maps?q={self.last_latitude},{self.last_longitude}'
                f'&key={config.google_maps_api_key}'
            )
        else:
            map_url = f'https://www.openstreetmap.org/?mlat={self.last_latitude}&mlon={self.last_longitude}&zoom=15'
        return {
            'type': 'ir.actions.act_url',
            'url': map_url,
            'target': 'new',
        }

    def action_fetch_trips(self):
        """Fetch trips from Traccar /api/reports/trips for the last 30 days."""
        self.ensure_one()
        config = self._get_traccar_config()
        device_int_id = self._resolve_traccar_device_id(config)

        now = fields.Datetime.now()
        from_dt = (now - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
        to_dt = now.strftime('%Y-%m-%dT%H:%M:%SZ')

        trips_data = config._api_get_safe('/api/reports/trips', params={
            'deviceId': device_int_id,
            'from': from_dt,
            'to': to_dt,
        })

        if not trips_data:
            raise UserError(_('No trips found in Traccar for the last 30 days. Make sure the device has moved.'))

        Trip = self.env['fleet.traccar.trip']
        imported = 0
        for t in trips_data:
            # Use startTime+deviceId as unique key to avoid duplicates
            start_time = self._parse_traccar_datetime(t.get('startTime'))
            if not start_time:
                continue
            existing = Trip.search([
                ('vehicle_id', '=', self.id),
                ('start_time', '=', start_time),
            ], limit=1)
            if existing:
                continue

            end_time = self._parse_traccar_datetime(t.get('endTime'))
            distance_m = t.get('distance', 0) or 0
            avg_speed_knots = t.get('averageSpeed', 0) or 0
            max_speed_knots = t.get('maxSpeed', 0) or 0

            Trip.create({
                'vehicle_id': self.id,
                'device_id': self.traccar_device_id.id if self.traccar_device_id else False,
                'start_time': start_time,
                'end_time': end_time,
                'start_lat': t.get('startLat', 0),
                'start_lng': t.get('startLon', 0),
                'end_lat': t.get('endLat', 0),
                'end_lng': t.get('endLon', 0),
                'start_address': t.get('startAddress', ''),
                'end_address': t.get('endAddress', ''),
                'distance': round(distance_m / 1000, 2),
                'avg_speed': round(avg_speed_knots * KNOTS_TO_KMH, 1),
                'max_speed': round(max_speed_knots * KNOTS_TO_KMH, 1),
            })
            imported += 1

        return {
            'type': 'ir.actions.act_window',
            'name': _('Trip History'),
            'res_model': 'fleet.traccar.trip',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {
                'search_default_vehicle_id': self.id,
                'display_notification': {
                    'title': _('Trips Imported'),
                    'message': _('%d new trip(s) imported from Traccar.') % imported,
                    'type': 'success',
                }
            },
        }

    def action_fetch_routes(self):
        """Fetch last 24h route positions from Traccar for this vehicle."""
        self.ensure_one()
        config = self._get_traccar_config()
        device_int_id = self._resolve_traccar_device_id(config)
        now = fields.Datetime.now()
        from_dt = (now - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%SZ')
        to_dt = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        positions = config._api_get_safe('/api/positions', params={
            'deviceId': device_int_id,
            'from': from_dt,
            'to': to_dt,
        })
        if positions:
            self._import_positions(positions)
            self.last_route_update = now
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Routes Fetched'),
                'message': _('%d position(s) imported for %s.') % (len(positions or []), self.name),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_view_device_summary(self):
        """Open the form view of the linked Traccar device.
            Raises UserError if no device is linked to this vehicle."""
        self.ensure_one()
        if not self.traccar_device_id:
            raise UserError(_('No Traccar device linked to this vehicle.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Device Summary'),
            'res_model': 'fleet.traccar.device',
            'res_id': self.traccar_device_id.id,
            'view_mode': 'form',
        }

    def action_view_trips(self):
        """Open the list of trips associated with this vehicle."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Trips'),
            'res_model': 'fleet.traccar.trip',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
        }

    def action_view_events(self):
        """Open the list of events associated with this vehicle."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Events'),
            'res_model': 'fleet.traccar.event',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
        }

    @staticmethod
    def _parse_traccar_datetime(dt_str):
        """Convert Traccar ISO datetime string to Odoo-compatible format.
        Handles: '2026-03-11T08:47:41.177+00:00', '2026-03-11T08:47:41Z', etc.
        """
        if not dt_str:
            return False
        try:
            from datetime import datetime, timezone
            dt_str = dt_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            try:
                import re
                clean = re.sub(r'\.\d+', '', dt_str)  # remove milliseconds
                clean = re.sub(r'[T]', ' ', clean)      # replace T with space
                clean = re.sub(r'[Z+].*$', '', clean)   # remove timezone
                return clean.strip()
            except Exception:
                return False

    def _process_position(self, pos_data):
        """Update vehicle fields from a single Traccar position dict."""
        attrs = pos_data.get('attributes') or {}
        speed_knots = pos_data.get('speed', 0) or 0
        speed_kmh = round(speed_knots * KNOTS_TO_KMH, 1)

        from datetime import datetime
        now_utc = datetime.utcnow()
        fix_str = pos_data.get('deviceTime') or pos_data.get('fixTime') or pos_data.get('serverTime')
        fix_dt = None
        if fix_str:
            parsed = self._parse_traccar_datetime(fix_str)
            if parsed:
                try:
                    fix_dt = datetime.strptime(parsed, '%Y-%m-%d %H:%M:%S')
                except Exception:
                    pass

        minutes_since_update = ((now_utc - fix_dt).total_seconds() / 60) if fix_dt else 9999

        if speed_kmh > 2:
            status = 'running'
        elif minutes_since_update <= 10:
            status = 'idle'
        else:
            status = 'offline'

        vals = {
            'last_latitude': pos_data.get('latitude', 0),
            'last_longitude': pos_data.get('longitude', 0),
            'last_speed': speed_kmh,
            'last_battery': attrs.get('batteryLevel', 0),
            'last_accuracy': pos_data.get('accuracy', 0),
            'last_update': self._parse_traccar_datetime(pos_data.get('deviceTime') or pos_data.get('fixTime')),
            'current_status': status,
        }
        self.write(vals)

        # Save position record (skip duplicates)
        pos_id = pos_data.get('id')
        if pos_id:
            existing = self.env['fleet.traccar.position'].search([
                ('traccar_position_id', '=', pos_id),
                ('vehicle_id', '=', self.id),
            ], limit=1)
            if not existing:
                self.env['fleet.traccar.position'].create({
                    'vehicle_id': self.id,
                    'device_id': self.traccar_device_id.id if self.traccar_device_id else False,
                    'traccar_position_id': pos_id,
                    'fix_time': self._parse_traccar_datetime(pos_data.get('fixTime')),
                    'server_time': self._parse_traccar_datetime(pos_data.get('serverTime')),
                    'latitude': pos_data.get('latitude', 0),
                    'longitude': pos_data.get('longitude', 0),
                    'altitude': pos_data.get('altitude', 0),
                    'speed': speed_kmh,
                    'course': pos_data.get('course', 0),
                    'accuracy': pos_data.get('accuracy', 0),
                    'battery_level': attrs.get('batteryLevel', 0),
                    'motion': bool(attrs.get('motion')),
                    'odometer': attrs.get('odometer', 0),
                    'attributes': attrs,
                })

    def _import_positions(self, positions_data):
        """Bulk import a list of position dicts."""
        for p in positions_data:
            try:
                self._process_position(p)
            except Exception as e:
                _logger.warning('Error importing position for %s: %s', self.name, e)

    @api.model
    def action_sync_all_positions(self):
        """Called by cron: sync latest positions for all active Traccar vehicles."""
        config = self.env['fleet.traccar.config'].search([], limit=1)
        if not config or not config.traccar_url:
            _logger.warning('Traccar sync skipped: no configuration found.')
            return

        vehicles = self.search([('activate_traccar', '=', True)])
        if not vehicles:
            return

        positions = config._api_get_safe('/api/positions') or []
        pos_by_device = {p.get('deviceId'): p for p in positions}

        for vehicle in vehicles:
            try:
                dev_id = None
                if vehicle.traccar_device_id and vehicle.traccar_device_id.traccar_id:
                    dev_id = vehicle.traccar_device_id.traccar_id

                if dev_id and dev_id in pos_by_device:
                    vehicle._process_position(pos_by_device[dev_id])
                elif vehicle.current_status != 'offline':
                    # Device not in current positions response → mark offline
                    vehicle.current_status = 'offline'
            except Exception as e:
                _logger.error('Traccar sync error for vehicle %s: %s', vehicle.name, e)

        config.last_sync = fields.Datetime.now()
        _logger.info('Traccar position sync complete: %d vehicles processed.', len(vehicles))

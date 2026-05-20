# -*- coding: utf-8 -*-
#############################################################################
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

"""
REST API controller for Ignition SCADA → Odoo data ingestion.

Endpoints
---------
POST /api/scada/push
    Receive one or many sensor readings from Ignition.
    Body (JSON):
    {
        "api_key": "YOUR_API_KEY",
        "readings": [
            {
                "tag_path": "[default]Well1/Pressure/PSI",
                "value": 2450.5,
                "quality": "good",
                "timestamp": "2026-04-14T08:30:00"   // optional ISO-8601
            },
            ...
        ]
    }
    Returns:
    {
        "status": "ok",
        "processed": 3,
        "skipped": 0,
        "errors": []
    }

GET /api/scada/tags
    Returns all active tag configurations so Ignition can discover
    which tag paths are registered without manual setup.
    Header: X-SCADA-API-Key: YOUR_API_KEY

GET /api/scada/equipment
    Returns live values for all oil equipment — for Ignition to display
    Odoo ERP data on its HMI screens.

Authentication
--------------
Every request must carry the API key either as a JSON body field
("api_key") or as the HTTP header "X-SCADA-API-Key".
The key is configured in Odoo Settings → SCADA Integration.
"""

import json
import logging
from datetime import datetime

from odoo import SUPERUSER_ID, http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

# Sentinel for missing config
_NOT_SET = object()


def _get_api_key():
    """Retrieve the configured SCADA API key from ir.config_parameter."""
    return request.env['ir.config_parameter'].sudo().get_param(
        'oil_erp_scada.api_key', default=''
    )


def _auth(req_key):
    """Return True if the provided key matches the stored key."""
    stored = _get_api_key()
    if not stored:
        _logger.warning('SCADA API key not configured — all requests rejected.')
        return False
    return req_key == stored


def _bind_acting_user():
    """Bind request.env to a real user so downstream defaults (reported_by,
    create_uid, mail.thread followers, etc.) can resolve a singleton — under
    auth='none' request.env.user is empty and every framework default that
    reads self.env.user blows up with "Expected singleton: res.users()".
    """
    admin = request.env.ref('base.user_admin', raise_if_not_found=False)
    if admin:
        request.update_env(user=admin.id)
        return
    internal = request.env['res.users'].sudo().search(
        [('share', '=', False), ('active', '=', True)], limit=1,
    )
    request.update_env(user=internal.id if internal else SUPERUSER_ID)


def _json_response(data, status=200):
    return Response(
        json.dumps(data),
        status=status,
        content_type='application/json',
    )


class ScadaApiController(http.Controller):

    # ── POST /api/scada/push ───────────────────────────────────────────────
    @http.route('/api/scada/push', type='http', auth='none',
                methods=['POST'], csrf=False)
    def push_readings(self, **kwargs):
        """
        Main ingestion endpoint.  Ignition calls this whenever tag values
        change (or on a fixed interval).  Handles batch payloads.
        """
        try:
            body = json.loads(request.httprequest.data or '{}')
        except json.JSONDecodeError as e:
            return _json_response({'status': 'error', 'message': f'Invalid JSON: {e}'}, 400)

        # Auth
        api_key = body.get('api_key') or request.httprequest.headers.get('X-SCADA-API-Key', '')
        if not _auth(api_key):
            return _json_response({'status': 'error', 'message': 'Unauthorized'}, 401)
        _bind_acting_user()

        readings = body.get('readings', [])
        if not isinstance(readings, list):
            return _json_response({'status': 'error', 'message': '"readings" must be a list'}, 400)

        processed, skipped, errors = 0, 0, []

        Tag = request.env['scada.tag'].sudo()

        # Group readings by (tag_path, timestamp)
        from collections import defaultdict
        grouped = defaultdict(list)
        for item in readings:
            tag_path = item.get('tag_path', '').strip()
            ts = item.get('timestamp')
            grouped[(tag_path, ts)].append(item)

        for (tag_path, ts_raw), items in grouped.items():
            if not tag_path:
                skipped += len(items)
                continue

            tag = Tag.search([('tag_path', '=', tag_path), ('active', '=', True)], limit=1)
            if not tag:
                skipped += len(items)
                errors.append(f'Tag not registered: {tag_path}')
                continue

            # Parse optional timestamp
            ts = None
            if ts_raw:
                try:
                    ts = datetime.fromisoformat(str(ts_raw).replace('Z', '+00:00'))
                    ts = ts.replace(tzinfo=None)
                except (ValueError, TypeError):
                    ts = None

            measurements = {}
            production_data = {}
            quality = 'good'

            for item in items:
                # measurement_type is expected in the payload to identify which measurement this is.
                # If not provided, skip it, because we don't know what this value is for.
                measurement_type = item.get('measurement_type')
                if not measurement_type:
                    skipped += 1
                    errors.append(
                        f'{tag_path}: measurement_type is required for '
                        f'multi-measurement tags.'
                    )
                    continue

                if measurement_type == 'production':
                    scada_key = item.get('scada_key')
                    if scada_key:
                        production_data[scada_key] = float(item.get('value', 0.0))
                else:
                    measurements[measurement_type] = float(item.get('value', 0.0))

                # If any item in the payload has bad/uncertain quality, mark the whole payload
                item_q = item.get('quality', 'good')
                if item_q in ('bad', 'uncertain'):
                    quality = item_q

            if not measurements and not production_data:
                continue

            try:
                with request.env.cr.savepoint():
                    tag.process_reading(
                        measurements=measurements,
                        quality=quality,
                        timestamp=ts,
                        production_data=production_data
                    )
                processed += len(items)
            except Exception as e:
                _logger.exception('Error processing SCADA reading for %s', tag_path)
                errors.append(f'{tag_path}: {e}')
                skipped += len(items)

        return _json_response({
            'status': 'ok',
            'processed': processed,
            'skipped': skipped,
            'errors': errors,
        })

    # ── POST /api/scada/push_device ──────────────────────────────────────
    @http.route('/api/scada/push_device', type='http', auth='none',
                methods=['POST'], csrf=False)
    def push_device_readings(self, **kwargs):
        """
        Device-centric batch ingestion endpoint.
        Accepts multiple values for one or more devices in a single call.
        Each value is mapped to its corresponding SCADA tag by tag_type or
        tag_path and written to the correct field on the target record.

        Body (JSON):
        {
            "api_key": "YOUR_API_KEY",
            "devices": [
                {
                    "device_type": "equipment",
                    "device_id": 5,
                    "device_name": "Pump-001",
                    "timestamp": "2026-04-14T08:30:00",
                    "quality": "good",
                    "values": {
                        "pressure": 2450.5,
                        "temperature": 185.3,
                        "vibration": 0.3
                    }
                },
                {
                    "device_type": "tank",
                    "device_id": 3,
                    "values": {
                        "level": 5420.0,
                        "temperature": 145.2
                    }
                }
            ]
        }

        "values" keys can be:
          - tag_type names (pressure, temperature, level, flow_rate, etc.)
          - full Ignition tag paths ("[default]Well1/Pressure/PSI")

        Returns:
        {
            "status": "ok",
            "results": [
                {"device_type": "equipment", "device_id": 5, "processed": 2, "skipped": 0, "errors": []},
                ...
            ],
            "total_processed": 4,
            "total_skipped": 0
        }
        """
        try:
            body = json.loads(request.httprequest.data or '{}')
        except json.JSONDecodeError as e:
            return _json_response({'status': 'error', 'message': f'Invalid JSON: {e}'}, 400)

        # Auth
        api_key = body.get('api_key') or request.httprequest.headers.get('X-SCADA-API-Key', '')
        if not _auth(api_key):
            return _json_response({'status': 'error', 'message': 'Unauthorized'}, 401)
        _bind_acting_user()

        devices = body.get('devices', [])
        if not isinstance(devices, list):
            return _json_response({'status': 'error', 'message': '"devices" must be a list'}, 400)

        Tag = request.env['scada.tag'].sudo()
        results = []
        total_processed = 0
        total_skipped = 0

        _model_map = {
            'equipment': 'maintenance.equipment',
            'workcenter': 'mrp.workcenter',
            'project': 'project.project',
        }

        for device in devices:
            device_type = device.get('device_type', '').strip()
            device_id = device.get('device_id')
            device_name = device.get('device_name', '').strip()
            values = device.get('values', {})
            quality = device.get('quality', 'good')

            if not device_type or not values:
                total_skipped += 1
                results.append({
                    'device_type': device_type,
                    'device_id': device_id,
                    'processed': 0,
                    'skipped': 1,
                    'errors': ['Missing device_type or values'],
                })
                continue

            # Resolve device_id from device_name if not provided
            if not device_id and device_name:
                model_name = _model_map.get(device_type)
                if model_name:
                    rec = request.env[model_name].sudo().search(
                        [('name', '=', device_name)], limit=1
                    )
                    if rec:
                        device_id = rec.id

            if not device_id:
                total_skipped += 1
                results.append({
                    'device_type': device_type,
                    'device_id': None,
                    'processed': 0,
                    'skipped': 1,
                    'errors': [f'Cannot resolve device: type={device_type}, name={device_name}'],
                })
                continue

            # Parse optional timestamp
            ts = None
            if device.get('timestamp'):
                try:
                    ts = datetime.fromisoformat(
                        str(device['timestamp']).replace('Z', '+00:00')
                    )
                    ts = ts.replace(tzinfo=None)
                except (ValueError, TypeError):
                    ts = None

            try:
                result = Tag.process_device_readings(
                    device_type=device_type,
                    device_id=device_id,
                    values=values,
                    quality=quality,
                    timestamp=ts,
                )
                total_processed += result.get('processed', 0)
                total_skipped += result.get('skipped', 0)
                results.append({
                    'device_type': device_type,
                    'device_id': device_id,
                    'processed': result.get('processed', 0),
                    'skipped': result.get('skipped', 0),
                    'errors': result.get('errors', []),
                })
            except Exception as e:
                _logger.exception(
                    'Error processing device readings for %s id=%s', device_type, device_id
                )
                total_skipped += 1
                results.append({
                    'device_type': device_type,
                    'device_id': device_id,
                    'processed': 0,
                    'skipped': 1,
                    'errors': [str(e)],
                })

        return _json_response({
            'status': 'ok',
            'results': results,
            'total_processed': total_processed,
            'total_skipped': total_skipped,
        })

    # ── GET /api/scada/tags ────────────────────────────────────────────────
    @http.route('/api/scada/tags', type='http', auth='none',
                methods=['GET'], csrf=False)
    def list_tags(self, **kwargs):
        """
        Returns all active registered tags so Ignition can auto-populate
        its subscription list on startup.
        """
        api_key = request.httprequest.headers.get('X-SCADA-API-Key', '')
        if not _auth(api_key):
            return _json_response({'status': 'error', 'message': 'Unauthorized'}, 401)

        tags = request.env['scada.tag'].sudo().search([('active', '=', True)])
        result = []
        for t in tags:
            result.append({
                'id': t.id,
                'name': t.name,
                'tag_path': t.tag_path,
                'tag_type': t.tag_type,
                'unit': t.unit or '',
                'odoo_model': t.odoo_model,
                'odoo_field': t.odoo_field or '',
                'equipment_id': t.equipment_id.id if t.equipment_id else None,
                'equipment_name': t.equipment_id.name if t.equipment_id else '',
                'last_value': t.last_value,
                'last_quality': t.last_quality,
                'last_sync': t.last_sync.isoformat() if t.last_sync else None,
            })
        return _json_response({'status': 'ok', 'tags': result, 'count': len(result)})

    # ── GET /api/scada/equipment ───────────────────────────────────────────
    @http.route('/api/scada/equipment', type='http', auth='none',
                methods=['GET'], csrf=False)
    def list_equipment(self, **kwargs):
        """
        Returns live operating parameters of all oil equipment.
        Ignition can poll this to display Odoo ERP data on HMI screens.
        """
        api_key = request.httprequest.headers.get('X-SCADA-API-Key', '')
        if not _auth(api_key):
            return _json_response({'status': 'error', 'message': 'Unauthorized'}, 401)

        equipment = request.env['maintenance.equipment'].sudo().search(
            [('is_oil_equipment', '=', True), ('active', '=', True)]
        )
        result = []
        for eq in equipment:
            result.append({
                'id': eq.id,
                'name': eq.name,
                'criticality': eq.criticality,
                'location_type': eq.location_type or '',
                'operating_pressure': eq.operating_pressure,
                'operating_temperature': eq.operating_temperature,
                'live_pressure': eq.live_pressure,
                'live_temperature': eq.live_temperature,
                'last_scada_sync': eq.last_scada_sync.isoformat() if eq.last_scada_sync else None,
                'certification_expiry': eq.certification_expiry.isoformat() if eq.certification_expiry else None,
            })
        return _json_response({'status': 'ok', 'equipment': result, 'count': len(result)})

    # -- GET /api/scada/health -----------------------------------------------
    @http.route('/api/scada/tanks', type='http', auth='none',
                methods=['GET'], csrf=False)
    def list_tanks(self, **kwargs):
        """
        Returns live storage location levels and volumes (is_storage_tank=True)
        for HMI tank-farm overview screens.
        """
        api_key = request.httprequest.headers.get('X-SCADA-API-Key', '')
        if not _auth(api_key):
            return _json_response({'status': 'error', 'message': 'Unauthorized'}, 401)

        locations = request.env['stock.location'].sudo().search([
            ('is_storage_tank', '=', True),
        ])
        result = []
        for loc in locations:
            result.append({
                'id': loc.id,
                'name': loc.display_name,
                'product_type': loc.product_type_id.name,
                'tank_type': loc.tank_type_id.name,
                'current_level_mm': loc.current_level_mm,
                'current_temperature_f': loc.current_temperature_f,
                'gross_volume_bbl': round(loc.gross_volume_bbl, 2),
                'net_standard_volume_bbl': round(loc.net_standard_volume_bbl, 2),
                'ullage_bbl': round(loc.ullage_bbl, 2),
                'max_capacity_bbl': loc.max_capacity_bbl,
                'fill_percent': round(loc.fill_percent, 1),
                'tank_state': loc.tank_state,
                'last_scada_sync': loc.last_scada_sync.isoformat() if loc.last_scada_sync else None,
            })
        return _json_response({'status': 'ok', 'locations': result, 'count': len(result)})

    # ── GET /api/scada/production/daily ────────────────────────────────────
    @http.route('/api/scada/production/daily', type='http', auth='none',
                methods=['GET'], csrf=False)
    def daily_production(self, **kwargs):
        """
        Returns the last 7 days of confirmed daily production reports.
        Ignition can display production trends on the control room overview.
        """
        api_key = request.httprequest.headers.get('X-SCADA-API-Key', '')
        if not _auth(api_key):
            return _json_response({'status': 'error', 'message': 'Unauthorized'}, 401)

        reports = request.env['oil.daily.production'].sudo().search(
            [('picking_id', '!=', False)],
            order='report_date desc',
            limit=50,
        )
        result = []
        for r in reports:
            oil_vol = sum(
                l.produced_qty for l in r.line_ids
                if 'oil' in l.product_id.name.lower() or 'crude' in l.product_id.name.lower()
            )
            gas_vol = sum(
                l.produced_qty for l in r.line_ids
                if 'gas' in l.product_id.name.lower()
            )
            water_vol = sum(
                l.produced_qty for l in r.line_ids
                if 'water' in l.product_id.name.lower()
            )
            result.append({
                'id': r.id,
                'report_date': str(r.report_date),
                'well': r.well_id.name if r.well_id else '',
                'project': r.project_id.name if r.project_id else '',
                'storage_location': r.storage_location_id.display_name if r.storage_location_id else '',
                'oil_volume_bbl': round(oil_vol, 2),
                'gas_volume_mcf': round(gas_vol, 2),
                'water_volume_bbl': round(water_vol, 2),
                'source': r.source,
            })
        return _json_response({'status': 'ok', 'reports': result, 'count': len(result)})

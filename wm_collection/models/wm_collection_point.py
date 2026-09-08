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
import logging
import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WmCollectionPoint(models.Model):
    """A physical waste pickup location linked to a partner, zone, and service frequency configuration."""
    _name = 'wm.collection.point'
    _description = 'Collection Point'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    zone_id = fields.Many2one('wm.service.zone', string='Zone', help='Service zone used for automated route assignment.')
    use_route_zones = fields.Boolean(compute='_compute_use_settings')
    street = fields.Char(string='Street')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    zip = fields.Char(string='Zip')
    country_id = fields.Many2one('res.country', string='Country')
    latitude = fields.Float(string='Latitude', digits=(10, 7))
    longitude = fields.Float(string='Longitude', digits=(10, 7))
    category_ids = fields.Many2many('wm.waste.category', string='Categories')
    contact_address = fields.Char(string='Address', compute='_compute_contact_address')

    def _compute_use_settings(self):
        """
        Retrieve map integration and zone restriction settings from system
        configuration to control which address fields and geo-coding features
        are enabled for this collection point.
        """
        use_zones = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_route_zones', 'False') in ('True', '1')
        for rec in self:
            rec.use_route_zones = use_zones

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """
        Pre-populate the collection point address fields from the selected
        partner's delivery address when the partner changes, reducing manual
        data entry for dispatchers.
        """
        if self.partner_id:
            if not self.street and self.partner_id.street:
                self.street = self.partner_id.street
            if not self.city and self.partner_id.city:
                self.city = self.partner_id.city
            if not self.state_id and self.partner_id.state_id:
                self.state_id = self.partner_id.state_id
            if not self.zip and self.partner_id.zip:
                self.zip = self.partner_id.zip
            if not self.country_id and self.partner_id.country_id:
                self.country_id = self.partner_id.country_id
            if self.partner_id.partner_latitude and self.partner_id.partner_longitude:
                self.latitude = self.partner_id.partner_latitude
                self.longitude = self.partner_id.partner_longitude
            else:
                self._auto_geo_localize()

    @api.onchange('street', 'city', 'state_id', 'zip', 'country_id')
    def _onchange_address_geo_localize(self):
        """
        Automatically fetch latitude and longitude when address fields change.
        """
        if self.street or self.city or self.zip or self.country_id:
            self._auto_geo_localize()

    def _auto_geo_localize(self):
        """
        Silently attempt to geolocate point when address changes.
        """
        for point in self:
            if point.latitude and point.longitude:
                continue
            strategies = []
            structured_params = {'format': 'json', 'limit': 1, 'addressdetails': 1}
            if point.street:
                structured_params['street'] = point.street
            if point.city:
                structured_params['city'] = point.city
            if point.state_id:
                structured_params['state'] = point.state_id.name
            if point.zip:
                structured_params['postalcode'] = point.zip
            if point.country_id:
                structured_params['country'] = point.country_id.code

            if point.street or point.city:
                strategies.append(('structured', structured_params))

            address_parts = [
                point.street,
                point.city,
                point.state_id.name if point.state_id else '',
                point.zip,
                point.country_id.name if point.country_id else ''
            ]
            full_query = ', '.join([p for p in address_parts if p])
            if full_query:
                strategies.append(('full_address', {'q': full_query, 'format': 'json', 'limit': 1, 'addressdetails': 1}))

            result = None
            for strategy_name, params in strategies:
                try:
                    headers = {
                        'User-Agent': 'OdooWasteManagement/1.0 (waste_management@cybrosys.com)',
                        'Accept-Language': 'en'
                    }
                    url = "https://nominatim.openstreetmap.org/search"
                    response = requests.get(url, params=params, headers=headers, timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        if data:
                            result = data[0]
                            break
                except Exception as e:
                    _logger.warning("Geocoding request failed for collection point %s: %s", point.id, e)
                    break

            if result and 'lat' in result and 'lon' in result:
                try:
                    point.latitude = float(result['lat'])
                    point.longitude = float(result['lon'])
                except (ValueError, TypeError) as e:
                    _logger.warning("Failed to parse coordinates for collection point %s: %s", point.id, e)

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to implement custom initialization and validation
        logic.
        """
        records = super().create(vals_list)
        for rec in records:
            if (rec.street or rec.city or rec.country_id) and not (rec.latitude or rec.longitude):
                rec._auto_geo_localize()
        return records

    def write(self, vals):
        """
        Override write to implement business validations and side effects.
        """
        res = super().write(vals)
        address_fields = {'street', 'city', 'state_id', 'zip', 'country_id'}
        if address_fields.intersection(vals.keys()) and not ('latitude' in vals or 'longitude' in vals):
            for rec in self:
                rec._auto_geo_localize()
        return res

    @api.depends('street', 'city', 'state_id', 'zip', 'country_id')
    def _compute_contact_address(self):
        """
        Construct the formatted contact address string from the collection
        point's partner fields, used for route sheet generation and carrier
        label printing.
        """
        for point in self:
            parts = [
                point.street,
                point.city,
                point.state_id.name if point.state_id else '',
                point.zip,
                point.country_id.name if point.country_id else ''
            ]
            point.contact_address = ", ".join([p for p in parts if p])

    def action_geo_localize(self):
        """
        Geolocate the collection point using OpenStreetMap's Nominatim API (Free).
        Uses structured queries and fallback strategies for better accuracy.
        """
        for point in self:
            strategies = []

            # Strategy 1: Structured query (most accurate)
            structured_params = {
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            if point.street:
                structured_params['street'] = point.street
            if point.city:
                structured_params['city'] = point.city
            if point.state_id:
                structured_params['state'] = point.state_id.name
            if point.zip:
                structured_params['postalcode'] = point.zip
            if point.country_id:
                structured_params['country'] = point.country_id.code

            if point.street or point.city:
                strategies.append(('structured', structured_params))

            # Strategy 2: Full address
            address_parts = [
                point.street,
                point.city,
                point.state_id.name if point.state_id else '',
                point.zip,
                point.country_id.name if point.country_id else ''
            ]
            full_query = ', '.join([p for p in address_parts if p])
            if full_query:
                strategies.append(('full_address', {
                    'q': full_query,
                    'format': 'json',
                    'limit': 1,
                    'addressdetails': 1
                }))

            # Strategy 3: ZIP code + Country (Primary fallback for specific areas)
            if point.zip:
                zip_params = {
                    'postalcode': point.zip,
                    'format': 'json',
                    'limit': 1,
                    'addressdetails': 1
                }
                if point.country_id:
                    zip_params['country'] = point.country_id.code
                if point.city:
                    zip_params['city'] = point.city
                strategies.append(('zip_code', zip_params))

            # Strategy 4: City + Country (fallback)
            if point.city and point.country_id:
                strategies.append(('city_country', {
                    'q': f"{point.city}, {point.country_id.name}",
                    'format': 'json',
                    'limit': 1
                }))

            # Strategy 4: Just country (last resort)
            if point.country_id:
                strategies.append(('country_only', {
                    'q': point.country_id.name,
                    'format': 'json',
                    'limit': 1
                }))

            result = None
            for strategy_name, params in strategies:
                try:
                    headers = {
                        'User-Agent': 'OdooWebMap/1.0 (Odoo Community Module)',
                        'Accept-Language': 'en'
                    }
                    url = "https://nominatim.openstreetmap.org/search"
                    response = requests.get(url, params=params, headers=headers, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    if data:
                        result = data[0]
                        break
                except Exception as e:
                    _logger.warning("Geocoding lookup attempt failed for collection point %s: %s", point.id, e)
                    continue

            if result:
                point.write({
                    'latitude': float(result['lat']),
                    'longitude': float(result['lon']),
                })
            else:
                raise UserError(_(
                    "Could not geolocate address for %s.\n"
                    "Please verify the address is complete and correct."
                ) % point.name)
        return True

    def action_view_map(self):
        """
        Open the geographic map view centred on this collection point's
        coordinates, displaying its pin marker and nearby route stops for
        logistics planning.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Collection Points Map'),
            'res_model': 'wm.collection.point',
            'view_mode': 'map,form',
            'views': [
                (self.env.ref('wm_collection.view_wm_collection_point_map').id, 'map'),
                (self.env.ref('wm_collection.view_wm_collection_point_form').id, 'form')
            ],
            'target': 'current',
        }

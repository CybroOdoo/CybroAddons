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
import requests
from odoo import models, fields, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    """Extend res.partner to add geolocation using OpenStreetMap Nominatim API."""
    _inherit = 'res.partner'

    def action_geo_localize_nominatim(self):
        """
        Geolocate the partner using OpenStreetMap's Nominatim API (Free).
        Uses structured queries and fallback strategies for better accuracy.
        """
        for partner in self:
            if not partner.country_id:
                continue

            # Try multiple query strategies for better results
            strategies = self._get_geocoding_strategies(partner)

            result = None
            network_error = False
            for strategy_name, params in strategies:
                try:
                    headers = {
                        'User-Agent': 'OdooWebMap/1.0 (Odoo Community Module)',
                        'Accept-Language': 'en'  # Prefer English results
                    }
                    url = "https://nominatim.openstreetmap.org/search"

                    response = requests.get(url, params=params, headers=headers, timeout=10)
                    response.raise_for_status()
                    data = response.json()

                    if data:
                        # Check if result is reasonable (has good importance score)
                        if float(data[0].get('importance', 0)) > 0.3:
                            result = data[0]
                            break
                        elif not result:  # Keep first result as fallback
                            result = data[0]

                except requests.exceptions.RequestException:
                    network_error = True
                    break
                except Exception:
                    continue

            if result:
                partner.write({
                    'partner_latitude': float(result['lat']),
                    'partner_longitude': float(result['lon']),
                    'date_localization': fields.Date.context_today(partner)
                })
            elif network_error:
                raise UserError(_("Geocoding service unavailable. Please check your network connection."))
            else:
                raise UserError(_(
                    "Could not geolocate address for %s.\n"
                    "Please verify the address is complete and correct."
                ) % partner.display_name)

        return True
    
    def _get_geocoding_strategies(self, partner):
        """
        Generate multiple geocoding query strategies in order of specificity.
        Returns list of (strategy_name, params) tuples.
        """
        strategies = []
        
        # Strategy 1: Structured query (most accurate)
        structured_params = {
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        
        if partner.street:
            structured_params['street'] = partner.street
        if partner.city:
            structured_params['city'] = partner.city
        if partner.state_id:
            structured_params['state'] = partner.state_id.name
        if partner.zip:
            structured_params['postalcode'] = partner.zip
        if partner.country_id:
            structured_params['country'] = partner.country_id.code  # Use country code for better results
        
        # Only use structured query if we have street or city
        if partner.street or partner.city:
            strategies.append(('structured', structured_params))
        
        # Strategy 2: Full address as single query
        address_parts = [
            partner.street,
            partner.street2,
            partner.city,
            partner.state_id.name if partner.state_id else '',
            partner.zip,
            partner.country_id.name
        ]
        full_query = ', '.join([p for p in address_parts if p])
        
        if full_query:
            strategies.append(('full_address', {
                'q': full_query,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }))
        
        # Strategy 3: City + Country (fallback for incomplete addresses)
        if partner.city and partner.country_id:
            strategies.append(('city_country', {
                'q': f"{partner.city}, {partner.country_id.name}",
                'format': 'json',
                'limit': 1
            }))
        
        # Strategy 4: Just country (last resort)
        if partner.country_id:
            strategies.append(('country_only', {
                'q': partner.country_id.name,
                'format': 'json',
                'limit': 1
            }))
        
        return strategies

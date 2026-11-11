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
#############################################################################
import logging
import requests
from odoo import models
from odoo.http import request

_logger = logging.getLogger(__name__)

PRICELIST_SESSION_KEY = 'website_sale_current_pl'


class Website(models.Model):
    """Extend website to apply GeoIP-based pricelist for public visitors."""
    _inherit = 'website'

    def get_user_location(self):
        """Return country name for the current user's IP, or None."""
        user_ip = None
        if request and hasattr(request, 'session'):
            user_ip = request.session.get('user_ip')
        if not user_ip:
            try:
                user_ip = self.env.user.ip_address
            except Exception as e:
                _logger.debug("Could not read user IP address: %s", e)
        if not user_ip and request and hasattr(request, 'httprequest'):
            addr = getattr(request.httprequest, 'remote_addr', None)
            if addr and addr not in ('127.0.0.1', '::1', 'localhost'):
                user_ip = addr
        if not user_ip:
            return None
        try:
            resp = requests.get(
                f'http://ip-api.com/json/{user_ip}', timeout=2
            ).json()
            return resp.get('country')
        except Exception as e:
            _logger.warning('GeoIP lookup failed for %s: %s', user_ip, e)
            return None

    def _get_and_cache_current_pricelist(self):
        """
        Override: if the session already has a pricelist set by our GeoIP
        or language-switch controller, respect it.  Otherwise fall back to
        the stock Odoo logic.

        For public (not-logged-in) visitors we additionally auto-detect their
        location and apply the matching pricelist the first time they arrive.
        """
        try:
            public_user = self.env.ref('base.public_user', raise_if_not_found=False)
            is_public = (
                (public_user and self.env.user.id == public_user.id)
                or self.env.user._is_public()
            )

            if is_public and request and hasattr(request, 'session') and PRICELIST_SESSION_KEY not in request.session:
                # Public visitor with no session pricelist yet → GeoIP detect
                user_ip = request.session.get('user_ip')
                if not user_ip and hasattr(request, 'httprequest'):
                    addr = getattr(request.httprequest, 'remote_addr', None)
                    if addr and addr not in ('127.0.0.1', '::1', 'localhost'):
                        user_ip = addr
                        request.session['user_ip'] = user_ip
                if not user_ip:
                    try:
                        resp = requests.get(
                            'https://api.ipify.org?format=json', timeout=2
                        )
                        if resp.status_code == 200:
                            user_ip = resp.json().get('ip')
                            if user_ip:
                                request.session['user_ip'] = user_ip
                    except Exception as e:
                        _logger.debug('ipify lookup failed: %s', e)

                if user_ip:
                    try:
                        geo = requests.get(
                            f'http://ip-api.com/json/{user_ip}', timeout=2
                        ).json()
                        country_name = geo.get('country')
                        if country_name:
                            pricelist = self._pricelist_for_country(country_name)
                            if pricelist:
                                request.session[PRICELIST_SESSION_KEY] = pricelist.id
                    except Exception as e:
                        _logger.warning('Public GeoIP pricelist lookup failed: %s', e)

        except Exception as e:
            _logger.warning('Error in GeoIP pricelist override: %s', e)

        return super()._get_and_cache_current_pricelist()

    def _pricelist_for_country(self, country_name):
        """
        Return the best available pricelist for a country name.
        Uses countryinfo and res.country to get the currency dynamically,
        then finds a matching pricelist — no currency names are hardcoded.
        """
        try:
            currencies = []
            try:
                from countryinfo import CountryInfo
                info = CountryInfo(country_name)
                currencies = info.currencies() or []
            except Exception as e:
                _logger.debug('CountryInfo currencies lookup failed for %s: %s', country_name, e)

            currency = None
            if currencies:
                currency = self.env['res.currency'].sudo().search(
                    [('name', '=', currencies[0]),
                     ('active', '=', True)], limit=1
                )
            if not currency:
                country_rec = self.env['res.country'].sudo().search(
                    [('name', '=ilike', country_name)], limit=1
                )
                if country_rec and country_rec.currency_id and country_rec.currency_id.active:
                    currency = country_rec.currency_id

            if not currency:
                return None

            # Prefer pricelists available on this website
            available = self.get_pricelist_available()
            pricelist = next(
                (pl for pl in available if pl.currency_id == currency), None
            )
            # Fallback: any pricelist in the system with that currency
            if not pricelist:
                pricelist = self.env['product.pricelist'].sudo().search(
                    [('currency_id', '=', currency.id)], limit=1
                )
            return pricelist
        except Exception as e:
            _logger.warning(
                'Could not resolve pricelist for country %s: %s', country_name, e
            )
            return None

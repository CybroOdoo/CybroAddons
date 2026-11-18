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

from odoo import fields, models

SALE_BUDGETS = (1000000, 2000000, 4000000, 8000000)
RENT_BUDGETS = (6000, 10000, 15000, 25000)
LISTING_SORTS = {
    'newest': 'sequence, date_listed desc, id desc',
    'price-asc': 'price asc, id',
    'price-desc': 'price desc, id',
    'size': 'area desc, id',
}


class Website(models.Model):
    """Listing data of the Propelle pages and snippets."""
    _inherit = 'website'

    def _propelle_cities(self):
        """Cities offered by the search panel and the filters.

        :return: list of dictionaries with the value and label of each city.
        """
        return [
            {'value': city.name, 'label': city.display_name, 'id': city.id}
            for city in self.env['propelle.city'].sudo().search([])
        ]

    def _propelle_property_types(self):
        """Property types offered by the search panel and the filters.

        :return: list of dictionaries with the value and label of each type.
        """
        selection = self.env['propelle.property']._fields[
            'property_type']._description_selection(self.env)
        return [{'value': value, 'label': label} for value, label in selection]

    def _propelle_budgets(self, listing_type):
        """Budget steps of the price filters.

        :param str listing_type: ``sale`` or ``rent``.
        :return: list of dictionaries with the value and labels of each step.
        """
        currency = self.company_id.currency_id
        if listing_type == 'rent':
            return [{
                'value': amount,
                'label': self.env._(
                    '%(price)s / mo', price=currency._propelle_format(amount)),
                'long_label': self.env._(
                    'Up to %(price)s / month',
                    price=currency._propelle_format(amount)),
            } for amount in RENT_BUDGETS]
        return [{
            'value': amount,
            'label': currency._propelle_format(amount),
            'long_label': self.env._(
                'Up to %(price)s', price=currency._propelle_format(amount)),
        } for amount in SALE_BUDGETS]

    def _propelle_listing_domain(self, listing_type, filters=None):
        """Domain of the published listings of the Buy or the Rent page.

        :param str listing_type: ``sale`` or ``rent``.
        :param dict filters: choices of the filter bar (``location``,
            ``type``, ``min``, ``max``, ``beds`` and ``furnished``). Empty
            values and ``all`` mean no filter.
        :return: search domain.
        """
        filters = filters or {}
        domain = [
            ('is_published', '=', True),
            ('listing_type', '=', listing_type),
        ]
        if filters.get('location') not in (None, '', 'all'):
            domain.append(('city_id.name', '=', filters['location']))
        if filters.get('type') not in (None, '', 'all'):
            domain.append(('property_type', '=', filters['type']))
        if filters.get('min'):
            domain.append(('price', '>=', filters['min']))
        if filters.get('max'):
            domain.append(('price', '<=', filters['max']))
        if filters.get('beds'):
            domain.append(('bedrooms', '>=', filters['beds']))
        if filters.get('furnished') in ('furnished', 'unfurnished'):
            domain.append(
                ('is_furnished', '=', filters['furnished'] == 'furnished'))
        return domain

    def _propelle_listings(self, listing_type, filters=None, sort='newest',
                           offset=0, limit=None):
        """Published listings of the Buy or the Rent page.

        :param str listing_type: ``sale`` or ``rent``.
        :param dict filters: choices of the filter bar.
        :param str sort: ``newest``, ``price-asc``, ``price-desc`` or
            ``size``.
        :param int offset: number of listings to skip.
        :param int limit: maximum number of listings, all when empty.
        :return: recordset of listings.
        """
        return self.env['propelle.property'].sudo().search(
            self._propelle_listing_domain(listing_type, filters),
            order=LISTING_SORTS.get(sort, LISTING_SORTS['newest']),
            offset=offset, limit=limit)

    def _propelle_listing_count(self, listing_type, filters=None):
        """Number of published listings matching the filters.

        :param str listing_type: ``sale`` or ``rent``.
        :param dict filters: choices of the filter bar.
        :return: the number of listings.
        """
        return self.env['propelle.property'].sudo().search_count(
            self._propelle_listing_domain(listing_type, filters))

    def _propelle_listing_stats(self, listing_type):
        """Figures shown beside the title of the Buy and Rent pages, over
        all the published listings of the kind.

        :param str listing_type: ``sale`` or ``rent``.
        :return: list of (label, value) pairs.
        """
        properties = self.env['propelle.property'].sudo()
        domain = self._propelle_listing_domain(listing_type)
        currency = self.company_id.currency_id
        total = properties.search_count(domain)
        cheapest = properties.search(domain, order='price asc', limit=1)
        count = self.env._('%(count)s homes', count=total)
        if total == 1:
            count = self.env._('1 home')
        if listing_type == 'rent':
            return [
                (self.env._('Available now'), count),
                (self.env._('Rent from'), self.env._(
                    '%(price)s / mo',
                    price=currency._propelle_format(cheapest.price))),
                (self.env._('Furnished'), str(properties.search_count(
                    domain + [('is_furnished', '=', True)]))),
            ]
        week_ago = fields.Date.context_today(self) - timedelta(days=7)
        return [
            (self.env._('Listed now'), count),
            (self.env._('Prices from'),
             currency._propelle_format(cheapest.price)),
            (self.env._('New this week'), str(properties.search_count(
                domain + [('date_listed', '>=', week_ago)]))),
        ]

    def _propelle_projects(self):
        """Published development projects.

        :return: recordset of projects.
        """
        return self.env['propelle.project'].sudo().search(
            [('is_published', '=', True)])

    def _propelle_counts(self):
        """Number of listings and projects, shown by the home page tiles.

        :return: dictionary of counts.
        """
        properties = self.env['propelle.property'].sudo()
        published = [('is_published', '=', True)]
        return {
            'sale': properties.search_count(
                published + [('listing_type', '=', 'sale')]),
            'rent': properties.search_count(
                published + [('listing_type', '=', 'rent')]),
            'projects': self.env['propelle.project'].sudo().search_count(
                published),
        }

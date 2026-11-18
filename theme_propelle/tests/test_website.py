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

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPropelleWebsite(TransactionCase):
    """Test the listing data helpers of the website."""

    @classmethod
    def setUpClass(cls):
        """Create cities and listings of known kinds."""
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1)
        properties = cls.env['propelle.property']
        cls.city_a = cls.env['propelle.city'].create({'name': 'Alpha'})
        cls.city_b = cls.env['propelle.city'].create({'name': 'Beta'})
        base = {'is_published': True, 'listing_type': 'sale'}
        cls.cheap = properties.create(dict(
            base, name='Cheap Flat', city_id=cls.city_a.id,
            property_type='apartment', price=111, bedrooms=1, area=500,
            date_listed=fields.Date.today() - timedelta(days=30)))
        cls.mid = properties.create(dict(
            base, name='Mid House', city_id=cls.city_b.id,
            property_type='house', price=222, bedrooms=3, area=2000))
        cls.big = properties.create(dict(
            base, name='Big Villa', city_id=cls.city_b.id,
            property_type='villa', price=333, bedrooms=5, area=9000))
        cls.hidden = properties.create(dict(
            base, name='Hidden Villa', is_published=False,
            city_id=cls.city_b.id, property_type='villa', price=1))
        cls.rental = properties.create({
            'name': 'Rental Loft', 'listing_type': 'rent',
            'is_published': True, 'is_furnished': True,
            'city_id': cls.city_a.id, 'property_type': 'apartment',
            'price': 4000})

    def listing_names(self, filters=None, sort='newest', listing_type='sale'):
        """Names of the listings the website returns."""
        return self.website._propelle_listings(
            listing_type, filters, sort).mapped('name')

    def test_domain_only_published_of_the_kind(self):
        """Unpublished listings and the other kind never show."""
        names = self.listing_names()
        self.assertNotIn('Hidden Villa', names)
        self.assertNotIn('Rental Loft', names)
        self.assertIn('Cheap Flat', names)
        self.assertEqual(self.listing_names(listing_type='rent').count(
            'Rental Loft'), 1)

    def test_filters(self):
        """Each choice of the filter bar narrows the listings."""
        test = {self.cheap.name, self.mid.name, self.big.name}
        def found(filters):
            """Test listings that match the filters."""
            return set(self.listing_names(filters)) & test
        self.assertEqual(found({'location': 'Beta'}),
                         {'Mid House', 'Big Villa'})
        self.assertEqual(found({'type': 'villa'}), {'Big Villa'})
        self.assertEqual(found({'min': 200}), {'Mid House', 'Big Villa'})
        self.assertEqual(found({'max': 200}), {'Cheap Flat'})
        self.assertEqual(found({'beds': 3}), {'Mid House', 'Big Villa'})
        self.assertEqual(found({'location': 'all', 'type': 'all'}), test)
        self.assertIn('Rental Loft', self.listing_names(
            {'furnished': 'furnished'}, listing_type='rent'))
        self.assertNotIn('Rental Loft', self.listing_names(
            {'furnished': 'unfurnished'}, listing_type='rent'))

    def test_sorting(self):
        """The listings follow the chosen order."""
        def order(sort):
            """Test listings in the order of the sort."""
            names = self.listing_names(sort=sort)
            return [n for n in names if n in (
                'Cheap Flat', 'Mid House', 'Big Villa')]
        self.assertEqual(order('price-asc'),
                         ['Cheap Flat', 'Mid House', 'Big Villa'])
        self.assertEqual(order('price-desc'),
                         ['Big Villa', 'Mid House', 'Cheap Flat'])
        self.assertEqual(order('size')[0], 'Big Villa')
        self.assertEqual(order('unknown'), order('newest'))

    def test_paging_and_count(self):
        """The count ignores the page, the page honours offset and limit."""
        total = self.website._propelle_listing_count('sale')
        self.assertEqual(total, len(self.listing_names()))
        page = self.website._propelle_listings(
            'sale', sort='price-asc', offset=1, limit=2)
        everything = self.website._propelle_listings(
            'sale', sort='price-asc')
        self.assertEqual(page.ids, everything[1:3].ids)
        self.assertEqual(self.website._propelle_listing_count(
            'sale', {'location': 'Beta'}), 2)

    def test_budgets(self):
        """Budget steps are labelled with the currency of the company."""
        sale = self.website._propelle_budgets('sale')
        rent = self.website._propelle_budgets('rent')
        symbol = self.website.company_id.currency_id.symbol
        self.assertTrue(sale and rent)
        self.assertTrue(all(symbol in step['label'] for step in sale))
        self.assertTrue(all('/ mo' in step['label'] for step in rent))
        self.assertTrue(all(step['long_label'].startswith('Up to')
                            for step in sale + rent))
        self.assertEqual([s['value'] for s in sale],
                         sorted(s['value'] for s in sale))

    def test_listing_stats(self):
        """The figures cover the published listings of the kind."""
        stats = dict(self.website._propelle_listing_stats('sale'))
        total = self.website._propelle_listing_count('sale')
        self.assertIn(str(total), stats['Listed now'])
        self.assertEqual(len(stats), 3)
        rent = dict(self.website._propelle_listing_stats('rent'))
        self.assertEqual(rent['Furnished'], str(
            self.env['propelle.property'].search_count([
                ('is_published', '=', True), ('listing_type', '=', 'rent'),
                ('is_furnished', '=', True)])))
        self.assertIn('/ mo', rent['Rent from'])

    def test_cities_and_types(self):
        """The search panel gets the cities and the property types."""
        cities = {c['value']: c for c in self.website._propelle_cities()}
        self.assertEqual(cities['Alpha']['id'], self.city_a.id)
        types = {t['value'] for t in self.website._propelle_property_types()}
        self.assertTrue({'villa', 'apartment', 'house'} <= types)

    def test_counts_and_projects(self):
        """The counts follow the published listings and projects."""
        before = self.website._propelle_counts()
        self.cheap.is_published = False
        project = self.env['propelle.project'].create({
            'name': 'Counted Project', 'location': 'X, Y',
            'is_published': True})
        after = self.website._propelle_counts()
        self.assertEqual(after['sale'], before['sale'] - 1)
        self.assertEqual(after['projects'], before['projects'] + 1)
        self.assertIn(project, self.website._propelle_projects())

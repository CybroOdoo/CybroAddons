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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPropelleModels(TransactionCase):
    """Test the computed values and actions of the Propelle models."""

    @classmethod
    def setUpClass(cls):
        """Create a city, a listing and a project."""
        super().setUpClass()
        cls.city = cls.env['propelle.city'].create({
            'name': 'Testville', 'state_code': 'TX'})
        cls.prop = cls.env['propelle.property'].create({
            'name': 'Model Test House',
            'listing_type': 'sale',
            'property_type': 'villa',
            'city_id': cls.city.id,
            'neighbourhood': 'Old Town',
            'price': 1250000,
        })
        cls.project = cls.env['propelle.project'].create({
            'name': 'Model Test Project',
            'location': 'Old Town, Testville',
            'state': 'selling',
            'price_from': 4800000,
        })

    def test_city_display_name(self):
        """The state code follows the name, and is left out when empty."""
        self.assertEqual(self.city.display_name, 'Testville, TX')
        self.city.state_code = False
        self.assertEqual(self.city.display_name, 'Testville')

    def test_city_property_count(self):
        """A city counts its listings."""
        self.assertEqual(self.city.property_count, 1)
        self.env['propelle.property'].create({
            'name': 'Second House', 'city_id': self.city.id,
            'property_type': 'house', 'price': 1})
        self.city.invalidate_recordset()
        self.assertEqual(self.city.property_count, 2)

    def test_property_location(self):
        """The location joins neighbourhood, city and state code."""
        self.assertEqual(self.prop.location, 'Old Town, Testville, TX')
        self.prop.neighbourhood = False
        self.assertEqual(self.prop.location, 'Testville, TX')

    def test_property_tag(self):
        """The tag is the custom label, or the name of the type."""
        self.assertEqual(self.prop.tag, 'Villa')
        self.prop.type_label = 'Waterfront'
        self.assertEqual(self.prop.tag, 'Waterfront')

    def test_property_price_label(self):
        """The price is shown whole, with the currency of the listing."""
        label = self.prop.price_label
        self.assertIn('1,250,000', label)
        self.assertIn(self.prop.currency_id.symbol, label)

    def test_property_toggle_published(self):
        """The button publishes and unpublishes the listing."""
        self.prop.is_published = False
        self.prop.action_toggle_published()
        self.assertTrue(self.prop.is_published)
        self.prop.action_toggle_published()
        self.assertFalse(self.prop.is_published)

    def test_property_card_values(self):
        """The booking page gets the values of a sale and of a rental."""
        values = self.prop._propelle_card_values()
        self.assertEqual(values['id'], str(self.prop.id))
        self.assertEqual(values['status'], 'sale')
        self.assertEqual(values['city'], 'Testville')
        self.assertEqual(values['price'], self.prop.price_label)
        self.assertIn('/web/image/propelle.property/', values['img'])
        self.prop.listing_type = 'rent'
        self.assertIn('/ month', self.prop._propelle_card_values()['price'])

    def test_project_availability(self):
        """The availability is the custom label, or the name of the status."""
        self.assertEqual(self.project.availability, 'Now selling')
        self.project.availability_label = 'Last 3 homes'
        self.assertEqual(self.project.availability, 'Last 3 homes')

    def test_project_price_label(self):
        """The starting price is shown in its short form."""
        self.assertIn('4.8M', self.project.price_label)

    def test_project_city_name(self):
        """The city is the last part of the location."""
        self.assertEqual(self.project.city_name, 'Testville')
        self.project.location = 'Malibu'
        self.assertEqual(self.project.city_name, 'Malibu')

    def test_project_toggle_published(self):
        """The button publishes and unpublishes the project."""
        self.project.is_published = False
        self.project.action_toggle_published()
        self.assertTrue(self.project.is_published)
        self.project.action_toggle_published()
        self.assertFalse(self.project.is_published)

    def test_currency_format(self):
        """Amounts are shown whole, and short when asked."""
        usd = self.env.ref('base.USD')
        self.assertEqual(usd._propelle_format(1250000), '$1,250,000')
        self.assertEqual(usd._propelle_format(1250000, compact=True), '$1.2M')
        self.assertEqual(usd._propelle_format(4000000, compact=True), '$4M')
        self.assertEqual(usd._propelle_format(890000, compact=True), '$890K')
        self.assertEqual(usd._propelle_format(500, compact=True), '$500')
        self.assertEqual(usd._propelle_format(False), '$0')
        eur = self.env.ref('base.EUR')
        self.assertTrue(eur._propelle_format(1000).endswith(eur.symbol)
                        or eur.position == 'before')

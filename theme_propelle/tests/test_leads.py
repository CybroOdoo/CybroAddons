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
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestPropelleLeads(HttpCase):
    """Test the requests of viewings and valuations, and the alerts."""

    @classmethod
    def setUpClass(cls):
        """Prepare a weekday and a published listing."""
        super().setUpClass()
        day = fields.Date.today() + timedelta(days=1)
        while day.weekday() >= 5:
            day += timedelta(days=1)
        cls.day = fields.Date.to_string(day)
        cls.listing = cls.env['propelle.property'].create({
            'name': 'Test Villa',
            'listing_type': 'sale',
            'property_type': 'villa',
            'city_id': cls.env['propelle.city'].search([], limit=1).id,
            'price': 1000000,
            'is_published': True,
        })

    def _request(self, **extra):
        """Send a viewing request with valid contact details."""
        values = {
            'mode': 'view', 'home': self.listing.id, 'date': self.day,
            'hour': 11, 'name': 'Route Tester', 'email': 'route@example.com',
            'phone': '+1 310 555 0101', 'kind': 'In person',
            'notes': 'Ring the bell',
        }
        values.update(extra)
        return self.make_jsonrpc_request('/propelle/booking/request', values)

    def test_viewing_creates_lead(self):
        """A viewing request creates a lead with the visit details."""
        before = self.env['crm.lead'].search_count([])
        result = self._request()
        self.assertTrue(result.get('reference'), result)
        self.assertEqual(self.env['crm.lead'].search_count([]), before + 1)
        lead = self.env['crm.lead'].search([], order='id desc', limit=1)
        self.assertEqual(lead.email_from, 'route@example.com')
        self.assertIn('Test Villa', lead.name)
        self.assertIn('11:00 am', lead.description)
        self.assertIn('Ring the bell', lead.description)

    def test_valuation_creates_lead(self):
        """A valuation request needs an address and creates a lead."""
        refused = self._request(mode='sell', home=0, address='x')
        self.assertIn('error', refused)
        result = self._request(
            mode='sell', home=0, address='12 Ocean Drive', city='Miami',
            ptype='Villa', beds='3')
        self.assertTrue(result.get('reference'), result)
        lead = self.env['crm.lead'].search([], order='id desc', limit=1)
        self.assertIn('12 Ocean Drive', lead.name)

    def test_invalid_requests_are_refused(self):
        """Bad contact details, closed days and hours create no lead."""
        before = self.env['crm.lead'].search_count([])
        sunday = fields.Date.today() + timedelta(days=1)
        while sunday.weekday() != 6:
            sunday += timedelta(days=1)
        for extra in (
            {'email': 'nope'},
            {'phone': 'abc'},
            {'hour': 3},
            {'date': fields.Date.to_string(sunday)},
            {'date': fields.Date.to_string(fields.Date.today())},
            {'home': 0},
        ):
            with self.subTest(extra=extra):
                self.assertIn('error', self._request(**extra))
        self.assertEqual(self.env['crm.lead'].search_count([]), before)

    def test_alert_creates_lead(self):
        """An alert request is saved as a lead, a wrong email is refused."""
        bad = self.make_jsonrpc_request(
            '/propelle/alert', {'email': 'nope', 'city': 'Miami'})
        self.assertIn('error', bad)
        before = self.env['crm.lead'].search_count([])
        good = self.make_jsonrpc_request(
            '/propelle/alert', {'email': 'a@example.com', 'city': 'Miami'})
        self.assertTrue(good['saved'])
        self.assertEqual(self.env['crm.lead'].search_count([]), before + 1)

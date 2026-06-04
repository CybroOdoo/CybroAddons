# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from unittest.mock import MagicMock, patch
from odoo.tests.common import TransactionCase

# Patch target paths — must match the names as imported in res_partner.py
GEOCODER_PATH = 'odoo.addons.contacts_timezone.models.res_partner.Nominatim'
TZ_FINDER_PATH = 'odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_location(lat=40.7128, lng=-74.0060):
    """Return a minimal mock geopy Location."""
    loc = MagicMock()
    loc.latitude = lat
    loc.longitude = lng
    return loc


def _make_geocoder_mock(location=None, side_effect=None):
    """Return a fully configured (Nominatim instance, Nominatim class) mock pair."""
    geocoder = MagicMock()
    if side_effect:
        geocoder.geocode.side_effect = side_effect
    else:
        geocoder.geocode.return_value = location
    nominatim_cls = MagicMock(return_value=geocoder)
    return geocoder, nominatim_cls


def _make_tzfinder_mock(tz_str=None):
    """Return a (TimezoneFinder instance, TimezoneFinder class) mock pair."""
    tf = MagicMock()
    tf.timezone_at.return_value = tz_str
    tf_cls = MagicMock(return_value=tf)
    return tf, tf_cls


# ---------------------------------------------------------------------------
# 1. Field definition tests — no geopy needed
# ---------------------------------------------------------------------------

class TestResPartnerFields(TransactionCase):
    """Verify that the two custom fields exist and have the correct type."""

    @patch(TZ_FINDER_PATH)
    @patch(GEOCODER_PATH)
    def setUp(self, mock_nom_cls, mock_tf_cls):
        super().setUp()
        # Prevent real network calls during partner creation in setUp
        geocoder, nom_cls = _make_geocoder_mock(location=None)
        mock_nom_cls.return_value = geocoder
        tf, tf_cls = _make_tzfinder_mock(tz_str=None)
        mock_tf_cls.return_value = tf
        with patch(GEOCODER_PATH, mock_nom_cls), patch(TZ_FINDER_PATH, mock_tf_cls):
            self.partner = self.env['res.partner'].create({'name': 'Test Partner TZ'})

    def test_contact_local_time_tz_field_exists(self):
        """contact_local_time_tz must be a Char field on res.partner."""
        field = self.env['res.partner']._fields.get('contact_local_time_tz')
        self.assertIsNotNone(field, "Field 'contact_local_time_tz' must be defined")
        self.assertEqual(field.type, 'char')

    def test_contact_local_tz_field_exists(self):
        """contact_local_tz must be a Selection field on res.partner."""
        field = self.env['res.partner']._fields.get('contact_local_tz')
        self.assertIsNotNone(field, "Field 'contact_local_tz' must be defined")
        self.assertEqual(field.type, 'selection')

    def test_contact_local_tz_selection_contains_utc(self):
        """The selection list must contain 'UTC'."""
        field = self.env['res.partner']._fields['contact_local_tz']
        selection = field.selection
        if callable(selection):
            selection = selection(self.partner)
        self.assertIn('UTC', [v for v, _ in selection])

    def test_contact_local_tz_selection_contains_common_timezones(self):
        """Spot-check well-known timezone strings in the selection."""
        field = self.env['res.partner']._fields['contact_local_tz']
        selection = field.selection
        if callable(selection):
            selection = selection(self.partner)
        tz_values = [v for v, _ in selection]
        for tz in ('America/New_York', 'Europe/London', 'Asia/Kolkata'):
            self.assertIn(tz, tz_values, f"'{tz}' must be in the selection list")


# ---------------------------------------------------------------------------
# 2. action_compute_contact_local_time_tz tests
# ---------------------------------------------------------------------------

class TestComputeLocalTime(TransactionCase):
    """Tests for action_compute_contact_local_time_tz()."""

    def _create_partner_with_tz(self, tz_str):
        """
        Create a partner whose contact_local_tz is set to tz_str by mocking
        geopy to return lat/lng that maps to that timezone.
        """
        geocoder, nom_cls = _make_geocoder_mock(location=_mock_location())
        tf, tf_cls = _make_tzfinder_mock(tz_str=tz_str)
        country = self.env['res.country'].search([('code', '=', 'US')], limit=1)
        with patch(GEOCODER_PATH, nom_cls), patch(TZ_FINDER_PATH, tf_cls):
            partner = self.env['res.partner'].create({
                'name': 'TZ Partner',
                'country_id': country.id,
            })
            self.env.flush_all()
        return partner

    def _compute_local_time_with_mock(self, partner, tz_str):
        """
        Call action_compute_contact_local_time_tz while keeping geopy mocked
        so that any triggered recompute still returns tz_str.
        """
        geocoder, nom_cls = _make_geocoder_mock(location=_mock_location())
        tf, tf_cls = _make_tzfinder_mock(tz_str=tz_str)
        with patch(GEOCODER_PATH, nom_cls), patch(TZ_FINDER_PATH, tf_cls):
            partner.action_compute_contact_local_time_tz()

    # --- happy paths ---

    def test_computes_local_time_when_tz_set(self):
        """contact_local_time_tz must be populated when contact_local_tz is valid."""
        partner = self._create_partner_with_tz('America/New_York')
        self.assertEqual(partner.contact_local_tz, 'America/New_York')
        self._compute_local_time_with_mock(partner, 'America/New_York')
        self.assertTrue(
            partner.contact_local_time_tz,
            "contact_local_time_tz must be non-empty after computing with a valid tz",
        )

    def test_computes_local_time_utc(self):
        """UTC timezone must produce a non-empty local time string."""
        partner = self._create_partner_with_tz('UTC')
        self._compute_local_time_with_mock(partner, 'UTC')
        self.assertTrue(partner.contact_local_time_tz)

    def test_computes_local_time_kolkata(self):
        """Asia/Kolkata (IST UTC+5:30) must produce a non-empty local time."""
        partner = self._create_partner_with_tz('Asia/Kolkata')
        self._compute_local_time_with_mock(partner, 'Asia/Kolkata')
        self.assertTrue(partner.contact_local_time_tz)

    def test_computes_local_time_london(self):
        """Europe/London must produce a non-empty local time."""
        partner = self._create_partner_with_tz('Europe/London')
        self._compute_local_time_with_mock(partner, 'Europe/London')
        self.assertTrue(partner.contact_local_time_tz)

    # --- edge / failure cases ---

    def test_no_timezone_clears_local_time(self):
        """When contact_local_tz is False, contact_local_time_tz must be cleared."""
        geocoder, nom_cls = _make_geocoder_mock(location=None)
        tf, tf_cls = _make_tzfinder_mock(tz_str=None)
        with patch(GEOCODER_PATH, nom_cls), patch(TZ_FINDER_PATH, tf_cls):
            partner = self.env['res.partner'].create({'name': 'No TZ Partner'})
            self.env.flush_all()
            self.assertFalse(partner.contact_local_tz)
            partner.action_compute_contact_local_time_tz()
        self.assertFalse(
            partner.contact_local_time_tz,
            "contact_local_time_tz must be False when no timezone is set",
        )

    def test_invalid_timezone_clears_local_time(self):
        """An invalid timezone string must not raise and must clear the field."""
        geocoder, nom_cls = _make_geocoder_mock(location=_mock_location())
        tf, tf_cls = _make_tzfinder_mock(tz_str='Invalid/Timezone_XYZ')
        country = self.env['res.country'].search([('code', '=', 'US')], limit=1)
        with patch(GEOCODER_PATH, nom_cls), patch(TZ_FINDER_PATH, tf_cls):
            partner = self.env['res.partner'].create({
                'name': 'Bad TZ Partner',
                'country_id': country.id,
            })
            self.env.flush_all()
            partner.action_compute_contact_local_time_tz()
        self.assertFalse(
            partner.contact_local_time_tz,
            "contact_local_time_tz must be False for an invalid timezone",
        )

    def test_batch_compute_multiple_partners(self):
        """action_compute_contact_local_time_tz on a multi-record set must work."""
        partner1 = self._create_partner_with_tz('America/New_York')
        partner2 = self._create_partner_with_tz('Asia/Tokyo')

        geocoder, nom_cls = _make_geocoder_mock(location=_mock_location())
        # timezone_at will be called multiple times; alternate via side_effect list
        tf = MagicMock()
        tf.timezone_at.side_effect = ['America/New_York', 'Asia/Tokyo']
        tf_cls = MagicMock(return_value=tf)

        combined = partner1 | partner2
        with patch(GEOCODER_PATH, nom_cls), patch(TZ_FINDER_PATH, tf_cls):
            combined.action_compute_contact_local_time_tz()

        self.assertTrue(partner1.contact_local_time_tz)
        self.assertTrue(partner2.contact_local_time_tz)

# ---------------------------------------------------------------------------
# 3. _get_timezone_from_address computed field tests
# ---------------------------------------------------------------------------

class TestGetTimezoneFromAddress(TransactionCase):
    """
    Tests for the _get_timezone_from_address stored computed field.
    Each test manages its own patch context to guarantee the mock is active
    during the ORM flush that triggers the computation.
    """

    def setUp(self):
        super().setUp()
        self.country_us = self.env['res.country'].search([('code', '=', 'US')], limit=1)
        self.state_ny = self.env['res.country.state'].search(
            [('country_id', '=', self.country_us.id), ('code', '=', 'NY')], limit=1
        )

    def _create_partner(self, country=None, state=None, nom_cls=None, tf_cls=None):
        """Create a partner inside an active patch context."""
        vals = {'name': 'Address Partner'}
        if country:
            vals['country_id'] = country.id
        if state:
            vals['state_id'] = state.id
        partner = self.env['res.partner'].create(vals)
        self.env.flush_all()
        return partner

    # --- successful geo-lookup ---

    def test_timezone_set_when_geocoding_succeeds(self):
        """When geopy returns a valid location, contact_local_tz must be set."""
        geocoder, nom_cls = _make_geocoder_mock(location=_mock_location(40.7128, -74.0060))
        tf, tf_cls = _make_tzfinder_mock(tz_str='America/New_York')
        with patch(GEOCODER_PATH, nom_cls), patch(TZ_FINDER_PATH, tf_cls):
            partner = self._create_partner(country=self.country_us, state=self.state_ny)
        self.assertEqual(partner.contact_local_tz, 'America/New_York')

    def test_timezone_set_for_kolkata(self):
        """A Kolkata lat/lng should result in Asia/Kolkata timezone."""
        geocoder, nom_cls = _make_geocoder_mock(location=_mock_location(22.5726, 88.3639))
        tf, tf_cls = _make_tzfinder_mock(tz_str='Asia/Kolkata')
        country_in = self.env['res.country'].search([('code', '=', 'IN')], limit=1)
        with patch(GEOCODER_PATH, nom_cls), patch(TZ_FINDER_PATH, tf_cls):
            partner = self._create_partner(country=country_in)
        self.assertEqual(partner.contact_local_tz, 'Asia/Kolkata')

    # --- geocoding returns no result ---

    def test_timezone_false_when_geocoding_returns_none(self):
        """When geopy returns None, contact_local_tz must be False."""
        geocoder, nom_cls = _make_geocoder_mock(location=None)
        tf, tf_cls = _make_tzfinder_mock(tz_str=None)
        with patch(GEOCODER_PATH, nom_cls), patch(TZ_FINDER_PATH, tf_cls):
            partner = self._create_partner(country=self.country_us)
        self.assertFalse(partner.contact_local_tz)

    def test_timezone_false_when_timezone_at_returns_none(self):
        """When timezone_at() returns None, contact_local_tz must be False."""
        geocoder, nom_cls = _make_geocoder_mock(location=_mock_location())
        tf, tf_cls = _make_tzfinder_mock(tz_str=None)
        with patch(GEOCODER_PATH, nom_cls), patch(TZ_FINDER_PATH, tf_cls):
            partner = self._create_partner(country=self.country_us, state=self.state_ny)
        self.assertFalse(partner.contact_local_tz)

    # --- partner with no country / state ---

    def test_timezone_false_for_partner_with_no_address(self):
        """A partner with no country or state must produce False timezone."""
        geocoder, nom_cls = _make_geocoder_mock(location=None)
        tf, tf_cls = _make_tzfinder_mock(tz_str=None)
        with patch(GEOCODER_PATH, nom_cls), patch(TZ_FINDER_PATH, tf_cls):
            partner = self._create_partner()
        self.assertFalse(partner.contact_local_tz)

    # --- recompute on field change ---

    def test_recompute_triggered_on_country_change(self):
        """Changing country_id must re-trigger _get_timezone_from_address."""
        geocoder, nom_cls = _make_geocoder_mock(location=None)
        tf, tf_cls = _make_tzfinder_mock(tz_str=None)
        with patch(GEOCODER_PATH, nom_cls), patch(TZ_FINDER_PATH, tf_cls):
            partner = self._create_partner()
            self.assertFalse(partner.contact_local_tz)

            # Now update mock to return a valid timezone and change the country
            geocoder.geocode.return_value = _mock_location(51.5074, -0.1278)
            tf.timezone_at.return_value = 'Europe/London'
            country_gb = self.env['res.country'].search([('code', '=', 'GB')], limit=1)
            partner.write({'country_id': country_gb.id})
            self.env.flush_all()

        self.assertEqual(partner.contact_local_tz, 'Europe/London')

    def test_recompute_triggered_on_state_change(self):
        """Changing state_id must re-trigger _get_timezone_from_address."""
        geocoder, nom_cls = _make_geocoder_mock(location=_mock_location(34.0522, -118.2437))
        tf, tf_cls = _make_tzfinder_mock(tz_str='America/Los_Angeles')
        state_ca = self.env['res.country.state'].search(
            [('country_id', '=', self.country_us.id), ('code', '=', 'CA')], limit=1
        )
        with patch(GEOCODER_PATH, nom_cls), patch(TZ_FINDER_PATH, tf_cls):
            partner = self._create_partner(country=self.country_us)
            partner.write({'state_id': state_ca.id})
            self.env.flush_all()
        self.assertEqual(partner.contact_local_tz, 'America/Los_Angeles')

    # --- address string construction ---

    def test_geocode_called_with_country_and_state(self):
        """geocode() must be called with a string containing country and state names."""
        geocoder, nom_cls = _make_geocoder_mock(location=None)
        tf, tf_cls = _make_tzfinder_mock(tz_str=None)
        with patch(GEOCODER_PATH, nom_cls), patch(TZ_FINDER_PATH, tf_cls):
            partner = self._create_partner(country=self.country_us, state=self.state_ny)

        calls = geocoder.geocode.call_args_list
        self.assertTrue(calls, "geocode() must have been called at least once")
        called_address = calls[-1][0][0]
        self.assertIn(self.country_us.name, called_address)
        self.assertIn(self.state_ny.name, called_address)

# ---------------------------------------------------------------------------
# 4. Integration: full address → timezone → local time flow
# ---------------------------------------------------------------------------

class TestIntegrationComputeFlow(TransactionCase):
    """End-to-end: address resolves to timezone (mocked), then local time is computed."""

    def setUp(self):
        super().setUp()
        self.country_us = self.env['res.country'].search([('code', '=', 'US')], limit=1)
        self.state_ny = self.env['res.country.state'].search(
            [('country_id', '=', self.country_us.id), ('code', '=', 'NY')], limit=1
        )

    def test_full_flow_address_to_local_time(self):
        """Full flow: address → timezone (mock) → local time populated."""
        geocoder, nom_cls = _make_geocoder_mock(location=_mock_location(40.7128, -74.0060))
        tf, tf_cls = _make_tzfinder_mock(tz_str='America/New_York')
        with patch(GEOCODER_PATH, nom_cls), patch(TZ_FINDER_PATH, tf_cls):
            partner = self.env['res.partner'].create({
                'name': 'Integration Partner',
                'country_id': self.country_us.id,
                'state_id': self.state_ny.id,
            })
            self.env.flush_all()
            self.assertEqual(partner.contact_local_tz, 'America/New_York')
            partner.action_compute_contact_local_time_tz()

        self.assertTrue(
            partner.contact_local_time_tz,
            "contact_local_time_tz must be set after the full compute flow",
        )

    def test_full_flow_geocoding_fails_then_no_local_time(self):
        """When geocoding fails, both timezone and local time must remain False."""
        geocoder, nom_cls = _make_geocoder_mock(location=None)
        tf, tf_cls = _make_tzfinder_mock(tz_str=None)
        with patch(GEOCODER_PATH, nom_cls), patch(TZ_FINDER_PATH, tf_cls):
            partner = self.env['res.partner'].create({
                'name': 'No Address Partner',
                'country_id': self.country_us.id,
            })
            self.env.flush_all()
            self.assertFalse(partner.contact_local_tz)
            partner.action_compute_contact_local_time_tz()

        self.assertFalse(partner.contact_local_time_tz)

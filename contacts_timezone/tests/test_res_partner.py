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
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'contacts_timezone')
class TestResPartnerTimezone(TransactionCase):
    """Tests for the contacts_timezone module's ResPartner extension."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a partner with India state+country (used across many tests)
        cls.country_india = cls.env.ref('base.in')
        cls.state_kerala = cls.env['res.country.state'].search(
            [('country_id', '=', cls.country_india.id), ('name', 'ilike', 'Kerala')],
            limit=1,
        )
        cls.partner_india = cls.env['res.partner'].create({
            'name': 'Test Partner India',
            'country_id': cls.country_india.id,
            'state_id': cls.state_kerala.id if cls.state_kerala else False,
        })

        cls.country_us = cls.env.ref('base.us')
        cls.state_ny = cls.env['res.country.state'].search(
            [('country_id', '=', cls.country_us.id), ('name', 'ilike', 'New York')],
            limit=1,
        )
        cls.partner_us = cls.env['res.partner'].create({
            'name': 'Test Partner US',
            'country_id': cls.country_us.id,
            'state_id': cls.state_ny.id if cls.state_ny else False,
        })

        # Partner with no address information
        cls.partner_no_address = cls.env['res.partner'].create({
            'name': 'Test Partner No Address',
        })

    # ------------------------------------------------------------------
    # 1. Field presence tests
    # ------------------------------------------------------------------

    def test_field_contact_local_time_tz_exists(self):
        """contact_local_time_tz Char field must exist on res.partner."""
        partner = self.partner_india
        self.assertIn(
            'contact_local_time_tz',
            partner._fields,
            "Field 'contact_local_time_tz' should be defined on res.partner",
        )

    def test_field_contact_local_tz_exists(self):
        """contact_local_tz Selection field must exist on res.partner."""
        partner = self.partner_india
        self.assertIn(
            'contact_local_tz',
            partner._fields,
            "Field 'contact_local_tz' should be defined on res.partner",
        )

    def test_field_contact_local_time_tz_is_char(self):
        """contact_local_time_tz must be a Char field."""
        field = self.partner_india._fields['contact_local_time_tz']
        self.assertEqual(field.type, 'char')

    def test_field_contact_local_tz_is_selection(self):
        """contact_local_tz must be a Selection field."""
        field = self.partner_india._fields['contact_local_tz']
        self.assertEqual(field.type, 'selection')

    def test_field_contact_local_time_tz_readonly(self):
        """contact_local_time_tz must be readonly."""
        field = self.partner_india._fields['contact_local_time_tz']
        self.assertTrue(field.readonly)

    def test_field_contact_local_tz_readonly(self):
        """contact_local_tz must be readonly."""
        field = self.partner_india._fields['contact_local_tz']
        self.assertTrue(field.readonly)

    def test_field_contact_local_tz_contains_valid_timezones(self):
        """Selection choices for contact_local_tz must include common timezones."""
        import pytz
        field = self.partner_india._fields['contact_local_tz']
        selection_keys = [k for k, _ in field.selection(self.partner_india)]
        for tz in ('Asia/Kolkata', 'America/New_York', 'Europe/London', 'UTC'):
            self.assertIn(tz, selection_keys, f"Timezone '{tz}' missing from selection")

    def test_fields_default_to_false_on_new_partner(self):
        """Newly created partners must have both timezone fields unset."""
        partner = self.env['res.partner'].create({'name': 'Brand New Partner'})
        self.assertFalse(partner.contact_local_tz)
        self.assertFalse(partner.contact_local_time_tz)

    # ------------------------------------------------------------------
    # 2. action_compute_contact_local_time_tz — happy path
    # ------------------------------------------------------------------

    def _make_mock_location(self, lat, lng):
        loc = MagicMock()
        loc.latitude = lat
        loc.longitude = lng
        return loc

    @patch('odoo.addons.contacts_timezone.models.res_partner.Nominatim')
    @patch('odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder')
    def test_compute_sets_timezone_for_india(self, mock_tf_cls, mock_nom_cls):
        """action_compute should set Asia/Kolkata for an India partner."""
        mock_geocoder = MagicMock()
        mock_nom_cls.return_value = mock_geocoder
        mock_geocoder.geocode.return_value = self._make_mock_location(10.8505, 76.2711)

        mock_tf = MagicMock()
        mock_tf_cls.return_value = mock_tf
        mock_tf.timezone_at.return_value = 'Asia/Kolkata'

        self.partner_india.action_compute_contact_local_time_tz()

        self.assertEqual(self.partner_india.contact_local_tz, 'Asia/Kolkata')

    @patch('odoo.addons.contacts_timezone.models.res_partner.Nominatim')
    @patch('odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder')
    def test_compute_sets_local_time_format(self, mock_tf_cls, mock_nom_cls):
        """contact_local_time_tz must follow 'YYYY-MM-DD HH:MM:SS' format."""
        import re
        mock_geocoder = MagicMock()
        mock_nom_cls.return_value = mock_geocoder
        mock_geocoder.geocode.return_value = self._make_mock_location(40.7128, -74.0060)

        mock_tf = MagicMock()
        mock_tf_cls.return_value = mock_tf
        mock_tf.timezone_at.return_value = 'America/New_York'

        self.partner_us.action_compute_contact_local_time_tz()

        pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'
        self.assertRegex(
            self.partner_us.contact_local_time_tz,
            pattern,
            "Local time must be formatted as YYYY-MM-DD HH:MM:SS",
        )

    @patch('odoo.addons.contacts_timezone.models.res_partner.Nominatim')
    @patch('odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder')
    def test_compute_sets_timezone_for_us(self, mock_tf_cls, mock_nom_cls):
        """action_compute should set America/New_York for a New York partner."""
        mock_geocoder = MagicMock()
        mock_nom_cls.return_value = mock_geocoder
        mock_geocoder.geocode.return_value = self._make_mock_location(40.7128, -74.0060)

        mock_tf = MagicMock()
        mock_tf_cls.return_value = mock_tf
        mock_tf.timezone_at.return_value = 'America/New_York'

        self.partner_us.action_compute_contact_local_time_tz()

        self.assertEqual(self.partner_us.contact_local_tz, 'America/New_York')
        self.assertTrue(self.partner_us.contact_local_time_tz)

    @patch('odoo.addons.contacts_timezone.models.res_partner.Nominatim')
    @patch('odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder')
    def test_compute_resets_fields_before_each_call(self, mock_tf_cls, mock_nom_cls):
        """Every call must reset both fields before computing new values."""
        # First call sets a value
        mock_geocoder = MagicMock()
        mock_nom_cls.return_value = mock_geocoder
        mock_geocoder.geocode.return_value = self._make_mock_location(10.0, 76.0)
        mock_tf = MagicMock()
        mock_tf_cls.return_value = mock_tf
        mock_tf.timezone_at.return_value = 'Asia/Kolkata'
        self.partner_india.action_compute_contact_local_time_tz()
        self.assertEqual(self.partner_india.contact_local_tz, 'Asia/Kolkata')

        # Second call with geocoder returning nothing should blank the fields
        mock_geocoder.geocode.return_value = None
        self.partner_india.action_compute_contact_local_time_tz()
        self.assertFalse(self.partner_india.contact_local_tz)
        self.assertFalse(self.partner_india.contact_local_time_tz)

    # ------------------------------------------------------------------
    # 3. action_compute_contact_local_time_tz — edge cases / failures
    # ------------------------------------------------------------------

    @patch('odoo.addons.contacts_timezone.models.res_partner.Nominatim')
    @patch('odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder')
    def test_compute_geocode_returns_none(self, mock_tf_cls, mock_nom_cls):
        """When geocoder finds nothing, fields must remain False."""
        mock_geocoder = MagicMock()
        mock_nom_cls.return_value = mock_geocoder
        mock_geocoder.geocode.return_value = None

        mock_tf_cls.return_value = MagicMock()

        self.partner_india.action_compute_contact_local_time_tz()

        self.assertFalse(self.partner_india.contact_local_tz)
        self.assertFalse(self.partner_india.contact_local_time_tz)

    @patch('odoo.addons.contacts_timezone.models.res_partner.Nominatim')
    @patch('odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder')
    def test_compute_timezone_finder_returns_none(self, mock_tf_cls, mock_nom_cls):
        """When TimezoneFinder returns None, fields must remain False."""
        mock_geocoder = MagicMock()
        mock_nom_cls.return_value = mock_geocoder
        mock_geocoder.geocode.return_value = self._make_mock_location(0.0, 0.0)

        mock_tf = MagicMock()
        mock_tf_cls.return_value = mock_tf
        mock_tf.timezone_at.return_value = None

        self.partner_india.action_compute_contact_local_time_tz()

        self.assertFalse(self.partner_india.contact_local_tz)
        self.assertFalse(self.partner_india.contact_local_time_tz)

    @patch('odoo.addons.contacts_timezone.models.res_partner.Nominatim')
    @patch('odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder')
    def test_compute_geocoder_raises_exception(self, mock_tf_cls, mock_nom_cls):
        """Exceptions from the geocoder must be caught; fields stay False."""
        mock_geocoder = MagicMock()
        mock_nom_cls.return_value = mock_geocoder
        mock_geocoder.geocode.side_effect = Exception("Network error")

        mock_tf_cls.return_value = MagicMock()

        # Must NOT raise; exception is caught internally
        try:
            self.partner_india.action_compute_contact_local_time_tz()
        except Exception:
            self.fail("action_compute_contact_local_time_tz raised an unexpected exception")

        self.assertFalse(self.partner_india.contact_local_tz)
        self.assertFalse(self.partner_india.contact_local_time_tz)

    @patch('odoo.addons.contacts_timezone.models.res_partner.Nominatim')
    @patch('odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder')
    def test_compute_partner_with_no_address(self, mock_tf_cls, mock_nom_cls):
        """Partner without state/country: geocode is called with empty address; fields stay False."""
        mock_geocoder = MagicMock()
        mock_nom_cls.return_value = mock_geocoder
        mock_geocoder.geocode.return_value = None

        mock_tf_cls.return_value = MagicMock()

        self.partner_no_address.action_compute_contact_local_time_tz()

        self.assertFalse(self.partner_no_address.contact_local_tz)
        self.assertFalse(self.partner_no_address.contact_local_time_tz)

    # ------------------------------------------------------------------
    # 4. Address building for geocoding
    # ------------------------------------------------------------------

    @patch('odoo.addons.contacts_timezone.models.res_partner.Nominatim')
    @patch('odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder')
    def test_geocode_address_uses_state_and_country(self, mock_tf_cls, mock_nom_cls):
        """Geocoder must receive 'State, Country' as the address string."""
        mock_geocoder = MagicMock()
        mock_nom_cls.return_value = mock_geocoder
        mock_geocoder.geocode.return_value = None
        mock_tf_cls.return_value = MagicMock()

        self.partner_india.action_compute_contact_local_time_tz()

        call_args = mock_geocoder.geocode.call_args
        geocoded_address = call_args[0][0]

        if self.state_kerala:
            self.assertIn(self.state_kerala.name, geocoded_address)
        self.assertIn(self.country_india.name, geocoded_address)

    @patch('odoo.addons.contacts_timezone.models.res_partner.Nominatim')
    @patch('odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder')
    def test_geocode_address_only_country_when_no_state(self, mock_tf_cls, mock_nom_cls):
        """When state is absent, address must be just the country name."""
        partner = self.env['res.partner'].create({
            'name': 'No State Partner',
            'country_id': self.country_us.id,
        })

        mock_geocoder = MagicMock()
        mock_nom_cls.return_value = mock_geocoder
        mock_geocoder.geocode.return_value = None
        mock_tf_cls.return_value = MagicMock()

        partner.action_compute_contact_local_time_tz()

        call_args = mock_geocoder.geocode.call_args
        geocoded_address = call_args[0][0]

        # Should be just the country name, no leading comma
        self.assertFalse(geocoded_address.startswith(','))
        self.assertIn(self.country_us.name, geocoded_address)

    # ------------------------------------------------------------------
    # 5. Batch / multi-record processing
    # ------------------------------------------------------------------

    @patch('odoo.addons.contacts_timezone.models.res_partner.Nominatim')
    @patch('odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder')
    def test_compute_on_multiple_records(self, mock_tf_cls, mock_nom_cls):
        """action_compute must process every record in a multi-record set."""
        partner_a = self.env['res.partner'].create({
            'name': 'Batch A',
            'country_id': self.country_india.id,
        })
        partner_b = self.env['res.partner'].create({
            'name': 'Batch B',
            'country_id': self.country_us.id,
        })

        mock_geocoder = MagicMock()
        mock_nom_cls.return_value = mock_geocoder
        mock_geocoder.geocode.return_value = self._make_mock_location(10.0, 76.0)

        mock_tf = MagicMock()
        mock_tf_cls.return_value = mock_tf
        mock_tf.timezone_at.return_value = 'Asia/Kolkata'

        batch = partner_a | partner_b
        batch.action_compute_contact_local_time_tz()

        self.assertEqual(mock_geocoder.geocode.call_count, 2,
                         "geocode must be called once per partner in the recordset")
        for partner in batch:
            self.assertEqual(partner.contact_local_tz, 'Asia/Kolkata')
            self.assertTrue(partner.contact_local_time_tz)

    @patch('odoo.addons.contacts_timezone.models.res_partner.Nominatim')
    @patch('odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder')
    def test_one_failure_does_not_abort_batch(self, mock_tf_cls, mock_nom_cls):
        """An exception on one record must not prevent others from being processed."""
        partner_ok = self.env['res.partner'].create({
            'name': 'OK Partner',
            'country_id': self.country_india.id,
        })
        partner_bad = self.env['res.partner'].create({
            'name': 'Bad Partner',
            'country_id': self.country_us.id,
        })

        mock_geocoder = MagicMock()
        mock_nom_cls.return_value = mock_geocoder

        mock_tf = MagicMock()
        mock_tf_cls.return_value = mock_tf

        # First call raises, second succeeds
        mock_geocoder.geocode.side_effect = [
            Exception("Geocode failed"),
            self._make_mock_location(10.0, 76.0),
        ]
        mock_tf.timezone_at.return_value = 'Asia/Kolkata'

        batch = partner_bad | partner_ok
        try:
            batch.action_compute_contact_local_time_tz()
        except Exception:
            self.fail("A single partner failure must not propagate out of the method")

    # ------------------------------------------------------------------
    # 6. Nominatim user_agent
    # ------------------------------------------------------------------

    @patch('odoo.addons.contacts_timezone.models.res_partner.Nominatim')
    @patch('odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder')
    def test_nominatim_user_agent_set(self, mock_tf_cls, mock_nom_cls):
        """Nominatim must be instantiated with a non-empty user_agent."""
        mock_geocoder = MagicMock()
        mock_nom_cls.return_value = mock_geocoder
        mock_geocoder.geocode.return_value = None
        mock_tf_cls.return_value = MagicMock()

        self.partner_india.action_compute_contact_local_time_tz()

        _, kwargs = mock_nom_cls.call_args
        self.assertIn('user_agent', kwargs)
        self.assertTrue(kwargs['user_agent'])

    # ------------------------------------------------------------------
    # 7. Timezone correctness (no external calls needed)
    # ------------------------------------------------------------------

    @patch('odoo.addons.contacts_timezone.models.res_partner.Nominatim')
    @patch('odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder')
    def test_local_time_is_timezone_aware(self, mock_tf_cls, mock_nom_cls):
        """The stored local time string must correspond to the set timezone."""
        import pytz
        from datetime import datetime

        tz_str = 'Asia/Kolkata'

        mock_geocoder = MagicMock()
        mock_nom_cls.return_value = mock_geocoder
        mock_geocoder.geocode.return_value = self._make_mock_location(10.0, 76.0)

        mock_tf = MagicMock()
        mock_tf_cls.return_value = mock_tf
        mock_tf.timezone_at.return_value = tz_str

        self.partner_india.action_compute_contact_local_time_tz()

        stored = self.partner_india.contact_local_time_tz
        self.assertTrue(stored, "contact_local_time_tz must not be empty after a successful compute")

        # Stored time should be parseable
        try:
            datetime.strptime(stored, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            self.fail(f"Stored time '{stored}' is not in '%Y-%m-%d %H:%M:%S' format")

    @patch('odoo.addons.contacts_timezone.models.res_partner.Nominatim')
    @patch('odoo.addons.contacts_timezone.models.res_partner.TimezoneFinder')
    def test_timezone_finder_receives_correct_coordinates(self, mock_tf_cls, mock_nom_cls):
        """TimezoneFinder.timezone_at must be called with the geocoded lat/lng."""
        lat, lng = 48.8566, 2.3522

        mock_geocoder = MagicMock()
        mock_nom_cls.return_value = mock_geocoder
        mock_geocoder.geocode.return_value = self._make_mock_location(lat, lng)

        mock_tf = MagicMock()
        mock_tf_cls.return_value = mock_tf
        mock_tf.timezone_at.return_value = 'Europe/Paris'

        partner = self.env['res.partner'].create({
            'name': 'Paris Partner',
            'country_id': self.env.ref('base.fr').id,
        })
        partner.action_compute_contact_local_time_tz()

        mock_tf.timezone_at.assert_called_once_with(lat=lat, lng=lng)
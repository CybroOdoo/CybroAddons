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
from datetime import UTC, datetime

import pytz
from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestSystrayWorldClock(TransactionCase):
    """Test suite for Systray World Clock Configuration."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ClockConfig = cls.env['systray.world.clock.config']

    def test_01_create_and_onchange_utc(self):
        """Test clock creation and timezone offset calculation for UTC."""
        clock = self.ClockConfig.create({
            'name': 'UTC Clock',
            'tz': 'UTC',
        })
        clock._onchange_tz()
        self.assertEqual(clock.name, 'UTC Clock')
        self.assertEqual(clock.tz, 'UTC')
        self.assertEqual(clock.offset, 0.0)

    def test_02_onchange_tz_positive_offset(self):
        """Test timezone offset calculation for Asia/Kolkata (+5.5 hours)."""
        clock = self.ClockConfig.create({
            'name': 'Kolkata Clock',
            'tz': 'Asia/Kolkata',
        })
        clock._onchange_tz()
        self.assertEqual(clock.offset, 5.5)

    def test_03_onchange_tz_matches_expected_offset(self):
        """Test timezone offset dynamically matches pytz calculation."""
        for tz_name in ['America/New_York', 'Europe/London', 'Asia/Tokyo']:
            clock = self.ClockConfig.create({
                'name': f'{tz_name} Clock',
                'tz': tz_name,
            })
            clock._onchange_tz()

            tz = pytz.timezone(tz_name)
            now_utc = datetime.now(UTC)
            local_dt = now_utc.astimezone(tz)
            expected_offset = local_dt.utcoffset().total_seconds() / 3600
            self.assertEqual(clock.offset, expected_offset)

    def test_04_onchange_tz_empty(self):
        """Test onchange behavior when timezone is unset."""
        clock = self.ClockConfig.new({
            'name': 'No TZ Clock',
            'tz': False,
            'offset': 2.0,
        })
        clock._onchange_tz()
        self.assertEqual(clock.offset, 0.0)

    def test_05_search_read_systray_fields(self):
        """Test search_read query matches fields requested by systray UI."""
        self.ClockConfig.create([
            {'name': 'London', 'tz': 'Europe/London', 'offset': 0.0},
            {'name': 'Tokyo', 'tz': 'Asia/Tokyo', 'offset': 9.0},
        ])
        results = self.ClockConfig.search_read([], fields=['name', 'tz', 'offset'])
        self.assertTrue(len(results) >= 2)
        fields_in_record = results[0].keys()
        self.assertIn('name', fields_in_record)
        self.assertIn('tz', fields_in_record)
        self.assertIn('offset', fields_in_record)

    def test_06_required_fields_validation(self):
        """Test that omitting required fields raises an integrity error."""
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.ClockConfig.create({'tz': 'UTC'})

        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError):
            with self.cr.savepoint():
                self.ClockConfig.create({'name': 'Missing TZ'})

    def test_07_multi_record_crud(self):
        """Test creation, modification, and deletion across multiple records."""
        clocks = self.ClockConfig.create([
            {'name': 'Clock A', 'tz': 'UTC', 'offset': 0.0},
            {'name': 'Clock B', 'tz': 'Asia/Kolkata', 'offset': 5.5},
        ])
        self.assertEqual(len(clocks), 2)

        clocks.write({'name': 'Updated Clock'})
        self.assertTrue(all(name == 'Updated Clock' for name in clocks.mapped('name')))

        clocks.unlink()
        remaining = self.ClockConfig.search([('id', 'in', clocks.ids)])
        self.assertFalse(remaining)

    def test_08_multi_record_compute_offset(self):
        """Test stored compute method across multiple records."""
        clocks = self.ClockConfig.create([
            {'name': 'London', 'tz': 'UTC'},
            {'name': 'India', 'tz': 'Asia/Kolkata'},
        ])
        # Auto-computed on create
        self.assertEqual(clocks[0].offset, 0.0)
        self.assertEqual(clocks[1].offset, 5.5)

        # Trigger multi-recordset compute directly
        clocks._compute_offset()
        self.assertEqual(clocks[0].offset, 0.0)
        self.assertEqual(clocks[1].offset, 5.5)

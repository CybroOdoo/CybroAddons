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
from datetime import datetime

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import format_datetime


@tagged('post_install', '-at_install')
class TestEventEvent(TransactionCase):
    """Unit tests for the event.event model extensions."""

    @classmethod
    def setUpClass(cls):
        """Set up sample events for date localization tests."""
        super().setUpClass()
        cls.event_utc = cls.env['event.event'].create({
            'name': 'UTC Calendar Event',
            'date_begin': datetime(2026, 11, 15, 10, 30, 0),
            'date_end': datetime(2026, 11, 16, 12, 0, 0),
            'date_tz': 'UTC',
        })
        cls.event_ny = cls.env['event.event'].create({
            'name': 'New York Calendar Event',
            'date_begin': datetime(2026, 12, 1, 15, 0, 0),
            'date_end': datetime(2026, 12, 2, 17, 0, 0),
            'date_tz': 'America/New_York',
        })

    def test_compute_date_begin_pred_located(self):
        """Verify _compute_date_begin_pred_located formats date_begin in event timezone."""
        expected_utc = format_datetime(
            self.env,
            self.event_utc.date_begin,
            tz='UTC',
            dt_format='medium',
        )
        self.assertEqual(self.event_utc.date_begin_pred_located, expected_utc)

        # Updating timezone should recompute the localized string
        self.event_utc.write({'date_tz': 'Asia/Kolkata'})
        expected_ist = format_datetime(
            self.env,
            self.event_utc.date_begin,
            tz='Asia/Kolkata',
            dt_format='medium',
        )
        self.assertEqual(self.event_utc.date_begin_pred_located, expected_ist)
        self.assertNotEqual(self.event_utc.date_begin_pred_located, expected_utc)

        # Updating date_begin should recompute the localized string
        new_begin = datetime(2026, 11, 20, 8, 0, 0)
        self.event_utc.write({'date_begin': new_begin, 'date_end': datetime(2026, 11, 21, 8, 0, 0)})
        expected_updated = format_datetime(
            self.env,
            new_begin,
            tz='Asia/Kolkata',
            dt_format='medium',
        )
        self.assertEqual(self.event_utc.date_begin_pred_located, expected_updated)

        # Batch computation across multiple records
        events = self.event_utc + self.event_ny
        events._compute_date_begin_pred_located()
        expected_ny = format_datetime(
            self.env,
            self.event_ny.date_begin,
            tz='America/New_York',
            dt_format='medium',
        )
        self.assertEqual(self.event_ny.date_begin_pred_located, expected_ny)

        # Empty date_begin should compute to an empty string
        empty_event = self.env['event.event'].new({'name': 'Undated Event', 'date_begin': False})
        empty_event._compute_date_begin_pred_located()
        self.assertEqual(empty_event.date_begin_pred_located, '')


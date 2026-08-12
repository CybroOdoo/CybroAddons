# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#############################################################################
import pytz
from datetime import datetime
from odoo.tests.common import TransactionCase
from odoo.tests import tagged, Form


@tagged('post_install', '-at_install')
class TestSystrayWorldClockConfig(TransactionCase):
    """Test cases for the Systray World Clock Configuration model."""

    def test_create_world_clock_config(self):
        """Test basic creation of world clock config record."""
        config = self.env['systray.world.clock.config'].create({
            'name': 'London',
            'tz': 'Europe/London',
            'offset': 1.0,
        })
        self.assertEqual(config.name, 'London')
        self.assertEqual(config.tz, 'Europe/London')
        self.assertEqual(config.offset, 1.0)

    def test_onchange_tz(self):
        """Test that offset is calculated correctly via onchange."""
        with Form(self.env['systray.world.clock.config']) as form:
            form.name = 'Tokyo'
            form.tz = 'Asia/Tokyo'
        config = form.save()

        # Calculate expected offset using pytz
        utc_dt = pytz.utc.localize(datetime.utcnow())
        tz = pytz.timezone('Asia/Tokyo')
        local_dt = utc_dt.astimezone(tz)
        expected_offset = local_dt.utcoffset().total_seconds() / 3600

        self.assertEqual(
            config.offset,
            expected_offset,
            "The offset should be calculated correctly via onchange."
        )

    def test_onchange_tz_empty(self):
        """Test onchange behavior when timezone is unset."""
        config = self.env['systray.world.clock.config'].create({
            'name': 'No timezone',
            'tz': 'Europe/London',
            'offset': 1.0,
        })
        config.tz = False
        config._onchange_tz()
        self.assertEqual(
            config.offset,
            1.0,
            "Offset should be unchanged if timezone is empty."
        )

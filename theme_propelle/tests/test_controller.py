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
from datetime import date

from odoo.tests import TransactionCase, tagged

from odoo.addons.theme_propelle.controllers.theme_propelle import (
    PropelleWebsite)


@tagged('post_install', '-at_install')
class TestPropelleController(TransactionCase):
    """Test the helpers of the controller."""

    def test_open_hours(self):
        """Weekdays open 9 to 5, Saturday 10 to 3, Sunday closed."""
        monday, saturday, sunday = (
            date(2026, 11, 16), date(2026, 11, 21), date(2026, 11, 22))
        self.assertEqual(PropelleWebsite._open_hours(monday)[0], 9)
        self.assertEqual(PropelleWebsite._open_hours(monday)[-1], 17)
        self.assertEqual(PropelleWebsite._open_hours(saturday)[0], 10)
        self.assertEqual(PropelleWebsite._open_hours(saturday)[-1], 15)
        self.assertEqual(PropelleWebsite._open_hours(sunday), ())

    def test_hour_label(self):
        """Hours are written in the twelve hour clock."""
        label = PropelleWebsite._hour_label
        self.assertEqual(label(9), '9:00 am')
        self.assertEqual(label(12), '12:00 pm')
        self.assertEqual(label(15), '3:00 pm')

    def test_to_int(self):
        """A posted value becomes an integer, or 0 when it is not one."""
        to_int = PropelleWebsite._to_int
        self.assertEqual(to_int('12'), 12)
        self.assertEqual(to_int(7), 7)
        self.assertEqual(to_int('abc'), 0)
        self.assertEqual(to_int(None), 0)
        self.assertEqual(to_int(''), 0)

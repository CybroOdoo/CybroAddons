# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase, tagged

from ..models.utils import get_param, set_param, to_bool


@tagged('post_install', '-at_install')
class TestUtils(TransactionCase):

    def test_to_bool(self):
        for value in ('1', 'true', 'True', ' YES ', 'on', True, 1):
            self.assertTrue(to_bool(value), value)
        for value in ('', '0', 'false', 'no', 'off', False, None, 0):
            self.assertFalse(to_bool(value), value)

    def test_set_and_get_param(self):
        key = 'backend_theme_infinito_plus.test_key'
        set_param(self.env, key, 'Top Left')
        self.assertEqual(get_param(self.env, key), 'Top Left')
        set_param(self.env, key, 42)
        self.assertEqual(get_param(self.env, key), '42')

    def test_empty_values_are_cleared(self):
        key = 'backend_theme_infinito_plus.test_key'
        for empty in (False, None, 0, '0', 'False', 'false'):
            set_param(self.env, key, 'something')
            set_param(self.env, key, empty)
            self.assertFalse(get_param(self.env, key), empty)

    def test_get_param_default(self):
        key = 'backend_theme_infinito_plus.missing_key'
        self.assertFalse(get_param(self.env, key))
        self.assertEqual(get_param(self.env, key, default='x'), 'x')
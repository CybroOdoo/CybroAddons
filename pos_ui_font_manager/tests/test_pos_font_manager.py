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
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosFontManager(TransactionCase):
    """Tests for the POS font size configuration."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env['pos.config'].create({'name': 'Font Test POS'})

    def test_defaults(self):
        """New configurations use the medium preset at 100% scale."""
        self.assertEqual(self.config.pos_font_preset, 'medium')
        self.assertEqual(self.config.pos_global_scale, 100)
        self.assertEqual(self.config.pos_product_card_font_size, 0)
        self.assertEqual(self.config.pos_popups_dialogs_font_size, 0)

    def test_write_preset_and_sizes(self):
        """Preset and custom sizes can be stored on the configuration."""
        self.config.write({
            'pos_font_preset': 'custom',
            'pos_global_scale': 120,
            'pos_product_card_font_size': 18,
            'pos_payment_total_font_size': 72,
        })
        self.assertEqual(self.config.pos_font_preset, 'custom')
        self.assertEqual(self.config.pos_global_scale, 120)
        self.assertEqual(self.config.pos_product_card_font_size, 18)
        self.assertEqual(self.config.pos_payment_total_font_size, 72)

    def test_settings_write_through(self):
        """Settings fields are related to the POS configuration."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.config.id,
            'pos_font_preset': 'large',
            'pos_global_scale': 110,
        })
        self.assertEqual(settings.pos_font_preset, 'large')
        self.assertEqual(self.config.pos_font_preset, 'large')
        self.assertEqual(self.config.pos_global_scale, 110)

    def test_invalid_global_scale(self):
        """A scale outside 10-300% is rejected."""
        with self.assertRaises(ValidationError):
            self.config.pos_global_scale = 0
        with self.assertRaises(ValidationError):
            self.config.pos_global_scale = 500

    def test_invalid_font_size(self):
        """Negative or oversized pixel values are rejected."""
        with self.assertRaises(ValidationError):
            self.config.pos_navbar_font_size = -1
        with self.assertRaises(ValidationError):
            self.config.pos_numpad_font_size = 500

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from odoo.addons.pharmaceutical_base.models.pharma_measured_value_mixin import device_capture
from odoo.addons.pharmaceutical_base.models.pharma_value_source import PharmaValueSource

from .common import PharmaTestCommon


@tagged('post_install', '-at_install')
class TestPremiumFeature(PharmaTestCommon):
    """The premium add-on catalogue behind the Learn more dialogs."""

    @classmethod
    def setUpClass(cls):
        """Load the Device Capture feature and an administrator."""
        super().setUpClass()
        cls.feature = cls.env.ref('pharmaceutical_base.pharma_premium_feature_device_capture')
        cls.admin = cls.env.ref('base.user_admin')
        cls.missing = cls.env['pharma.premium.feature'].create({
            'name': 'Ghost', 'code': 'ghost', 'module_name': 'pharma_no_such_module',
        })

    def test_module_state(self):
        """The add-on state follows the module list."""
        self.assertIn(self.feature.module_state, ('available', 'not_available', 'installed'))
        self.assertEqual(self.missing.module_state, 'not_available')
        self.assertFalse(self.missing.is_installed)
        Feature = self.env['pharma.premium.feature']
        self.assertFalse(Feature._pharma_feature_installed('ghost'))
        self.assertFalse(Feature._pharma_feature_installed('unknown_code'))
        base = Feature.create({'name': 'Base', 'code': 'base_mod', 'module_name': 'pharmaceutical_base'})
        self.assertTrue(base.is_installed)

    def test_dialog_and_purchase(self):
        """Learn more opens the dialog; the purchase button opens the Apps page."""
        action = self.env['pharma.premium.feature'].action_open_dialog_by_code('device_capture')
        self.assertEqual((action['res_id'], action['target']), (self.feature.id, 'new'))
        with self.assertRaises(UserError):
            self.env['pharma.premium.feature'].action_open_dialog_by_code('unknown_code')
        self.assertEqual(self.feature.action_open_purchase()['url'], self.feature.purchase_url)
        with self.assertRaises(UserError):
            self.missing.action_open_purchase()

    def test_install_guards(self):
        """Only an administrator installs, and only a module on the server."""
        with self.assertRaises(UserError):
            self.missing.with_user(self.operator).action_install()
        with self.assertRaises(UserError):
            self.missing.with_user(self.admin).action_install()


@tagged('post_install', '-at_install')
class TestValueSource(PharmaTestCommon):
    """Measurement sources and the origin of measured values."""

    def test_sources_locked_without_addon(self):
        """Without Device Capture no source can be registered and views hide create."""
        Source = self.env['pharma.value.source']
        with self.assertRaises(UserError):
            Source.create({'name': 'Balance', 'code': 'BAL-1'})
        arch = Source.get_views([(False, 'list')])['views']['list']['arch']
        self.assertIn('create="0"', arch)
        self.assertIn('Device Capture is a premium add-on', Source.get_empty_list_help(''))

    def test_device_captured_value(self):
        """A value written inside device_capture is stamped with its source."""
        with patch.object(PharmaValueSource, '_pharma_device_capture_enabled', return_value=True):
            source = self.env['pharma.value.source'].create({'name': 'Balance', 'code': 'BAL-1'})
            self.assertIsInstance(source.get_empty_list_help('<p>help</p>'), str)
        order = self.create_order()
        order.action_start_test()
        line = order.result_line_ids
        with device_capture(source):
            line.write({'actual_value': 100.0})
        self.assertEqual((line.value_origin, line.value_source_id), ('device', source))
        line.write({'actual_value': 101.0, 'value_origin': 'device'})
        self.assertEqual((line.value_origin, line.value_source_id.id), ('manual', False))


@tagged('post_install', '-at_install')
class TestSettings(PharmaTestCommon):
    """Pharmaceutical ERP settings."""

    def test_scores_checked_when_module_enabled(self):
        """An out-of-range score is refused while its module is enabled."""
        Settings = self.env['res.config.settings']
        with self.assertRaises(ValidationError):
            Settings.new({'module_pharma_vendor_qualification': True,
                          'pharma_vendor_approval_percentage': 0}).set_values()
        with self.assertRaises(ValidationError):
            Settings.new({'module_pharma_sop_training': True,
                          'pharma_training_passing_score': 0}).set_values()

    def test_settings_saved(self):
        """Valid settings are stored on the company."""
        settings = self.env['res.config.settings'].create({'pharma_enforce_storage_class': True})
        settings.set_values()
        self.assertTrue(self.env.company.pharma_enforce_storage_class)

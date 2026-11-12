# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
import logging
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test cases for enabling/disabling POS print templates in settings."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Template = cls.env['pos.print.template']
        cls.Template.search([]).unlink()
        cls.group = cls.env.ref('direct_print_pos.group_pos_print_template')
        cls.report = cls.env.ref(
            'direct_print_pos.action_report_pos_receipt_direct_print')
        cls.ICP = cls.env['ir.config_parameter'].sudo()

    def _set_enable_pos_templates(self, value):
        settings = self.env['res.config.settings'].create({
            'enable_pos_templates': value,
        })
        settings.execute()
        return settings

    def test_enable_sets_config_parameter(self):
        """Enabling the setting stores the config parameter."""
        self._set_enable_pos_templates(True)
        self.assertTrue(
            self.ICP.get_param('direct_print_pos.enable_pos_templates'))
        logger.info('Passed : test_enable_sets_config_parameter')

    def test_enable_adds_current_user_to_group(self):
        """Enabling the setting adds the current user to the template group."""
        user = self.env['res.users'].create({
            'name': 'Template Admin',
            'login': 'template_admin',
            'group_ids': [(6, 0, [self.env.ref('base.group_system').id])],
        })
        settings = self.env['res.config.settings'].with_user(user).create({
            'enable_pos_templates': True,
        })
        settings.execute()
        self.assertIn(self.group, user.group_ids)
        logger.info('Passed : test_enable_adds_current_user_to_group')

    def test_enable_without_report_creates_no_template(self):
        """No template is created when the receipt report is missing."""
        self.report.unlink()
        self._set_enable_pos_templates(True)
        self.assertFalse(self.Template.search([]))
        logger.info('Passed : test_enable_without_report_creates_no_template')

    def test_enable_creates_default_template(self):
        """Enabling the setting creates a default template using the report."""
        self._set_enable_pos_templates(True)
        template = self.Template.search([('is_default', '=', True)])
        self.assertEqual(len(template), 1)
        self.assertEqual(template.name, 'Default POS Receipt')
        self.assertEqual(template.report_id, self.report)
        logger.info('Passed : test_enable_creates_default_template')

    def test_enable_twice_keeps_single_default_template(self):
        """Re-enabling the setting does not create a duplicate default."""
        self._set_enable_pos_templates(True)
        self._set_enable_pos_templates(True)
        self.assertEqual(
            self.Template.search_count([('is_default', '=', True)]), 1)
        logger.info('Passed : test_enable_twice_keeps_single_default_template')

    def test_enable_keeps_existing_default_template(self):
        """An existing default template is kept as is."""
        existing = self.Template.create({
            'name': 'My Receipt',
            'is_default': True,
        })
        self._set_enable_pos_templates(True)
        default = self.Template.search([('is_default', '=', True)])
        self.assertEqual(default, existing)
        logger.info('Passed : test_enable_keeps_existing_default_template')

    def test_disable_clears_parameter(self):
        """Disabling removes the user from the group and clears the param."""
        self._set_enable_pos_templates(True)
        self._set_enable_pos_templates(False)
        self.assertNotIn(self.group, self.env.user.group_ids)
        self.assertFalse(
            self.ICP.get_param('direct_print_pos.enable_pos_templates'))
        logger.info('Passed : test_disable_clears_parameter')

    def test_disable_does_not_create_template(self):
        """Disabling the setting does not create any template."""
        self._set_enable_pos_templates(False)
        self.assertFalse(self.Template.search([]))
        logger.info('Passed : test_disable_does_not_create_template')

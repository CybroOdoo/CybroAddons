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
from odoo.tests.common import TransactionCase


class TestRecyclingSetting(TransactionCase):
    """Unit tests verifying recycling module configuration and feature flag toggles."""

    def test_module_wm_recycling_setting_field_exists(self):
        """ Test res.config.settings contains module_wm_recycling boolean field. """
        settings = self.env['res.config.settings'].create({})
        self.assertIn('module_wm_recycling', settings._fields)
        self.assertEqual(settings._fields['module_wm_recycling'].type, 'boolean')

    def test_module_wm_compliance_setting_field_exists(self):
        """ Test res.config.settings contains module_wm_compliance boolean field. """
        settings = self.env['res.config.settings'].create({})
        self.assertIn('module_wm_compliance', settings._fields)
        self.assertEqual(settings._fields['module_wm_compliance'].type, 'boolean')

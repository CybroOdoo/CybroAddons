# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'sale_quotation_revision')
class TestResConfigSettings(TransactionCase):
    """Tests for is_quotation_revision on res.config.settings."""

    # ------------------------------------------------------------------
    # 1. Field presence & metadata
    # ------------------------------------------------------------------

    def test_field_exists(self):
        """is_quotation_revision must be defined on res.config.settings."""
        self.assertIn('is_quotation_revision', self.env['res.config.settings']._fields)

    def test_field_is_boolean(self):
        """is_quotation_revision must be a Boolean field."""
        field = self.env['res.config.settings']._fields['is_quotation_revision']
        self.assertEqual(field.type, 'boolean')

    def test_field_config_parameter_key(self):
        """config_parameter must point to the correct key."""
        field = self.env['res.config.settings']._fields['is_quotation_revision']
        self.assertEqual(
            field.config_parameter,
            'sale_quotation_revision.is_quotation_revision',
        )

    # ------------------------------------------------------------------
    # 2. Save / load round-trip
    # ------------------------------------------------------------------

    def test_enable_stores_true(self):
        """Saving True must write 'True' to ir.config_parameter."""
        s = self.env['res.config.settings'].create({'is_quotation_revision': True})
        s.execute()
        param = self.env['ir.config_parameter'].sudo().get_param(
            'sale_quotation_revision.is_quotation_revision'
        )
        self.assertEqual(param.lower(), 'true')

    def test_disable_stores_falsy(self):
        """Saving False must result in a falsy ir.config_parameter value.

        Odoo removes the record when a Boolean config_parameter is False,
        so get_param returns the Python bool False rather than a string.
        """
        # Enable first so the param record exists, then disable
        s1 = self.env['res.config.settings'].create({'is_quotation_revision': True})
        s1.execute()
        s2 = self.env['res.config.settings'].create({'is_quotation_revision': False})
        s2.execute()
        param = self.env['ir.config_parameter'].sudo().get_param(
            'sale_quotation_revision.is_quotation_revision'
        )
        if isinstance(param, str):
            self.assertNotEqual(param.lower(), 'true')
        else:
            self.assertFalse(param)

    def test_default_is_false(self):
        """A fresh settings record with no prior param must default to False."""
        self.env['ir.config_parameter'].sudo().search([
            ('key', '=', 'sale_quotation_revision.is_quotation_revision')
        ]).unlink()
        settings = self.env['res.config.settings'].create({})
        self.assertFalse(settings.is_quotation_revision)

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""Test suite for enviro.emission.factor extension in esg_data."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestEnviroEmissionFactorDataSource(TransactionCase):
    """Test cases for source_id field relation on enviro.emission.factor."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        provider_field = cls.env['enviro.data.source']._fields['provider']
        cls._orig_selection = provider_field._selection
        cls._orig_field_selection = provider_field.selection
        if 'test_provider' not in (provider_field._selection or {}):
            new_selection = dict(provider_field._selection or {})
            new_selection['test_provider'] = 'Test Provider'
            provider_field._selection = new_selection
            provider_field.selection = tuple(new_selection.items())

        cls.data_source = cls.env['enviro.data.source'].create({
            'name': 'Emission Factor Source',
            'provider': 'test_provider',
        })
        cls.uom = (
            cls.env.ref('uom.product_uom_unit', raise_if_not_found=False)
            or cls.env['uom.uom'].search([], limit=1)
        )
        cls.factor = cls.env['enviro.emission.factor'].create({
            'name': 'Electricity Factor 2026',
            'uom_id': cls.uom.id,
            'kg_co2e_per_unit': 0.45,
            'source_id': cls.data_source.id,
        })

    @classmethod
    def tearDownClass(cls):
        provider_field = cls.env['enviro.data.source']._fields['provider']
        provider_field._selection = cls._orig_selection
        provider_field.selection = cls._orig_field_selection
        super().tearDownClass()

    def test_emission_factor_source_id_linked(self):
        """Test that source_id is properly stored and linked to enviro.data.source."""
        self.assertEqual(
            self.factor.source_id,
            self.data_source,
            "Emission factor should link to the specified data source.",
        )
        self.assertEqual(self.factor.source_id.name, 'Emission Factor Source')

    def test_emission_factor_copy_source_id_not_duplicated(self):
        """Test that copying an emission factor leaves source_id empty (copy=False)."""
        copied_factor = self.factor.copy()
        self.assertFalse(
            copied_factor.source_id,
            "Copied factor should have source_id unset as copy=False.",
        )

    def test_data_source_unlink_ondelete_set_null(self):
        """Test that unlinking a data source sets source_id to False (ondelete='set null')."""
        factor_with_source = self.env['enviro.emission.factor'].create({
            'name': 'Natural Gas Factor',
            'uom_id': self.uom.id,
            'kg_co2e_per_unit': 2.02,
            'source_id': self.data_source.id,
        })
        self.assertEqual(factor_with_source.source_id, self.data_source)

        # Unlink the data source
        self.data_source.unlink()

        # The factor should still exist, but source_id should be cleared
        factor_with_source.invalidate_recordset(['source_id'])
        self.assertTrue(factor_with_source.exists())
        self.assertFalse(factor_with_source.source_id)

    def test_search_emission_factors_by_source(self):
        """Test searching emission factors by source_id."""
        factor_without_source = self.env['enviro.emission.factor'].create({
            'name': 'Manual Factor',
            'uom_id': self.uom.id,
            'kg_co2e_per_unit': 1.15,
        })
        factors_with_source = self.env['enviro.emission.factor'].search([
            ('source_id', '=', self.data_source.id)
        ])
        self.assertIn(self.factor, factors_with_source)
        self.assertNotIn(factor_without_source, factors_with_source)

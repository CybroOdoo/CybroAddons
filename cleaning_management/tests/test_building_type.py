# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Safa KB (odoo@cybrosys.com)
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
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestBuildingType(TransactionCase):
    """Test cases for building.type model."""

    def setUp(self):
        super().setUp()
        self.BuildingType = self.env['building.type']

    def test_create_building_type(self):
        """Test creating a building type with valid name."""
        building = self.BuildingType.create({'name': 'Apartment'})
        self.assertEqual(building.name, 'Apartment')
        self.assertTrue(building.id)

    def test_building_type_name_required(self):
        """Test that name is required for building type."""
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.BuildingType.create({})

    def test_multiple_building_types(self):
        """Demo data already exists, so compare against a baseline."""
        before = self.BuildingType.search_count([])
        self.BuildingType.create({'name': 'Villa'})
        self.BuildingType.create({'name': 'Office'})
        self.assertEqual(self.BuildingType.search_count([]), before + 2)

    def test_building_type_description(self):
        """Test building type has correct description."""
        self.assertEqual(self.BuildingType._description, "Building Type")
# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger
import psycopg2


class TestWorksheetTag(TransactionCase):
    """Test cases for the worksheet.tag model."""

    def setUp(self):
        super().setUp()
        self.tag_model = self.env['worksheet.tag']

    def test_create_tag(self):
        """Test creating a worksheet tag with valid data."""
        tag = self.tag_model.create({'name': 'Engine Repair', 'color': 2})
        self.assertEqual(tag.name, 'Engine Repair',
                         "Tag name should match the created value.")
        self.assertEqual(tag.color, 2,
                         "Tag color should match the created value.")


    def test_tag_name_required(self):
        """Test that a name is required to create a tag."""
        self.assertTrue(self.tag_model._fields['name'].required)

    @mute_logger('odoo.sql_db')
    def test_tag_name_unique(self):
        """Test the unique constraint on the tag name."""
        self.tag_model.create({'name': 'Bodywork'})
        with self.assertRaises(psycopg2.IntegrityError):
            self.tag_model.create({'name': 'Bodywork'})


    def test_tag_default_color(self):
        """Test that the default color index is 0 when not specified."""
        tag = self.tag_model.create({'name': 'Electrical'})
        self.assertEqual(tag.color, 0,
                         "Default color index should be 0.")


    def test_update_tag(self):
        """Test updating a worksheet tag."""
        tag = self.tag_model.create({'name': 'Tyre Change', 'color': 1})
        tag.write({'name': 'Tyre Rotation', 'color': 3})
        self.assertEqual(tag.name, 'Tyre Rotation',
                         "Tag name should be updated.")
        self.assertEqual(tag.color, 3,
                         "Tag color should be updated.")


    def test_delete_tag(self):
        """Test deleting a worksheet tag."""
        tag = self.tag_model.create({'name': 'Oil Change'})
        tag_id = tag.id
        tag.unlink()
        self.assertFalse(
            self.tag_model.search([('id', '=', tag_id)]),
            "Tag should be deleted and not found.")


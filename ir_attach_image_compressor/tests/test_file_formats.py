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

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestFileFormatSource(TransactionCase):
    """Test cases for the FileFormatSource model (source.file.format)."""

    def setUp(self):
        """Set up test fixtures for FileFormatSource tests."""
        super().setUp()
        self.FileFormat = self.env['source.file.format']
        # Create test file format records
        self.format_png = self.FileFormat.create({
            'name': 'png',
            'mime_type': 'image/png-test',
        })
        self.format_jpg = self.FileFormat.create({
            'name': 'jpg',
            'mime_type': 'image/jpg-test',
        })

    # -------------------------------------------------------------------------
    # Tests for: name_get()
    # -------------------------------------------------------------------------

    def test_name_get_single_record(self):
        """name_get returns 'name (mime_type)' tuple for a single record."""
        result = self.format_png.name_get()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], self.format_png.id)
        self.assertEqual(result[0][1], 'png (image/png-test)')

    def test_name_get_multiple_records(self):
        """name_get returns correct tuples for multiple records."""
        records = self.format_png | self.format_jpg
        result = records.name_get()
        self.assertEqual(len(result), 2)
        result_dict = dict(result)
        self.assertEqual(
            result_dict[self.format_png.id], 'png (image/png-test)')
        self.assertEqual(
            result_dict[self.format_jpg.id], 'jpg (image/jpg-test)')

    def test_name_get_format_structure(self):
        """name_get result is a list of (id, name_string) tuples."""
        result = self.format_jpg.name_get()
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], tuple)
        self.assertEqual(len(result[0]), 2)

    def test_name_get_id_matches(self):
        """name_get returns the correct database id as the first element."""
        result = self.format_png.name_get()
        self.assertEqual(result[0][0], self.format_png.id)

    def test_name_get_contains_mime_type(self):
        """name_get display name contains the mime_type in parentheses."""
        result = self.format_png.name_get()
        display_name = result[0][1]
        self.assertIn('image/png-test', display_name)
        self.assertIn('(', display_name)
        self.assertIn(')', display_name)

    # -------------------------------------------------------------------------
    # Tests for: model constraints and field validations
    # -------------------------------------------------------------------------

    def test_create_file_format_with_required_fields(self):
        """A file format record can be created with all required fields."""
        fmt = self.FileFormat.create({
            'name': 'gif',
            'mime_type': 'image/gif-test',
        })
        self.assertEqual(fmt.name, 'gif')
        self.assertEqual(fmt.mime_type, 'image/gif-test')

    def test_unique_mime_type_constraint(self):
        """Creating two records with the same mime_type raises a constraint error."""
        with mute_logger('odoo.sql_db'):
            with self.assertRaises(Exception):
                with self.env.cr.savepoint():
                    self.FileFormat.create({
                        'name': 'duplicate',
                        'mime_type': 'image/png-test',  # already used by format_png
                    })

    def test_name_field_required(self):
        """Creating a file format without 'name' raises a validation error."""
        with mute_logger('odoo.sql_db'):
            with self.assertRaises(Exception):
                with self.env.cr.savepoint():
                    self.FileFormat.create({
                        'mime_type': 'image/no-name',
                    })

    def test_mime_type_field_required(self):
        """Creating a file format without 'mime_type' raises a validation error."""
        with mute_logger('odoo.sql_db'):
            with self.assertRaises(Exception):
                with self.env.cr.savepoint():
                    self.FileFormat.create({
                        'name': 'no_mime',
                    })

    def test_name_get_empty_recordset(self):
        """name_get on an empty recordset returns an empty list."""
        empty = self.FileFormat.browse([])
        result = empty.name_get()
        self.assertEqual(result, [])

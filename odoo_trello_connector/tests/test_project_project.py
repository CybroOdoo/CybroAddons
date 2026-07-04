# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase


class TestProjectProject(TransactionCase):
    """Test cases for project.project trello_reference field"""

    def setUp(self):
        super().setUp()
        self.project = self.env['project.project'].create({
            'name': 'Test Trello Project',
        })

    def test_01_trello_reference_field_exists(self):
        """Test that trello_reference field exists on project.project"""
        self.assertIn('trello_reference', self.env['project.project']._fields)

    def test_02_create_project_with_trello_reference(self):
        """Test creating a project with a trello_reference value"""
        project = self.env['project.project'].create({
            'name': 'Project With Trello Ref',
            'trello_reference': 'abc123trello',
        })
        self.assertEqual(project.trello_reference, 'abc123trello')

    def test_03_update_trello_reference(self):
        """Test updating trello_reference on an existing project"""
        self.assertFalse(self.project.trello_reference)
        self.project.write({'trello_reference': 'newref456'})
        self.assertEqual(self.project.trello_reference, 'newref456')

    def test_04_trello_reference_default_empty(self):
        """Test that trello_reference defaults to empty"""
        project = self.env['project.project'].create({'name': 'No Ref Project'})
        self.assertFalse(project.trello_reference)

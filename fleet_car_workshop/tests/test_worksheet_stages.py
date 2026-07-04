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


class TestWorksheetStages(TransactionCase):
    """Test cases for the worksheet.stages model."""

    def setUp(self):
        super().setUp()
        self.stage_model = self.env['worksheet.stages']

    def test_create_stage(self):
        """Test creating a worksheet stage with valid data."""
        stage = self.stage_model.create({
            'name': 'In Progress',
            'sequence': 10,
            'description': 'Work is currently in progress.',
            'is_fold': False,
        })
        self.assertEqual(stage.name, 'In Progress',
                         "Stage name should match the created value.")
        self.assertEqual(stage.sequence, 10,
                         "Stage sequence should match the created value.")
        self.assertFalse(stage.is_fold,
                         "Stage should not be folded by default.")


    def test_stage_name_required(self):
        """Test that a name is required to create a worksheet stage."""
        self.assertTrue(self.stage_model._fields['name'].required)


    def test_stage_is_fold(self):
        """Test creating a folded stage (used for Done/Cancelled states)."""
        stage = self.stage_model.create({
            'name': 'Done',
            'sequence': 100,
            'is_fold': True,
        })
        self.assertTrue(stage.is_fold,
                        "Stage is_fold should be True.")


    def test_stage_ordering(self):
        """Test that stages are ordered by sequence."""
        stage_a = self.stage_model.create({'name': 'Alpha', 'sequence': 20})
        stage_b = self.stage_model.create({'name': 'Beta', 'sequence': 5})
        stages = self.stage_model.search([
            ('id', 'in', [stage_a.id, stage_b.id])
        ])
        self.assertEqual(stages[0].id, stage_b.id,
                         "Stages should be ordered by sequence ascending.")


    def test_update_stage(self):
        """Test updating a worksheet stage."""
        stage = self.stage_model.create({'name': 'Review', 'sequence': 50})
        stage.write({'name': 'Final Review', 'sequence': 55, 'is_fold': True})
        self.assertEqual(stage.name, 'Final Review',
                         "Stage name should be updated.")
        self.assertTrue(stage.is_fold,
                        "Stage is_fold should be updated to True.")


    def test_delete_stage(self):
        """Test deleting a worksheet stage that has no linked worksheets."""
        stage = self.stage_model.create({'name': 'Obsolete Stage', 'sequence': 999})
        stage_id = stage.id
        stage.unlink()
        self.assertFalse(
            self.stage_model.search([('id', '=', stage_id)]),
            "Stage should be deleted.")


    def test_default_vehicle_ids_with_context(self):
        """Test that _default_vehicle_ids respects the context."""
        fleet_vehicle = self.env['fleet.vehicle'].create({
            'model_id': self.env['fleet.vehicle.model'].create({
                'name': 'Test Model',
                'brand_id': self.env['fleet.vehicle.model.brand'].create(
                    {'name': 'Test Brand'}).id,
            }).id,
        })
        vehicle_detail = self.env['vehicle.details'].create({
            'vehicle_id': fleet_vehicle.id,
        })
        stage = self.stage_model.with_context(
            default_vehicle_id=vehicle_detail.id
        ).create({'name': 'Contextual Stage', 'sequence': 1})
        self.assertIn(vehicle_detail, stage.vehicle_ids,
                      "Vehicle from context should be in stage's vehicle_ids.")


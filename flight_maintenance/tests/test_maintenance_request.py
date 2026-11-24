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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestMaintenanceRequest(TransactionCase):
    """Unit tests for maintenance.request extensions in flight_maintenance."""

    @classmethod
    def setUpClass(cls):
        """Set up test aircraft, model, equipment, and stages for maintenance requests."""
        super().setUpClass()
        cls.Aircraft = cls.env['flight.aircraft']
        cls.Request = cls.env['maintenance.request']
        cls.Equipment = cls.env['maintenance.equipment']
        cls.Stage = cls.env['maintenance.stage']

        cls.stage_open = cls.Stage.search([('done', '=', False)], limit=1)
        if not cls.stage_open:
            cls.stage_open = cls.Stage.create({
                'name': 'Open Stage (MR Test)',
                'done': False,
                'sequence': 1,
            })
        cls.stage_done = cls.Stage.search([('done', '=', True)], limit=1)
        if not cls.stage_done:
            cls.stage_done = cls.Stage.create({
                'name': 'Done Stage (MR Test)',
                'done': True,
                'sequence': 99,
            })

        aircraft_vals = {'name': 'MR-TEST-AC-01', 'status': 'active'}
        if 'model_id' in cls.Aircraft._fields:
            Model = cls.env.get('flight.aircraft.model')
            if Model is not None:
                model = Model.search([], limit=1)
                if not model and 'name' in Model._fields:
                    Make = cls.env.get('flight.aircraft.make')
                    make = False
                    if Make is not None:
                        make = Make.search([], limit=1)
                        if not make and 'name' in Make._fields:
                            make = Make.create({'name': 'MR Make'})
                    model_vals = {'name': 'MR Model'}
                    if make and 'make_id' in Model._fields:
                        model_vals['make_id'] = make.id
                    model = Model.create(model_vals)
                if model:
                    aircraft_vals['model_id'] = model.id

        cls.aircraft = cls.Aircraft.create(aircraft_vals)
        cls.equipment = cls.aircraft.equipment_id

    def test_01_create_request_with_equipment_links_aircraft(self):
        """Creating a maintenance request specifying equipment_id populates aircraft_id."""
        req = self.Request.create({
            'name': 'Check Landing Gear',
            'equipment_id': self.equipment.id,
            'stage_id': self.stage_open.id,
        })
        self.assertEqual(req.aircraft_id, self.aircraft)

    def test_02_create_request_with_aircraft_links_equipment(self):
        """Creating a maintenance request specifying aircraft_id populates equipment_id."""
        req = self.Request.create({
            'name': 'Check Avionics',
            'aircraft_id': self.aircraft.id,
            'stage_id': self.stage_open.id,
        })
        self.assertEqual(req.equipment_id, self.equipment)

    def test_03_onchange_aircraft_sets_equipment(self):
        """Calling onchange on aircraft_id automatically sets equipment_id."""
        req = self.Request.new({
            'name': 'Onchange Aircraft Test',
            'aircraft_id': self.aircraft.id,
        })
        req._onchange_aircraft_id_set_equipment()
        self.assertEqual(req.equipment_id, self.equipment)

    def test_04_onchange_empty_aircraft_does_not_fail(self):
        """Calling onchange with empty aircraft_id safely leaves equipment_id untouched."""
        req = self.Request.new({
            'name': 'Onchange Empty Test',
            'aircraft_id': False,
        })
        req._onchange_aircraft_id_set_equipment()
        self.assertFalse(req.equipment_id)

    def test_05_action_recompute_aircraft_link(self):
        """action_recompute_aircraft_link recomputes aircraft_id from equipment_id."""
        req = self.Request.create({
            'name': 'Orphan Record Test',
            'equipment_id': self.equipment.id,
            'stage_id': self.stage_open.id,
        })
        req.write({'aircraft_id': False})
        self.assertFalse(req.aircraft_id)
        req.action_recompute_aircraft_link()
        self.assertEqual(req.aircraft_id, self.aircraft)

    def test_06_write_syncs_aircraft_and_equipment(self):
        """Writing aircraft_id or equipment_id bidirectionally synchronizes the opposite field."""
        req = self.Request.create({
            'name': 'Sync Write Test',
            'stage_id': self.stage_open.id,
        })
        # Write aircraft_id alone -> equipment_id must be populated
        req.write({'aircraft_id': self.aircraft.id})
        self.assertEqual(req.equipment_id, self.equipment)

        # Fresh request, write equipment_id alone -> aircraft_id must be populated
        req2 = self.Request.create({
            'name': 'Sync Write Test 2',
            'stage_id': self.stage_open.id,
        })
        req2.write({'equipment_id': self.equipment.id})
        self.assertEqual(req2.aircraft_id, self.aircraft)

    def test_07_unlink_request_recomputes_aircraft_status(self):
        """Deleting the only open grounding request restores the aircraft status to active."""
        req = self.Request.create({
            'name': 'Temporary Grounding Request',
            'aircraft_id': self.aircraft.id,
            'equipment_id': self.equipment.id,
            'stage_id': self.stage_open.id,
            'grounding': True,
        })
        self.assertEqual(self.aircraft.status, 'maintenance')

        req.unlink()
        self.assertEqual(self.aircraft.status, 'active')

    def test_08_compute_aircraft_id_sets_missing_equipment(self):
        """_compute_aircraft_id assigns aircraft.equipment_id if equipment_id is missing."""
        req = self.Request.create({
            'name': 'Missing Eq Test',
            'stage_id': self.stage_open.id,
        })
        req.equipment_id = False
        req.aircraft_id = self.aircraft
        req._compute_aircraft_id()
        self.assertEqual(req.equipment_id, self.aircraft.equipment_id)


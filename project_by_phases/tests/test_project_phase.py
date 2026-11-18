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
#############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestProjectPhase(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_1 = cls.env.company
        cls.user_1 = cls.env.user

        cls.project_1 = cls.env['project.project'].create({
            'name': 'Test Alpha Project',
            'company_id': cls.company_1.id,
        })

        cls.phase_1 = cls.env['project.phase'].create({
            'name': 'Phase 1 - Inception',
            'project_id': cls.project_1.id,
            'responsible_user_id': cls.user_1.id,
            'sequence': 10,
            'company_id': cls.company_1.id,
        })

    def test_01_phase_creation_and_defaults(self):
        """Test phase record creation and field values."""
        self.assertEqual(self.phase_1.name, 'Phase 1 - Inception')
        self.assertEqual(self.phase_1.project_id, self.project_1)
        self.assertEqual(self.phase_1.responsible_user_id, self.user_1)
        self.assertEqual(self.phase_1.sequence, 10)
        self.assertEqual(self.phase_1.company_id, self.company_1)

    def test_02_phase_sequence_ordering(self):
        """Test that phases are ordered by sequence then id."""
        phase_b = cls_phase_b = self.env['project.phase'].create({
            'name': 'Phase 3 - Deployment',
            'project_id': self.project_1.id,
            'responsible_user_id': self.user_1.id,
            'sequence': 30,
        })
        phase_c = self.env['project.phase'].create({
            'name': 'Phase 2 - Development',
            'project_id': self.project_1.id,
            'responsible_user_id': self.user_1.id,
            'sequence': 20,
        })

        phases = self.env['project.phase'].search(
            [('project_id', '=', self.project_1.id)]
        )
        self.assertEqual(
            phases.ids,
            [self.phase_1.id, phase_c.id, phase_b.id],
            "Phases should be ordered by sequence: 10, 20, 30"
        )

    def test_03_task_linking(self):
        """Test assigning a project phase to a task."""
        task = self.env['project.task'].create({
            'name': 'Design Architecture',
            'project_id': self.project_1.id,
            'project_phase_id': self.phase_1.id,
        })
        self.assertEqual(task.project_phase_id, self.phase_1)
        self.assertEqual(task.project_id, self.project_1)

    def test_04_get_project_phases_action(self):
        """Test smart button action on project returning related phases."""
        action = self.project_1.get_project_phases()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'project.phase')
        self.assertEqual(
            action.get('domain'), [('project_id', '=', self.project_1.id)]
        )
        self.assertEqual(
            action.get('context'), {'default_project_id': self.project_1.id}
        )

    def test_05_get_project_tasks_action(self):
        """Test smart button action on phase returning related tasks."""
        action = self.phase_1.get_project_tasks()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'project.task')
        self.assertEqual(
            action.get('domain'), [('project_phase_id', '=', self.phase_1.id)]
        )
        self.assertEqual(
            action.get('context'),
            {
                'default_project_phase_id': self.phase_1.id,
                'default_project_id': self.project_1.id,
            }
        )

    def test_06_ensure_one_guards(self):
        """Verify get_project_phases and get_project_tasks ensure_one()."""
        two_projects = self.project_1 | self.env['project.project'].create({
            'name': 'Project Beta'
        })
        with self.assertRaises(ValueError):
            two_projects.get_project_phases()

        two_phases = self.phase_1 | self.env['project.phase'].create({
            'name': 'Phase Other',
            'responsible_user_id': self.user_1.id,
        })
        with self.assertRaises(ValueError):
            two_phases.get_project_tasks()

    def test_07_multi_company_validation(self):
        """Test company_id validation between project and phase."""
        company_2 = self.env['res.company'].create({'name': 'Second Company'})
        project_comp_2 = self.env['project.project'].create({
            'name': 'Company 2 Project',
            'company_id': company_2.id,
        })

        # Phase for company_1 cannot link project belonging to company_2
        with self.assertRaises(Exception):
            self.env['project.phase'].create({
                'name': 'Inconsistent Company Phase',
                'project_id': project_comp_2.id,
                'company_id': self.company_1.id,
                'responsible_user_id': self.user_1.id,
            })

    def test_08_company_agnostic_project_and_task(self):
        """Test phase selection when project has no company set."""
        project_no_company = self.env['project.project'].create({
            'name': 'Global Project',
            'company_id': False,
        })
        phase = self.env['project.phase'].create({
            'name': 'Global Phase 1',
            'project_id': project_no_company.id,
            'responsible_user_id': self.user_1.id,
        })
        task = self.env['project.task'].create({
            'name': 'Global Task',
            'project_id': project_no_company.id,
            'project_phase_id': phase.id,
        })
        self.assertEqual(task.project_phase_id, phase)
        # Verify name_search works with domain [('project_id', '=', id)]
        search_results = self.env['project.phase'].name_search(
            '', domain=[('project_id', '=', project_no_company.id)]
        )
        self.assertIn(phase.id, [res[0] for res in search_results])

    def test_09_onchange_project_id(self):
        """Test onchange of project_id updates company_id."""
        phase = self.env['project.phase'].new({'name': 'Draft Phase'})
        phase.project_id = self.project_1
        phase._onchange_project_id()
        self.assertEqual(phase.company_id, self.project_1.company_id)

    def test_10_multi_record_compute_company(self):
        """Test _compute_company_id across multiple phase records."""
        phase_x = self.env['project.phase'].create({
            'name': 'Batch Phase 1',
            'project_id': self.project_1.id,
            'responsible_user_id': self.user_1.id,
        })
        phase_y = self.env['project.phase'].create({
            'name': 'Batch Phase 2',
            'project_id': self.project_1.id,
            'responsible_user_id': self.user_1.id,
        })
        records = phase_x | phase_y
        records._compute_company_id()
        self.assertEqual(phase_x.company_id, self.project_1.company_id)
        self.assertEqual(phase_y.company_id, self.project_1.company_id)


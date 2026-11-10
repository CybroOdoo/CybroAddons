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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Automated unit tests for Project Task Risk Management Odoo module."""
import base64

from psycopg2 import IntegrityError

from .. import _post_init_hook
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestProjectTaskRiskManagement(TransactionCase):
    """Test suite covering models, methods, wizards, constraints, and multi-recordset
    operations for project_task_risk_management_odoo.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test master data and isolate testing fixtures."""
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Test partner
        cls.test_partner = cls.env['res.partner'].create({
            'name': 'Risk Test Partner',
            'email': 'risk_test@example.com',
        })

        # Test user
        cls.test_user = cls.env['res.users'].create({
            'name': 'Risk Test Manager',
            'login': 'risk_manager_test',
            'email': 'risk_manager@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id,
                                  cls.env.ref('project.group_project_manager').id])],
        })

        # Test project
        cls.project = cls.env['project.project'].create({
            'name': 'Risk Management Test Project',
            'user_id': cls.test_user.id,
            'partner_id': cls.test_partner.id,
        })

        # Test task
        cls.task = cls.env['project.task'].create({
            'name': 'Risk Management Test Task',
            'project_id': cls.project.id,
            'user_ids': [(4, cls.test_user.id)],
        })

        # Test master data
        cls.category = cls.env['risk.category'].create({
            'name': 'Operational Risk',
            'code': 'OP-01',
        })
        cls.risk_type = cls.env['risk.type'].create({
            'name': 'Technical Risk',
            'code': 'TECH-01',
        })
        cls.response = cls.env['risk.response'].create({
            'name': 'Mitigate',
            'code': 'MIT-01',
        })
        cls.tag = cls.env['risk.tag'].create({
            'name': 'High Priority Tag',
        })

        # Test central risk repository record
        cls.risk = cls.env['risks.project'].create({
            'risk_name': 'Server Infrastructure Failure',
            'code': 'SRV-RISK-01',
            'risk_quantification': 'high',
            'category_id': cls.category.id,
            'risk_type_id': cls.risk_type.id,
            'risk_response_id': cls.response.id,
            'tag_ids': [(4, cls.tag.id)],
            'note': 'Risk of potential downtime due to hardware issues.',
        })

    def test_01_risk_master_data_models(self):
        """Test master data models: risk.category, risk.type, risk.response, risk.tag."""
        category = self.env['risk.category'].create({
            'name': 'Financial Risk',
            'code': 'FIN-01',
        })
        self.assertEqual(category.name, 'Financial Risk')
        self.assertEqual(category.code, 'FIN-01')

        risk_type = self.env['risk.type'].create({
            'name': 'Environmental Risk',
            'code': 'ENV-01',
        })
        self.assertEqual(risk_type.name, 'Environmental Risk')
        self.assertEqual(risk_type.code, 'ENV-01')

        response = self.env['risk.response'].create({
            'name': 'Accept',
            'code': 'ACC-01',
        })
        self.assertEqual(response.name, 'Accept')
        self.assertEqual(response.code, 'ACC-01')

        # Test risk.tag default color generation and unique constraint
        tag_1 = self.env['risk.tag'].create({'name': 'Security Audit'})
        self.assertGreaterEqual(tag_1.color, 1)
        self.assertLessEqual(tag_1.color, 11)

        # Direct test of _get_default_color
        color = tag_1._get_default_color()
        self.assertTrue(1 <= color <= 11)

        # Unique name constraint on risk.tag
        with mute_logger('odoo.sql_db'), self.assertRaises((ValidationError, IntegrityError)):
            self.env['risk.tag'].create({'name': 'Security Audit'})

    def test_02_risks_project_operations(self):
        """Test risks.project model fields and multi-recordset operations."""
        risk_1 = self.risk
        self.assertEqual(risk_1.risk_name, 'Server Infrastructure Failure')
        self.assertEqual(risk_1.code, 'SRV-RISK-01')
        self.assertEqual(risk_1.risk_quantification, 'high')
        self.assertEqual(risk_1.category_id, self.category)
        self.assertEqual(risk_1.risk_type_id, self.risk_type)
        self.assertEqual(risk_1.risk_response_id, self.response)
        self.assertIn(self.tag, risk_1.tag_ids)

        risk_2 = self.env['risks.project'].create({
            'risk_name': 'Vendor Delay',
            'code': 'VND-01',
            'risk_quantification': 'medium',
        })
        self.assertEqual(risk_2.risk_quantification, 'medium')

        # Multi-recordset batch update
        combined = risk_1 | risk_2
        combined.write({'note': 'Batch updated note for testing'})
        self.assertEqual(risk_1.note, 'Batch updated note for testing')
        self.assertEqual(risk_2.note, 'Batch updated note for testing')

    def test_03_project_risk_incident_line_and_onchange(self):
        """Test project.risk.incident.line creation, relations, and onchange behavior."""
        line = self.env['project.risk.incident.line'].new({
            'incident_order_id': self.project.id,
            'risk_id': self.risk.id,
            'probability': 65.5,
        })
        # Trigger onchange
        line._onchange_risk_id()
        self.assertEqual(line.category_id.id, self.category.id)
        self.assertEqual(line.risk_response_id.id, self.response.id)
        self.assertEqual(line.risk_type_id.id, self.risk_type.id)
        self.assertEqual(line.tag_ids.ids, [self.tag.id])

        # Test onchange when risk_id is False
        line.risk_id = False
        line._onchange_risk_id()

        # Save record in database
        saved_line = self.env['project.risk.incident.line'].create({
            'incident_order_id': self.project.id,
            'risk_id': self.risk.id,
            'des': 'Detailed project risk description',
            'category_id': self.category.id,
            'risk_response_id': self.response.id,
            'risk_type_id': self.risk_type.id,
            'tag_ids': [(6, 0, [self.tag.id])],
            'probability': 45.0,
        })
        self.assertIn(saved_line, self.project.risk_incident_line_ids)
        self.assertEqual(saved_line.probability, 45.0)

    def test_04_task_risk_incident_line_and_onchange(self):
        """Test task.risk.incident.line creation, relations, and onchange behavior."""
        task_line = self.env['task.risk.incident.line'].new({
            'task_incident_order_id': self.task.id,
            'risk_id': self.risk.id,
            'probability': 80.0,
        })
        # Trigger onchange
        task_line._onchange_risk_id()
        self.assertEqual(task_line.category_id.id, self.category.id)
        self.assertEqual(task_line.risk_response_id.id, self.response.id)
        self.assertEqual(task_line.risk_type_id.id, self.risk_type.id)
        self.assertEqual(task_line.tag_ids.ids, [self.tag.id])

        # Test onchange with False risk_id
        task_line.risk_id = False
        task_line._onchange_risk_id()

        # Save record in database
        saved_task_line = self.env['task.risk.incident.line'].create({
            'task_incident_order_id': self.task.id,
            'risk_id': self.risk.id,
            'des': 'Detailed task risk description',
            'category_id': self.category.id,
            'risk_response_id': self.response.id,
            'risk_type_id': self.risk_type.id,
            'tag_ids': [(6, 0, [self.tag.id])],
            'probability': 55.0,
        })
        self.assertIn(saved_task_line, self.task.task_risk_incident_line_ids)
        self.assertEqual(saved_task_line.des, 'Detailed task risk description')

    def test_05_create_incident_wizard_actions(self):
        """Test action returning methods from project and task models."""
        proj_action = self.project.create_incident_wiz()
        self.assertEqual(proj_action.get('type'), 'ir.actions.act_window')
        self.assertEqual(proj_action.get('res_model'), 'risk.incident.simplified')
        self.assertEqual(proj_action.get('view_mode'), 'form')
        self.assertEqual(proj_action.get('target'), 'new')
        self.assertEqual(proj_action.get('context', {}).get('default_project_id'), self.project.id)
        self.assertEqual(proj_action.get('context', {}).get('default_user_id'), self.test_user.id)

        task_action = self.task.task_create_incident_wiz()
        self.assertEqual(task_action.get('type'), 'ir.actions.act_window')
        self.assertEqual(task_action.get('res_model'), 'risk.incident.simplified')
        self.assertEqual(task_action.get('view_mode'), 'form')
        self.assertEqual(task_action.get('target'), 'new')
        self.assertEqual(task_action.get('context', {}).get('default_project_id'), self.project.id)
        self.assertEqual(task_action.get('context', {}).get('default_user_id'), self.test_user.id)

    def test_06_risk_incident_simplified_wizard_creation(self):
        """Test risk.incident.simplified wizard execution and incident creation."""
        dummy_image = base64.b64encode(b'FakeImageBytesData').decode('utf-8')
        wizard = self.env['risk.incident.simplified'].create({
            'risk_incident': 'Database Memory Leak',
            'note': 'Incident logged during stress testing.',
            'project_id': self.project.id,
            'user_id': self.test_user.id,
            'image': dummy_image,
        })
        self.assertEqual(wizard.risk_incident, 'Database Memory Leak')

        # Execute wizard action
        wizard.create_incident()

        # Check created incident
        incident = self.env['risk.incident'].search([
            ('risk_incident', '=', 'Database Memory Leak'),
            ('project_id', '=', self.project.id),
        ], limit=1)
        self.assertTrue(incident)
        self.assertEqual(incident.user_id, self.test_user)
        self.assertEqual(incident.note, 'Incident logged during stress testing.')
        self.assertTrue(incident.incident_image)
        self.assertEqual(bytes(incident.incident_image), b'FakeImageBytesData')
        self.assertEqual(incident.state, 'new')

    def test_07_risk_incident_model_and_lifecycle(self):
        """Test risk.incident state transitions, multi-recordset, and group_expand."""
        incident_1 = self.env['risk.incident'].create({
            'risk_incident': 'Incident Alpha',
            'project_id': self.project.id,
            'user_id': self.test_user.id,
            'partner_id': self.test_partner.id,
            'state': 'new',
        })
        incident_2 = self.env['risk.incident'].create({
            'risk_incident': 'Incident Beta',
            'project_id': self.project.id,
            'user_id': self.test_user.id,
            'state': 'to_do',
        })

        # Test _group_expand_states method
        expanded_states = incident_1._group_expand_states('new', [])
        expected_states = ['new', 'to_do', 'advanced', 'progress', 'done', 'cancel']
        self.assertEqual(expanded_states, expected_states)

        # Test state progression
        for next_state in ['advanced', 'progress', 'done', 'cancel']:
            incident_1.write({'state': next_state})
            self.assertEqual(incident_1.state, next_state)

        # Multi-recordset batch operations
        combined = incident_1 | incident_2
        combined.write({'deadline': '2026-12-31'})
        self.assertEqual(str(incident_1.deadline), '2026-12-31')
        self.assertEqual(str(incident_2.deadline), '2026-12-31')

    def test_08_post_init_hook_execution(self):
        """Test that _post_init_hook executes cleanly without errors."""
        _post_init_hook(self.env)
        stage_group = self.env.ref('project.group_project_stages', raise_if_not_found=False)
        if stage_group:
            self.assertIn(self.test_user, stage_group.user_ids)
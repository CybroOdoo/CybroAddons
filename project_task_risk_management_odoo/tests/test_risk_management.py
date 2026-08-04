# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.addons.project_task_risk_management_odoo.__init__ import _post_init_hook


class TestProjectTaskRiskManagement(TransactionCase):
    """ Test suite for Project Task Risk Management Odoo """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create standard testing project and task
        cls.project = cls.env['project.project'].create({
            'name': 'Test Risk Management Project',
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Test Risk Management Task',
            'project_id': cls.project.id,
        })

        # Create Risk metadata
        cls.category = cls.env['risk.category'].create({
            'name': 'Test Category',
            'code': 'TCAT',
        })
        cls.risk_type = cls.env['risk.type'].create({
            'name': 'Test Type',
            'code': 'TTYPE',
        })
        cls.risk_response = cls.env['risk.response'].create({
            'name': 'Test Response',
            'code': 'TRESP',
        })
        cls.tag = cls.env['risk.tag'].create({
            'name': 'Test Tag Risk Unique',
        })

        # Create a Project Risk
        cls.risk = cls.env['risks.project'].create({
            'risk_name': 'Test Project Risk',
            'code': 'RISK-01',
            'risk_quantification': 'high',
            'category_id': cls.category.id,
            'risk_type_id': cls.risk_type.id,
            'risk_response_id': cls.risk_response.id,
            'tag_ids': [fields.Command.link(cls.tag.id)],
            'note': 'Test Internal Notes',
        })

    def test_01_metadata_creation(self):
        """ Test risk metadata and template creation """
        self.assertEqual(self.category.name, 'Test Category')
        self.assertEqual(self.risk_type.name, 'Test Type')
        self.assertEqual(self.risk_response.name, 'Test Response')
        self.assertEqual(self.tag.name, 'Test Tag Risk Unique')
        self.assertTrue(self.tag.color > 0)

        self.assertEqual(self.risk.risk_name, 'Test Project Risk')
        self.assertEqual(self.risk.risk_quantification, 'high')
        self.assertEqual(self.risk.category_id, self.category)
        self.assertEqual(self.risk.risk_type_id, self.risk_type)
        self.assertEqual(self.risk.risk_response_id, self.risk_response)
        self.assertIn(self.tag, self.risk.tag_ids)

    def test_02_project_risk_incident_line(self):
        """ Test project risk incident line behavior, onchange and creation """
        # Test onchange method
        line = self.env['project.risk.incident.line'].new({
            'incident_order_id': self.project.id,
            'risk_id': self.risk.id,
        })
        line._onchange_risk_id()
        self.assertEqual(line.category_id, self.category)
        self.assertEqual(line.risk_response_id, self.risk_response)
        self.assertEqual(line.risk_type_id, self.risk_type)
        self.assertEqual(line.tag_ids, self.tag)

        # Test database creation
        line_db = self.env['project.risk.incident.line'].create({
            'incident_order_id': self.project.id,
            'risk_id': self.risk.id,
            'category_id': self.category.id,
            'risk_response_id': self.risk_response.id,
            'risk_type_id': self.risk_type.id,
            'tag_ids': [fields.Command.link(self.tag.id)],
            'probability': 75.0,
            'des': 'Project Risk Description',
        })
        self.assertEqual(line_db.probability, 75.0)
        self.assertEqual(line_db.des, 'Project Risk Description')
        self.assertIn(line_db, self.project.risk_incident_line_ids)

    def test_03_project_wizard_action(self):
        """ Test wizard retrieval action from project """
        action = self.project.create_incident_wiz()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'risk.incident.simplified')
        self.assertEqual(action.get('target'), 'new')
        self.assertEqual(action.get('context', {}).get('default_project_id'), self.project.id)

    def test_04_task_risk_incident_line(self):
        """ Test task risk incident line behavior, onchange and creation """
        # Test onchange method
        line = self.env['task.risk.incident.line'].new({
            'task_incident_order_id': self.task.id,
            'risk_id': self.risk.id,
        })
        line._onchange_risk_id()
        self.assertEqual(line.category_id, self.category)
        self.assertEqual(line.risk_response_id, self.risk_response)
        self.assertEqual(line.risk_type_id, self.risk_type)
        self.assertEqual(line.tag_ids, self.tag)

        # Test database creation
        line_db = self.env['task.risk.incident.line'].create({
            'task_incident_order_id': self.task.id,
            'risk_id': self.risk.id,
            'category_id': self.category.id,
            'risk_response_id': self.risk_response.id,
            'risk_type_id': self.risk_type.id,
            'tag_ids': [fields.Command.link(self.tag.id)],
            'probability': 40.0,
            'des': 'Task Risk Description',
        })
        self.assertEqual(line_db.probability, 40.0)
        self.assertEqual(line_db.des, 'Task Risk Description')
        self.assertIn(line_db, self.task.task_risk_incident_line_ids)

    def test_05_task_wizard_action(self):
        """ Test wizard retrieval action from task """
        action = self.task.task_create_incident_wiz()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'risk.incident.simplified')
        self.assertEqual(action.get('target'), 'new')
        self.assertEqual(action.get('context', {}).get('default_project_id'), self.project.id)

    def test_06_wizard_incident_creation(self):
        """ Test creating a risk incident through the simplified wizard """
        # Check start count of incidents
        incident_count_before = self.env['risk.incident'].search_count([])

        # Create wizard and execute
        wiz = self.env['risk.incident.simplified'].create({
            'risk_incident': 'Test Wizard Incident',
            'note': 'Test Description from Wizard',
            'user_id': self.env.user.id,
            'project_id': self.project.id,
        })
        wiz.create_incident()

        # Check that incident is created
        incident_count_after = self.env['risk.incident'].search_count([])
        self.assertEqual(incident_count_after, incident_count_before + 1)

        new_incident = self.env['risk.incident'].search([], order='id desc', limit=1)
        self.assertEqual(new_incident.risk_incident, 'Test Wizard Incident')
        self.assertEqual(new_incident.note, 'Test Description from Wizard')
        self.assertEqual(new_incident.project_id, self.project)
        self.assertEqual(new_incident.user_id, self.env.user)

    def test_07_group_expand_states(self):
        """ Test state expansion logic for kanban view grouping """
        states = self.env['risk.incident']._group_expand_states(None, None)
        expected_states = ['new', 'to_do', 'advanced', 'progress', 'done', 'cancel']
        self.assertEqual(states, expected_states)

    def test_08_post_init_hook(self):
        """ Test the post installation hook """
        # Run post_init_hook
        _post_init_hook(self.env)
        project_stage_group = self.env.ref('project.group_project_stages')
        non_share_users = self.env['res.users'].search([('share', '=', False)])
        # Every non-share user should be in the project stages group
        for user in non_share_users:
            self.assertIn(user, project_stage_group.user_ids)

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
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import HttpCase, new_test_user
from odoo.addons.project_website_kanban_view.controllers.project_website_kanban_view import (
    ProjectCustomerPortal,
)


@tagged('post_install', '-at_install')
class TestProjectWebsiteKanbanView(HttpCase):
    """Tests for the Website Project Kanban View module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Ensure the default config parameter is present
        cls.env['ir.config_parameter'].sudo().set_int(
            'project_website_kanban_view.task_per_pager', 80
        )

        cls.user_project = new_test_user(
            cls.env,
            login='project_test_user',
            groups='base.group_everyone,base.group_user,project.group_project_user',
            name='Project Test User',
        )

        cls.project = cls.env['project.project'].create({
            'name': 'Test Website Kanban Project',
            'privacy_visibility': 'employees',
        })

        cls.task_1 = cls.env['project.task'].create({
            'name': 'Website Kanban Task 1',
            'project_id': cls.project.id,
            'user_ids': [(6, 0, [cls.user_project.id])],
        })

        cls.task_2 = cls.env['project.task'].create({
            'name': 'Website Kanban Task 2',
            'project_id': cls.project.id,
            'user_ids': [(6, 0, [cls.user_project.id])],
        })

    def test_task_per_pager_config_parameter_exists(self):
        """The ir.config_parameter record is created with value 80 by default."""
        value = self.env['ir.config_parameter'].sudo().get_int(
            'project_website_kanban_view.task_per_pager'
        )
        self.assertTrue(value, "Config parameter must be set.")
        self.assertEqual(value, 80, "Default tasks per page should be 80.")

    def test_res_config_settings_field_exists(self):
        """task_per_pager field is present on res.config.settings."""
        config = self.env['res.config.settings'].create({})
        self.assertTrue(
            hasattr(config, 'task_per_pager'),
            "res.config.settings must have the task_per_pager field."
        )

    def test_res_config_settings_field_write_read(self):
        """task_per_pager field can be written and read back via config params."""
        config = self.env['res.config.settings'].create(
            {'task_per_pager': 20}
        )
        config.execute()
        value = self.env['ir.config_parameter'].sudo().get_int(
            'project_website_kanban_view.task_per_pager'
        )
        self.assertEqual(value, 20,
                         "Written value should be persisted to config param.")

    def test_res_config_settings_invalid_value(self):
        """Setting task_per_pager <= 0 raises a ValidationError."""
        with self.assertRaises(ValidationError):
            self.env['res.config.settings'].create({'task_per_pager': 0})
        with self.assertRaises(ValidationError):
            self.env['res.config.settings'].create({'task_per_pager': -5})

    def test_portal_my_projects_kanban(self):
        """Test /my/projects with viewtype=kanban renders kanban cards."""
        self.authenticate(self.user_project.login, self.user_project.login)
        response = self.url_open('/my/projects?viewtype=kanban')
        self.assertEqual(response.status_code, 200)
        self.assertIn('section-Kanban-view', response.text)
        self.assertIn('project-container', response.text)
        self.assertIn('Test Website Kanban Project', response.text)
        self.assertNotIn('kanban-task-container', response.text)

    def test_portal_my_projects_list(self):
        """Test /my/projects with viewtype=list renders table view."""
        self.authenticate(self.user_project.login, self.user_project.login)
        response = self.url_open('/my/projects?viewtype=list')
        self.assertEqual(response.status_code, 200)
        self.assertIn('o_portal_my_doc_table', response.text)

    def test_portal_my_tasks_kanban(self):
        """Test /my/tasks with viewtype=kanban renders task kanban view."""
        self.authenticate(self.user_project.login, self.user_project.login)
        response = self.url_open('/my/tasks?viewtype=kanban')
        self.assertEqual(response.status_code, 200)
        self.assertIn('section-Kanban-view', response.text)
        self.assertIn('kanban-task-container', response.text)
        self.assertIn('task-box', response.text)
        self.assertIn('Website Kanban Task 1', response.text)

    def test_portal_my_project_detail_kanban(self):
        """Test /my/projects/<id> with viewtype=kanban renders tasks kanban."""
        self.authenticate(self.user_project.login, self.user_project.login)
        response = self.url_open(f'/my/projects/{self.project.id}?viewtype=kanban')
        self.assertEqual(response.status_code, 200)
        self.assertIn('section-Kanban-view', response.text)
        self.assertIn('kanban-task-container', response.text)
        self.assertIn('Website Kanban Task 1', response.text)

    def test_portal_tasks_per_page_setting(self):
        """Test that configuring task_per_pager controls tasks per page and does not leak."""
        self.env['ir.config_parameter'].sudo().set_int(
            'project_website_kanban_view.task_per_pager', 1
        )
        self.authenticate(self.user_project.login, self.user_project.login)
        response = self.url_open('/my/tasks?viewtype=kanban')
        self.assertEqual(response.status_code, 200)
        self.assertIn('section-Kanban-view', response.text)

        # Verify controller instance does not retain _items_per_page on its __dict__
        controller = ProjectCustomerPortal()
        self.assertNotIn(
            '_items_per_page', controller.__dict__,
            "Controller instance must not mutate _items_per_page in its __dict__",
        )
        # Reset back to default
        self.env['ir.config_parameter'].sudo().set_int(
            'project_website_kanban_view.task_per_pager', 80
        )

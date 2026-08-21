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
from odoo.exceptions import AccessError


class TestInformationTemplates(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['info.hub.template.category'].create({
            'name': 'Test Operations Category',
            'sequence': 5,
            'icon': '⚙️',
        })
        cls.template = cls.env['info.hub.article'].create({
            'name': 'Test Guidelines SOP',
            'icon': '📋',
            'body': '<h3>Guidelines</h3><p>Follow standard procedures.</p>',
            'category': 'workspace',
            'is_template': True,
            'template_category_id': cls.category.id,
            'template_description': 'Guidelines SOP for operation tests.',
            'template_sequence': 15,
        })
        # Create a standard user for security validations
        cls.partner_demo = cls.env['res.partner'].create({
            'name': 'Demo User Partner',
            'email': 'demo@example.com',
        })
        cls.user_demo = cls.env['res.users'].create({
            'name': 'Demo User',
            'login': 'demo_user',
            'partner_id': cls.partner_demo.id,
            'group_ids': [(6, 0, [cls.env.ref('info_hub.group_info_user').id])],
        })

    def test_get_available_templates(self):
        """Verify that get_available_templates returns defined templates with details."""
        templates = self.env['info.hub.article'].get_available_templates()
        matching = [t for t in templates if t['id'] == self.template.id]
        self.assertEqual(len(matching), 1, "The seeded template should be returned.")
        self.assertEqual(matching[0]['name'], 'Test Guidelines SOP')
        self.assertEqual(matching[0]['icon'], '📋')
        self.assertEqual(matching[0]['template_category_id'][0], self.category.id)
        self.assertEqual(matching[0]['template_category_id'][1], 'Test Operations Category')
        self.assertEqual(matching[0]['template_sequence'], 15)

    def test_add_article_to_templates(self):
        """Verify that add_article_to_templates marks the article as template."""
        article = self.env['info.hub.article'].create({
            'name': 'Article promoted to template',
            'category': 'workspace',
            'is_template': False,
        })
        self.env['info.hub.article'].add_article_to_templates(article.id, self.category.id)
        self.assertTrue(article.is_template)
        self.assertEqual(article.template_category_id, self.category)

    def test_add_to_template_wizard_uses_existing_template_logic(self):
        """Verify that the template wizard successfully promotes an article using action_create_template."""
        article = self.env['info.hub.article'].create({
            'name': 'Wizard promoted template',
            'category': 'workspace',
            'is_template': False,
        })
        wizard = self.env['info.hub.add.to.template.wizard'].create({
            'article_id': article.id,
            'template_category_id': self.category.id,
        })
        action = wizard.action_create_template()
        self.assertEqual(action, {'type': 'ir.actions.act_window_close'})
        self.assertTrue(article.is_template)
        self.assertEqual(article.template_category_id, self.category)

    def test_get_template_preview(self):
        """Verify that get_template_preview returns correctly formatted preview data."""
        preview = self.env['info.hub.article'].get_template_preview(self.template.id)
        self.assertEqual(preview.get('name'), 'Test Guidelines SOP')
        self.assertEqual(preview.get('icon'), '📋')
        self.assertEqual(preview.get('body'), '<h3>Guidelines</h3><p>Follow standard procedures.</p>')
        self.assertEqual(preview.get('template_description'), 'Guidelines SOP for operation tests.')
        self.assertEqual(preview.get('template_category'), 'Test Operations Category')

    def test_create_article_from_template(self):
        """Verify that duplicating a template creates a new regular article in the target category."""
        new_article_id = self.env['info.hub.article'].create_article_from_template(
            self.template.id, 'workspace'
        )
        new_article = self.env['info.hub.article'].browse(new_article_id)
        self.assertTrue(new_article.exists())
        self.assertEqual(new_article.name, 'Test Guidelines SOP')
        self.assertEqual(new_article.icon, '📋')
        self.assertEqual(new_article.body, '<h3>Guidelines</h3><p>Follow standard procedures.</p>')
        self.assertEqual(new_article.category, 'workspace')
        self.assertFalse(new_article.is_template, "The cloned article must not be marked as a template.")
        self.assertEqual(new_article.author_id.id, self.env.uid)

    def test_security_workspace_permissions(self):
        """Verify that security permissions prevent unauthorized access to templates in private category."""
        # Create a template inside private category
        private_template = self.env['info.hub.article'].create({
            'name': 'Private Secret Template',
            'category': 'private',
            'author_id': self.env.ref('base.user_admin').id,
            'is_template': True,
        })

        # When queried as Admin, the template is visible
        admin_templates = self.env['info.hub.article'].get_available_templates()
        self.assertTrue(any(t['id'] == private_template.id for t in admin_templates))

        # When queried as standard user (demo), the template should not be returned
        user_article_model = self.env['info.hub.article'].with_user(self.user_demo)
        user_templates = user_article_model.get_available_templates()
        self.assertFalse(any(t['id'] == private_template.id for t in user_templates))

        # Attempting to fetch preview or clone the private template as standard user raises an error
        with self.assertRaises(AccessError):
            user_article_model.get_template_preview(private_template.id)

        with self.assertRaises(AccessError):
            user_article_model.create_article_from_template(private_template.id, 'workspace')

    def test_formview_action_redirection(self):
        """Verify that standard active articles redirect form view actions to the client dashboard,
        while template or archived articles do not.
        """
        # 1. Normal active article: should redirect to client action
        normal_article = self.env['info.hub.article'].create({
            'name': 'Normal active article',
            'category': 'workspace',
            'is_template': False,
            'active': True,
        })
        action = normal_article.get_formview_action()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'info_hub.InfoApp')
        self.assertEqual(action.get('res_id'), normal_article.id)
        self.assertEqual(action.get('params', {}).get('article_id'), normal_article.id)

        # 2. Template article: should use standard form view
        action_tpl = self.template.get_formview_action()
        self.assertEqual(action_tpl.get('type'), 'ir.actions.act_window')
        self.assertEqual(action_tpl.get('res_model'), 'info.hub.article')
        self.assertEqual(action_tpl.get('res_id'), self.template.id)

        # 3. Archived article: should use standard form view
        archived_article = self.env['info.hub.article'].create({
            'name': 'Archived article',
            'category': 'workspace',
            'is_template': False,
            'active': False,
        })
        action_arch = archived_article.get_formview_action()
        self.assertEqual(action_arch.get('type'), 'ir.actions.act_window')
        self.assertEqual(action_arch.get('res_model'), 'info.hub.article')
        self.assertEqual(action_arch.get('res_id'), archived_article.id)

    def test_favorite_field(self):
        """Verify that is_favorite works correctly."""
        article = self.env['info.hub.article'].create({
            'name': 'Favorite test',
            'category': 'workspace',
            'is_template': False,
            'active': True,
        })
        self.assertFalse(article.is_favorite)
        article.write({'is_favorite': True})
        self.assertTrue(article.is_favorite)

    def test_create_default_item_stages(self):
        """Verify that default stages are created as 'New', 'Ongoing', 'Done' with 'Done' folded."""
        article = self.env['info.hub.article'].create({
            'name': 'Kanban Parent Article',
            'category': 'workspace',
            'is_template': False,
            'active': True,
        })
        self.env['info.hub.article'].create_default_item_stages(article.id)
        stages = self.env['info.hub.article.stage'].search([('parent_id', '=', article.id)], order='sequence asc')
        self.assertEqual(len(stages), 3)
        self.assertEqual(stages[0].name, 'New')
        self.assertFalse(stages[0].fold)
        self.assertEqual(stages[1].name, 'Ongoing')
        self.assertFalse(stages[1].fold)
        self.assertEqual(stages[2].name, 'Done')
        self.assertTrue(stages[2].fold)

    def test_read_group_stage_ids(self):
        """Verify that _read_group_stage_ids expands and returns the correct parent stages."""
        article = self.env['info.hub.article'].create({
            'name': 'Kanban Parent Article',
            'category': 'workspace',
            'is_template': False,
            'active': True,
        })
        self.env['info.hub.article'].create_default_item_stages(article.id)
        # Call group expand
        domain = [('parent_id', '=', article.id), ('is_article_item', '=', True)]
        expanded_stages = self.env['info.hub.article']._read_group_stage_ids(None, domain)
        self.assertEqual(len(expanded_stages), 3)
        self.assertEqual(expanded_stages[2].name, 'Done')

    def test_archive_and_restore_hierarchy(self):
        """Verify that archiving a parent article archives all descendants, and restoring it unarchives all descendants."""
        parent = self.env['info.hub.article'].create({
            'name': 'Parent Article',
            'category': 'workspace',
            'active': True,
        })
        child_item = self.env['info.hub.article'].create({
            'name': 'Child Item',
            'parent_id': parent.id,
            'is_article_item': True,
            'active': True,
        })
        # Archive the parent
        parent.action_archive()
        self.assertFalse(parent.active)
        self.assertFalse(child_item.active)

        # Restore the parent
        parent.action_unarchive()
        self.assertTrue(parent.active)
        self.assertTrue(child_item.active)

    def test_kanban_view_properties_and_active_test(self):
        """Verify that archived articles and stages can be read with active_test=False in context."""
        parent = self.env['info.hub.article'].create({
            'name': 'Archived Kanban Parent',
            'category': 'workspace',
            'display_mode': 'kanban',
            'active': True,
        })
        self.env['info.hub.article'].create_default_item_stages(parent.id)
        parent.action_archive()

        # Check kanban view id retrieval
        view_id = self.env['info.hub.article'].get_kanban_view_id()
        self.assertTrue(view_id)

        # Check stage expansion with active_test=False context when parent is inactive
        domain = [('parent_id', '=', parent.id), ('is_article_item', '=', True)]
        expanded_stages = self.env['info.hub.article'].with_context(active_test=False)._read_group_stage_ids(None, domain)
        self.assertEqual(len(expanded_stages), 3)

    def test_trash_action_and_filter_excludes_article_items(self):
        """Verify that the Trash window action domain and the search view Trashed filter exclude article items and templates."""
        parent = self.env['info.hub.article'].create({
            'name': 'Parent Kanban Board',
            'category': 'workspace',
            'display_mode': 'kanban',
            'active': True,
        })
        child_item = self.env['info.hub.article'].create({
            'name': 'Kanban Card Item',
            'parent_id': parent.id,
            'is_article_item': True,
            'active': True,
        })
        parent.action_archive()

        # 1. Test Trashed filter in the search view
        search_view = self.env.ref('info_hub.view_info_article_search')
        # Check the domain in the 'trashed' filter
        filter_node = search_view.fields_get() # we can just inspect the search view's arch
        import xml.etree.ElementTree as ET
        root = ET.fromstring(search_view.arch)
        trashed_filter = root.find(".//filter[@name='trashed']")
        self.assertIsNotNone(trashed_filter)
        self.assertIn("('is_article_item', '=', False)", trashed_filter.attrib['domain'])
        self.assertIn("('is_template', '=', False)", trashed_filter.attrib['domain'])

        # 2. Test Trash action's domain
        trash_action = self.env.ref('info_hub.action_info_article_trash')
        self.assertEqual(trash_action.domain, "[('is_article_item', '=', False), ('active', '=', False)]")

        # 3. Test Templates filter context in the search view
        templates_filter = root.find(".//filter[@name='templates']")
        self.assertIsNotNone(templates_filter)
        self.assertIn("'active_test': False", templates_filter.attrib.get('context', ''))

    def test_kanban_web_read_group(self):
        """Simulate web_read_group RPC call for archived Kanban articles and items."""
        parent = self.env['info.hub.article'].create({
            'name': 'Parent Kanban Board',
            'category': 'workspace',
            'display_mode': 'kanban',
            'active': True,
        })
        self.env['info.hub.article'].create_default_item_stages(parent.id)
        stages = self.env['info.hub.article.stage'].search([('parent_id', '=', parent.id)])
        child_item = self.env['info.hub.article'].create({
            'name': 'Kanban Card Item',
            'parent_id': parent.id,
            'is_article_item': True,
            'active': True,
            'stage_id': stages[0].id,
        })
        parent.action_archive()

        # Call web_read_group mimicking client kanban view behavior (which sets read_group_expand=True)
        result = self.env['info.hub.article'].with_context(active_test=False, default_parent_id=parent.id, read_group_expand=True).web_read_group(
            domain=[('parent_id', '=', parent.id), ('is_article_item', '=', True)],
            groupby=['stage_id'],
        )
        self.assertTrue(result)
        self.assertEqual(len(result['groups']), 3)




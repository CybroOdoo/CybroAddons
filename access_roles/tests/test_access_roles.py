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
from lxml import etree
from odoo import Command
from odoo.modules.module import get_manifest
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAccessRoles(TransactionCase):
    """Comprehensive test suite for Access Roles module covering models and features."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_user = cls.env.ref('base.group_user')
        cls.group_system = cls.env.ref('base.group_system')
        cls.partner_model = cls.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)

        # Create a test access role
        cls.test_role = cls.env['access.role'].create({
            'name': 'Test Role',
            'groups_ids': [Command.set([cls.group_user.id, cls.group_system.id])],
        })

        # Create a second test access role for multi-record testing
        cls.test_role_2 = cls.env['access.role'].create({
            'name': 'Second Test Role',
            'groups_ids': [Command.set([cls.group_user.id])],
        })

        # Create a test user assigned to test_role
        cls.test_user = cls.env['res.users'].create({
            'name': 'Test Role User',
            'login': 'test_role_user',
            'email': 'test_role_user@example.com',
            'access_role_id': cls.test_role.id,
        })

        # Create role management record
        cls.role_management = cls.env['role.management'].create({
            'name': 'Test Role Management',
            'is_debug': True,
            'is_chatter': True,
            'is_readonly': False,
            'role_ids': [Command.set([cls.test_role.id])],
        })

    def test_01_manifest_metadata(self):
        """Verify manifest completeness, version, license, and dependencies."""
        manifest = get_manifest('access_roles')
        self.assertTrue(manifest, "Manifest for access_roles must exist.")
        self.assertEqual(manifest.get('name'), 'Access Roles')
        self.assertEqual(manifest.get('version'), '20.0.1.0.0')
        self.assertEqual(manifest.get('license'), 'LGPL-3')
        self.assertIn('mail', manifest.get('depends', []))
        self.assertIn('web', manifest.get('depends', []))

    def test_02_access_role_creation_and_counts(self):
        """Test access role creation, counts computation, and multi-recordset."""
        roles = self.test_role | self.test_role_2
        roles._compute_accesses_count()

        for role in roles:
            self.assertGreaterEqual(role.groups_count, 1)
            self.assertGreaterEqual(role.accesses_count, 0)
            self.assertGreaterEqual(role.rules_count, 0)

        # Multi-record write
        roles.write({'name': 'Updated Test Role'})
        self.assertEqual(self.test_role.name, 'Updated Test Role')
        self.assertEqual(self.test_role_2.name, 'Updated Test Role')

    def test_03_access_role_actions(self):
        """Test action helper methods returning window actions."""
        groups_act = self.test_role.action_get_groups()
        self.assertEqual(groups_act.get('res_model'), 'res.groups')
        self.assertEqual(groups_act.get('type'), 'ir.actions.act_window')

        access_act = self.test_role.action_get_accesses()
        self.assertEqual(access_act.get('res_model'), 'ir.access')
        self.assertEqual(access_act.get('type'), 'ir.actions.act_window')

        rules_act = self.test_role.action_get_rules()
        self.assertEqual(rules_act.get('res_model'), 'ir.access')
        self.assertEqual(rules_act.get('type'), 'ir.actions.act_window')

    def test_04_access_role_reified_groups_and_read(self):
        """Test reified group helpers, default_get, onchange, read, and write."""
        # default_get
        vals = self.env['access.role'].default_get(['name', 'groups_ids'])
        self.assertIn('groups_ids', vals)

        # onchange
        onchange_res = self.test_role.onchange(
            {'name': 'Test Role Onchange', 'groups_ids': [Command.set([self.group_user.id])]},
            ['name'],
            {'name': {}, 'groups_ids': {}},
        )
        self.assertIsInstance(onchange_res, dict)

        # fields_get
        fields_info = self.test_role.fields_get(['name', 'groups_ids'])
        self.assertIn('name', fields_info)

        # read
        read_res = self.test_role.read(['name', 'groups_ids'])
        self.assertTrue(read_res)
        self.assertEqual(read_res[0].get('id'), self.test_role.id)

        # _remove_reified_groups and _add_reified_groups
        raw_vals = {'in_group_%s' % self.group_user.id: True, 'name': 'Sample'}
        cleaned = self.test_role._remove_reified_groups(raw_vals)
        self.assertIn('groups_ids', cleaned)
        self.assertEqual(cleaned['name'], 'Sample')

    def test_05_role_management_lifecycle_and_multi(self):
        """Test role.management creation, compute methods, and open domain form."""
        rm1 = self.role_management
        rm2 = self.env['role.management'].create({
            'name': 'Second Role Management',
            'is_debug': False,
            'is_chatter': False,
            'is_readonly': True,
            'role_ids': [Command.set([self.test_role_2.id])],
        })

        rms = rm1 | rm2
        # Test multi-recordset compute
        rms._compute_selected_role_ids()
        rms._compute_access_role_menu_ids()

        for rm in rms:
            self.assertIsNotNone(rm.selected_role_ids)
            self.assertTrue(rm.access_role_menu_ids)

        # Test action_open_domain_form
        domain_rec = self.env['domain.model'].create({
            'name': "[('active', '=', True)]",
            'domain_model_id': self.partner_model.id,
        })
        self.env['field.access'].create({
            'model_id': self.partner_model.id,
            'domain_access_id': rm1.id,
            'domain_id': domain_rec.id,
        })
        act = rm1.action_open_domain_form()
        self.assertEqual(act.get('res_model'), 'domain.model')
        self.assertEqual(act.get('res_id'), domain_rec.id)

    def test_06_role_management_restriction_apis(self):
        """Test get_role_restrictions, get_export_restrictions, and check_model_access_restrictions."""
        # Test when env.user has role_management
        user = self.test_user
        self.test_role.write({'role_management_id': self.role_management.id})

        # Add model access to role management
        self.env['field.access'].create({
            'model_id': self.partner_model.id,
            'access_model_id': self.role_management.id,
            'is_hide_export': True,
            'is_hide_archive': True,
            'is_hide_create': True,
            'is_model_readonly': True,
        })

        RoleMgmt = self.env['role.management'].with_user(user)
        restrictions = RoleMgmt.get_role_restrictions()
        self.assertTrue(restrictions.get('is_debug'))
        self.assertTrue(restrictions.get('is_chatter'))

        export_restrictions = RoleMgmt.get_export_restrictions(user.id)
        self.assertTrue(export_restrictions)
        self.assertEqual(export_restrictions[0].get('model'), 'res.partner')
        self.assertTrue(export_restrictions[0].get('is_hide_export'))

        model_access = RoleMgmt.check_model_access_restrictions(user.id, 'res.partner')
        self.assertTrue(model_access.get('is_hide_create'))
        self.assertTrue(model_access.get('is_model_readonly'))

        # Empty restrictions when user has no role
        admin = self.env.ref('base.user_admin')
        admin.write({'access_role_id': False})
        AdminRoleMgmt = self.env['role.management'].with_user(admin)
        self.assertEqual(AdminRoleMgmt.get_role_restrictions(), {})
        self.assertEqual(AdminRoleMgmt.get_export_restrictions(admin.id), [])
        self.assertEqual(AdminRoleMgmt.check_model_access_restrictions(admin.id, 'res.partner'), {})

    def test_07_res_users_role_integration(self):
        """Test res.users creation and write with access_role_id and multi-user update."""
        user1 = self.env['res.users'].create({
            'name': 'Role User 1',
            'login': 'role_user_1',
            'email': 'role_user_1@example.com',
            'access_role_id': self.test_role.id,
        })
        user2 = self.env['res.users'].create({
            'name': 'Role User 2',
            'login': 'role_user_2',
            'email': 'role_user_2@example.com',
            'access_role_id': self.test_role_2.id,
        })

        # Verify initial groups synced
        self.assertIn(self.group_system.id, user1.group_ids.ids)

        # Multi-record write to switch roles
        users = user1 | user2
        users.write({'access_role_id': self.test_role_2.id})
        for u in users:
            self.assertEqual(u.access_role_id.id, self.test_role_2.id)

        # Multi-record write to clear role
        users.write({'access_role_id': False})
        for u in users:
            self.assertFalse(u.access_role_id)

    def test_08_res_users_onchange(self):
        """Test res.users _onchange_access_role_id on unsaved and saved records."""
        # Unsaved record triggers warning
        new_user = self.env['res.users'].new({
            'name': 'New Unsaved User',
            'access_role_id': self.test_role.id,
        })
        res = new_user._onchange_access_role_id()
        self.assertIn('warning', res)
        self.assertFalse(new_user.access_role_id)

        # Saved record write updates relation
        self.test_user.write({'access_role_id': self.test_role_2.id})
        self.assertIn(self.test_user.id, self.test_role_2.user_ids.ids)

    def test_09_domain_model_and_base_access_domain(self):
        """Test domain.model compute and BaseModel._access_domain override."""
        domain_rec = self.env['domain.model'].create({
            'name': "[('name', 'ilike', 'Test')]",
            'domain_model_id': self.partner_model.id,
        })
        self.assertEqual(domain_rec.domain_model_name, 'res.partner')

        # Multi-record compute
        domain_rec_2 = self.env['domain.model'].create({
            'name': '[]',
            'domain_model_id': False,
        })
        domains = domain_rec | domain_rec_2
        domains._compute_domain_model_name()
        self.assertEqual(domain_rec.domain_model_name, 'res.partner')
        self.assertFalse(domain_rec_2.domain_model_name)

        # Test _access_domain
        self.role_management.write({
            'domain_ids': [Command.set([domain_rec.id])],
            'role_ids': [Command.set([self.test_role.id])],
        })
        self.test_user.write({'access_role_id': self.test_role.id})
        Partner = self.env['res.partner'].with_user(self.test_user)
        access_dom = Partner._access_domain('read')
        self.assertTrue(access_dom)

        # Test superuser ignores role domain restrictions
        PartnerSuper = self.env['res.partner'].with_user(self.env.ref('base.user_root'))
        super_dom = PartnerSuper._access_domain('read')
        self.assertIsNotNone(super_dom)

    def test_10_field_access_onchange(self):
        """Test field.access _onchange_model_id clearing dependents."""
        fa = self.env['field.access'].new({
            'model_id': self.partner_model.id,
            'is_field_readonly': True,
        })
        fa._onchange_model_id()
        self.assertFalse(fa.fields_ids)
        self.assertFalse(fa.filter_ids)
        self.assertFalse(fa.group_ids)
        self.assertFalse(fa.button_ids)
        self.assertFalse(fa.tab_ids)

    def test_11_registries_and_hooks(self):
        """Test registry hooks and extraction methods."""
        # Button registry
        self.env['button.registry']._register_hook()
        all_buttons = self.env['button.registry'].get_all_buttons()
        self.assertIsInstance(all_buttons, dict)

        # Tab registry
        self.env['tab.registry']._register_hook()
        all_tabs = self.env['tab.registry'].get_all_tabs()
        self.assertIsInstance(all_tabs, dict)

        # Filter registry
        self.env['filter.registry']._register_hook()
        test_arch = '<search><filter name="test_f" string="Test Filter" domain="[(\'id\', \'=\', 1)]"/></search>'
        filters = self.env['filter.registry']._get_filter_elements_from_arch(test_arch)
        self.assertEqual(len(filters), 1)

        # GroupBy registry
        self.env['groupby.registry']._register_hook()
        tag = '<filter name="grp_name" string="Group Name" context="{\'group_by\': \'name\'}"/>'
        grp_attrs = self.env['groupby.registry']._extract_groupby_attributes(tag)
        self.assertEqual(grp_attrs.get('name'), 'grp_name')
        self.assertEqual(grp_attrs.get('string'), 'Group Name')

        # Test deduplication on repeated extraction
        self.env['groupby.registry']._create_or_update_groupby(
            'vendor', self.partner_model.id, [], "{'group_by': 'partner_id'}", 'Vendor'
        )
        self.env['groupby.registry']._create_or_update_groupby(
            'vendor', self.partner_model.id, [], "{'group_by': 'partner_id'}", 'Vendor'
        )
        vendor_records = self.env['groupby.registry'].search([
            ('name', '=', 'Vendor'),
            ('model_id', '=', self.partner_model.id)
        ])
        self.assertEqual(len(vendor_records), 1)

        self.env['filter.registry']._create_or_update_filter(
            'my_purchases', self.partner_model.id, [], "[('user_id', '=', uid)]", 'My Purchases'
        )
        self.env['filter.registry']._create_or_update_filter(
            'my_purchases', self.partner_model.id, [], "[('user_id', '=', uid)]", 'My Purchases'
        )
        filter_records = self.env['filter.registry'].search([
            ('name', '=', 'My Purchases'),
            ('model_id', '=', self.partner_model.id)
        ])
        self.assertEqual(len(filter_records), 1)

    def test_12_ir_ui_menu_filtering(self):
        """Test ir.ui.menu visibility filtering for users with hidden menus."""
        root_menu = self.env.ref('access_roles.access_role_menu_root', raise_if_not_found=False)
        if root_menu:
            child_menu = self.env['ir.ui.menu'].create({
                'name': 'Test Child Menu',
                'parent_id': root_menu.id,
            })
            self.role_management.write({'menu_ids': [Command.set([root_menu.id])]})
            self.test_user.write({'access_role_id': self.test_role.id})
            Menu = self.env['ir.ui.menu'].with_user(self.test_user)
            visible_menus = Menu._visible_menu_ids()
            self.assertNotIn(root_menu.id, visible_menus)
            blacklist = Menu._load_menus_blacklist()
            self.assertIn(root_menu.id, blacklist)
            self.assertIn(child_menu.id, blacklist)

    def test_13_ir_ui_view_postprocessing(self):
        """Test ir.ui.view postprocess modifications (buttons, fields, forms, lists)."""
        view = self.env['ir.ui.view']

        # Prepare field access restrictions
        fa_button = self.env['field.access'].create({
            'model_id': self.partner_model.id,
            'button_access_id': self.role_management.id,
        })
        btn_reg = self.env['button.registry'].create({
            'name': 'Test Action',
            'action_name': 'action_test',
            'model_id': self.partner_model.id,
        })
        fa_button.write({'button_ids': [Command.set([btn_reg.id])]})

        # Process button access
        tree = etree.fromstring('<form model_access_rights="res.partner"><button name="action_test"/></form>')
        processed_tree = view._process_button_access(tree, fa_button, 'res.partner')
        btn_node = processed_tree.xpath('//button')[0]
        self.assertEqual(btn_node.get('invisible'), '1')

        # Process form and list access
        name_field = self.env['ir.model.fields'].search([
            ('model_id', '=', self.partner_model.id),
            ('name', '=', 'name')
        ], limit=1)
        fa_field = self.env['field.access'].create({
            'model_id': self.partner_model.id,
            'access_field_id': self.role_management.id,
            'fields_ids': [Command.set([name_field.id])],
            'is_field_readonly': True,
        })
        field_tree = etree.fromstring('<form><field name="name"/></form>')
        processed_field = view._process_field_access(field_tree, fa_field, 'res.partner')
        self.assertEqual(processed_field.xpath('//field[@name="name"]')[0].get('readonly'), '1')

        fa_model = self.env['field.access'].create({
            'model_id': self.partner_model.id,
            'access_model_id': self.role_management.id,
            'is_model_readonly': True,
            'is_hide_create': True,
            'is_hide_delete': True,
            'is_hide_duplicate': True,
        })
        form_tree = etree.fromstring('<form><button name="save"/></form>')
        processed_form = view._process_form_access(form_tree, fa_model, self.role_management, 'res.partner')
        self.assertEqual(processed_form.xpath('//form')[0].get('create'), 'false')

        list_tree = etree.fromstring('<list><field name="name"/></list>')
        processed_list = view._process_list_access(list_tree, fa_model, self.role_management, 'res.partner')
        self.assertEqual(processed_list.xpath('//list')[0].get('create'), 'false')

        kanban_tree = etree.fromstring('<kanban><field name="name"/></kanban>')
        processed_kanban = view._process_kanban_access(kanban_tree, fa_model, self.role_management, 'res.partner')
        self.assertEqual(processed_kanban.xpath('//kanban')[0].get('create'), 'false')

    def test_14_res_groups_helpers_and_category_views(self):
        """Test res.groups helper methods and ir.module.category overrides."""
        Groups = self.env['res.groups']
        self.assertEqual(Groups.name_boolean_group(10), 'in_group_10')
        self.assertEqual(Groups.name_selection_groups([3, 1, 2]), 'sel_groups_1_2_3')
        self.assertTrue(Groups.is_boolean_group('in_group_5'))
        self.assertTrue(Groups.is_selection_groups('sel_groups_1_2'))
        self.assertEqual(Groups.get_boolean_group('in_group_42'), 42)
        self.assertEqual(Groups.get_selection_groups('sel_groups_4_5_6'), [4, 5, 6])

        # Test customize_role_group_fields
        customized = Groups.customize_role_group_fields('sel_groups_1_10_11', {}, 'access.role')
        self.assertEqual(customized.get('invisible'), '1')

        # Test ir.module.category write and unlink triggers
        cat = self.env['ir.module.category'].create({'name': 'Test New Cat'})
        cat.write({'name': 'Test Updated Cat'})
        cat_id = cat.id
        cat.unlink()
        self.assertFalse(self.env['ir.module.category'].browse(cat_id).exists())

    def test_15_security_acl_restrictions(self):
        """Test that regular employees cannot write or unlink role management configuration."""
        from odoo.exceptions import AccessError
        user_rm = self.role_management.with_user(self.test_user)
        with self.assertRaises(AccessError):
            user_rm.write({'name': 'Tampered Role Management'})
        with self.assertRaises(AccessError):
            user_rm.unlink()

from unittest.mock import patch

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger

from odoo.addons.odoo_dynamic_dashboard.models.dynamic_dashboard_ai import (
    DynamicDashboardAiGenerator,
)

USER_GROUP = 'odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_user'
MANAGER_GROUP = 'odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_manager'


@tagged('post_install', '-at_install')
class TestDynamicDashboardSecurity(TransactionCase):
    """ Access rights of each role on dashboards, their blocks, their menus and the
    data they show:

    - dashboard administrator: everything, on every dashboard
    - dashboard user: own dashboards (full access), shared dashboards (read only)
    - employee: only the dashboards put in a menu visible to one of their groups (read only)
    - portal user: nothing
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = new_test_user(cls.env, login='sec_manager', groups=MANAGER_GROUP)
        cls.user_a = new_test_user(cls.env, login='sec_user_a', groups=USER_GROUP)
        cls.user_b = new_test_user(cls.env, login='sec_user_b', groups=USER_GROUP)
        cls.employee = new_test_user(cls.env, login='sec_employee', groups='base.group_user')
        cls.portal = new_test_user(cls.env, login='sec_portal', groups='base.group_portal')
        cls.partner_model = cls.env['ir.model']._get('res.partner')

        Dashboard = cls.env['dynamic.dashboard']
        cls.private_a = Dashboard.with_user(cls.user_a).create({
            'name': 'Sec Private A',
            'block_ids': [Command.create({'model_id': cls.partner_model.id})],
        })
        cls.shared_a = Dashboard.with_user(cls.user_a).create({
            'name': 'Sec Shared A',
            'is_shared': True,
            'block_ids': [Command.create({'model_id': cls.partner_model.id})],
        })
        cls.private_b = Dashboard.with_user(cls.user_b).create({'name': 'Sec Private B'})
        cls.block_private_a = cls.private_a.block_ids
        cls.block_shared_a = cls.shared_a.block_ids

    def _visible(self, user, records):
        return records.with_user(user).search([('id', 'in', records.ids)])

    # ------------------------------------------------------------
    # Dashboards and blocks
    # ------------------------------------------------------------

    def test_dashboard_user(self):
        dashboards = self.private_a | self.shared_a | self.private_b
        self.assertEqual(self._visible(self.user_a, dashboards), self.private_a | self.shared_a)
        self.assertEqual(self._visible(self.user_b, dashboards), self.shared_a | self.private_b)

        # own dashboards: full access
        own = self.private_a.with_user(self.user_a)
        own.write({'name': 'Renamed'})
        own.block_ids.write({'width': '6'})
        self.env['dynamic.dashboard.block'].with_user(self.user_a).create({
            'dashboard_id': own.id, 'model_id': self.partner_model.id,
        })
        self.assertTrue(own.get_dashboard_data()['can_edit'])

        # shared dashboards of others: read only
        shared = self.shared_a.with_user(self.user_b)
        data = shared.get_dashboard_data()
        self.assertFalse(data['can_edit'])
        self.assertEqual(len(data['blocks']), 1)
        for operation in (
            lambda: shared.write({'name': 'Hijacked'}),
            shared.unlink,
            lambda: shared.block_ids.write({'width': '12'}),
            shared.block_ids.unlink,
            lambda: self.env['dynamic.dashboard.block'].with_user(self.user_b).create({
                'dashboard_id': shared.id, 'model_id': self.partner_model.id,
            }),
            lambda: shared.save_from_builder({'id': shared.id, 'name': 'Hijacked', 'blocks': []}),
            lambda: shared.set_block_sequence(shared.block_ids.ids),
        ):
            with self.subTest(operation=operation), self.assertRaises(AccessError):
                operation()
                self.env.flush_all()

        # private dashboards of others: no access at all
        with self.assertRaises(AccessError):
            self.private_a.with_user(self.user_b).get_dashboard_data()
        with self.assertRaises(AccessError):
            self.block_private_a.with_user(self.user_b).get_block_data_filtered([])

    def test_owner(self):
        """ Users own the dashboards they create; only administrators give them to others. """
        self.assertEqual(self.private_a.user_id, self.user_a)
        with self.assertRaises(AccessError):
            self.env['dynamic.dashboard'].with_user(self.user_a).create({
                'name': 'For B', 'user_id': self.user_b.id,
            })
        with self.assertRaises(AccessError):
            self.private_a.with_user(self.user_a).write({'user_id': self.user_b.id})
        self.private_a.with_user(self.user_a).write({'user_id': self.user_a.id, 'name': 'Still mine'})
        self.private_a.with_user(self.manager).write({'user_id': self.user_b.id})
        self.assertEqual(self._visible(self.user_b, self.private_a), self.private_a)
        self.assertFalse(self._visible(self.user_a, self.private_a))

    def test_manager(self):
        dashboards = self.private_a | self.shared_a | self.private_b
        self.assertEqual(self._visible(self.manager, dashboards), dashboards)
        other = self.private_a.with_user(self.manager)
        self.assertTrue(other.get_dashboard_data()['can_edit'])
        other.save_from_builder({'id': other.id, 'name': 'Managed', 'blocks': [
            {'block_type': 'tile', 'model': 'res.partner'},
        ]})
        self.assertEqual(other.name, 'Managed')
        self.private_b.with_user(self.manager).unlink()

    def test_employee_and_portal(self):
        dashboards = self.private_a | self.shared_a | self.private_b
        self.assertFalse(self._visible(self.employee, dashboards))
        with self.assertRaises(AccessError, msg="portal users cannot even search dashboards"):
            self._visible(self.portal, dashboards)
        for user in (self.employee, self.portal):
            with self.subTest(user=user.login):
                with self.assertRaises(AccessError):
                    self.shared_a.with_user(user).get_dashboard_data()
                with self.assertRaises(AccessError):
                    self.env['dynamic.dashboard'].with_user(user).create({'name': 'Nope'})
                with self.assertRaises(AccessError):
                    self.env['dynamic.dashboard.block'].with_user(user).preview_block(
                        {'block_type': 'tile', 'model': 'res.partner'},
                    )
                with self.assertRaises(AccessError):
                    self.env['dynamic.dashboard'].with_user(user).generate_with_ai("Sales")
        with self.assertRaises(AccessError):
            self.env['dynamic.dashboard'].with_user(self.portal).get_dashboard_list()

    def test_model_metadata(self):
        """ Dashboard users read the models and fields to build blocks, employees do not. """
        self.assertTrue(self.env['ir.model'].with_user(self.user_a).search_count([('model', '=', 'res.partner')]))
        self.assertTrue(self.env['ir.model.fields'].with_user(self.user_a).search_count([('model', '=', 'res.partner')]))
        for user in (self.employee, self.portal):
            with self.subTest(user=user.login), self.assertRaises(AccessError):
                self.env['ir.model'].with_user(user).search([('model', '=', 'res.partner')])

    # ------------------------------------------------------------
    # Menus
    # ------------------------------------------------------------

    def test_menu(self):
        root = self.env.ref('odoo_dynamic_dashboard.odoo_dynamic_dashboard_menu_root')
        for user, visible in ((self.user_a, True), (self.manager, True), (self.employee, False)):
            with self.subTest(user=user.login):
                self.assertEqual(root.id in self.env['ir.ui.menu'].with_user(user)._visible_menu_ids(), visible)
        with self.assertRaises(AccessError, msg="portal users have no backend menus"):
            self.env['ir.ui.menu'].with_user(self.portal)._visible_menu_ids()

        # only administrators put dashboards in menus
        with self.assertRaises(AccessError):
            self.private_a.with_user(self.user_a).set_dashboard_menu('Mine', root.id)
        with self.assertRaises(AccessError):
            self.private_a.with_user(self.user_a).read(['show_in_menu'])

        menu_id = self.private_a.with_user(self.manager).set_dashboard_menu(
            'For employees', False, group_ids=self.env.ref('base.group_user').ids,
        )
        menu = self.env['ir.ui.menu'].browse(menu_id)
        self.assertIn(menu_id, self.env['ir.ui.menu'].with_user(self.employee)._visible_menu_ids())

        # employees open the dashboard of their menu, read only
        dashboard = self.private_a.with_user(self.employee)
        data = dashboard.get_dashboard_data()
        self.assertFalse(data['can_edit'])
        self.assertFalse(data['blocks'][0]['error'])
        self.assertEqual(self.env['dynamic.dashboard'].with_user(self.employee).get_dashboard_list()[0]['id'],
                         dashboard.id)
        with self.assertRaises(AccessError):
            dashboard.write({'name': 'Hijacked'})
        with self.assertRaises(AccessError):
            self.private_a.with_user(self.portal).get_dashboard_data()

        # removing the menu removes the access it gave
        self.private_a.with_user(self.manager).show_in_menu = False
        self.assertFalse(menu.exists())
        self.assertFalse(self._visible(self.employee, self.private_a))

    # ------------------------------------------------------------
    # Data shown by the blocks
    # ------------------------------------------------------------

    def test_blocks_respect_record_rules(self):
        """ A block aggregates the records its viewer may read: the same shared block shows
        different figures to different users. """
        shared = self.env['dynamic.dashboard'].with_user(self.manager).create({
            'name': 'Sec Counting',
            'is_shared': True,
            'block_ids': [Command.create({
                'model_id': self.env['ir.model']._get_id('dynamic.dashboard'),
                'domain': "[('name', 'like', 'Sec ')]",
            })],
        })
        counts = {
            user.login: shared.with_user(user).get_dashboard_data()['blocks'][0]['value']
            for user in (self.manager, self.user_a, self.user_b)
        }
        # manager: all 4, A: private A + shared A + counting, B: private B + shared A + counting
        self.assertEqual(counts, {'sec_manager': 4, 'sec_user_a': 3, 'sec_user_b': 3})

    @mute_logger('odoo.addons.odoo_dynamic_dashboard.models.dynamic_dashboard_block')
    def test_blocks_respect_access_rights(self):
        """ A block on data its viewer cannot read shows an error instead of the data. """
        shared = self.env['dynamic.dashboard'].with_user(self.manager).create({
            'name': 'Sec Technical',
            'is_shared': True,
            'block_ids': [Command.create({'model_id': self.env['ir.model']._get_id('ir.config_parameter')})],
        })
        [block] = shared.with_user(self.user_a).get_dashboard_data()['blocks']
        self.assertEqual(block['error'], "You are not allowed to access this data.")
        self.assertNotIn('value', block)
        self.assertTrue(shared.block_ids.with_user(self.user_a).get_block_data_filtered([])['error'])
        # the admin, who can read the parameters, sees them
        self.assertFalse(shared.with_user(self.env.ref('base.user_admin')).get_dashboard_data()['blocks'][0]['error'])

    @mute_logger('odoo.addons.odoo_dynamic_dashboard.models.dynamic_dashboard_block')
    def test_filters_respect_access_rights(self):
        """ The filters of a viewer cannot reach fields they are not allowed to read. """
        def find_restricted_field():
            for model_name in sorted(self.env.registry):
                Model = self.env[model_name].with_user(self.user_b)
                if Model._abstract or Model._transient or not Model._auto or not Model.has_access('read'):
                    continue
                for name, field in Model._fields.items():
                    if field.store and field.groups and not Model.has_field_access(field, 'read'):
                        return model_name, name
            return None, None

        model_name, field_name = find_restricted_field()
        if not model_name:
            self.skipTest("no model with a restricted field readable by dashboard users")
        shared = self.env['dynamic.dashboard'].with_user(self.manager).create({
            'name': 'Sec Restricted',
            'is_shared': True,
            'block_ids': [Command.create({'model_id': self.env['ir.model']._get_id(model_name)})],
        })
        block = shared.block_ids.with_user(self.user_b)
        self.assertFalse(block.get_block_data_filtered([])['error'])
        data = block.get_block_data_filtered([(field_name, '!=', False)])
        self.assertEqual(data['error'], "You are not allowed to access this data.", f"{model_name}.{field_name}")

    def test_ai_analysis_access(self):
        with patch.object(DynamicDashboardAiGenerator, '_olg_chat', return_value="- Fine.\nRecommendation: none."):
            self.assertTrue(self.block_shared_a.with_user(self.user_b).get_ai_analysis()['analysis'])
            for user in (self.user_b, self.employee, self.portal):
                with self.subTest(user=user.login), self.assertRaises(AccessError):
                    self.block_private_a.with_user(user).get_ai_analysis()

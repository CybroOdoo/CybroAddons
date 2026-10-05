from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestDynamicDashboardMenu(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = new_test_user(
            cls.env, login='dashboard_manager',
            groups='odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_manager',
        )
        cls.dashboard_user = new_test_user(
            cls.env, login='dashboard_user', groups='odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_user',
        )
        cls.employee = new_test_user(cls.env, login='dashboard_employee', groups='base.group_user')
        cls.parent_menu = cls.env.ref('odoo_dynamic_dashboard.odoo_dynamic_dashboard_menu_root')
        cls.partner_model = cls.env['ir.model']._get('res.partner')

    def _create_dashboard(self, **values):
        return self.env['dynamic.dashboard'].with_user(self.manager).create({
            'name': 'Sales Overview',
            'block_ids': [(0, 0, {'model_id': self.partner_model.id})],
            **values,
        })

    def test_menu_lifecycle(self):
        dashboard = self._create_dashboard(show_in_menu=True, menu_parent_id=self.parent_menu.id)
        menu = dashboard.menu_id
        self.assertEqual(menu.name, 'Sales Overview')
        self.assertEqual(menu.parent_id, self.parent_menu)
        self.assertEqual(menu.action, dashboard.action_id)
        self.assertEqual(dashboard.action_id.params, {'dashboard_id': dashboard.id})
        self.assertEqual(menu.group_ids, self.env.ref('odoo_dynamic_dashboard.odoo_dynamic_dashboard_group_user'))

        dashboard.write({'name': 'Sales KPIs', 'menu_parent_id': False})
        self.assertEqual(menu.name, 'Sales KPIs')
        self.assertFalse(menu.parent_id)
        self.assertTrue(menu.web_icon, "a top-level dashboard menu is an app and needs an icon")

        action = dashboard.action_id
        dashboard.show_in_menu = False
        self.assertFalse(menu.exists())
        self.assertFalse(action.exists())

        dashboard.show_in_menu = True
        menu = dashboard.menu_id
        self.assertTrue(menu)
        dashboard.unlink()
        self.assertFalse(menu.exists())

    def test_menu_needs_manager(self):
        Dashboard = self.env['dynamic.dashboard'].with_user(self.dashboard_user)
        dashboard = Dashboard.create({'name': 'Mine'})
        self.assertFalse(dashboard.sudo().menu_id)
        with self.assertRaises(AccessError):
            dashboard.show_in_menu = True

    def test_menu_groups_grant_read(self):
        dashboard = self._create_dashboard()
        Dashboard = self.env['dynamic.dashboard'].with_user(self.employee)
        self.assertFalse(Dashboard.search([('id', '=', dashboard.id)]))

        dashboard.write({
            'show_in_menu': True,
            'menu_group_ids': [(6, 0, self.env.ref('base.group_user').ids)],
        })
        self.assertEqual(Dashboard.search([('id', '=', dashboard.id)]), dashboard)
        data = Dashboard.browse(dashboard.id).get_dashboard_data()
        self.assertFalse(data['can_edit'])
        self.assertFalse(data['blocks'][0]['error'])

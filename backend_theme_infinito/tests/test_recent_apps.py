from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRecentApps(TransactionCase):

    def setUp(self):
        super().setUp()
        self.RecentApps = self.env['recent.apps']

    def test_compute_with_menu_icon(self):
        menu = self.env.ref('base.menu_administration')
        rec = self.RecentApps.create({
            'app_id': menu.id,
            'user_id': self.env.user.id,
        })
        self.assertEqual(rec.name, menu.name)
        self.assertTrue(rec.icon)
        # type is the part of web_icon after the first '.'
        expected = str(menu.web_icon).split('.', 1)
        self.assertEqual(rec.type, expected[1] if len(expected) > 1 else '')

    def test_compute_type_without_icon(self):
        menu = self.env['ir.ui.menu'].create({'name': 'Test Menu No Icon'})
        rec = self.RecentApps.create({
            'app_id': menu.id,
            'user_id': self.env.user.id,
        })
        self.assertEqual(rec.name, 'Test Menu No Icon')
        self.assertEqual(rec.type, '')
        self.assertFalse(rec.icon)

    def test_recompute_when_app_changes(self):
        menu_a = self.env['ir.ui.menu'].create({'name': 'Menu A'})
        menu_b = self.env['ir.ui.menu'].create({'name': 'Menu B'})
        rec = self.RecentApps.create({
            'app_id': menu_a.id,
            'user_id': self.env.user.id,
        })
        self.assertEqual(rec.name, 'Menu A')
        rec.app_id = menu_b.id
        self.assertEqual(rec.name, 'Menu B')
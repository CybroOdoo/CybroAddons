import json

from odoo.tests import tagged

from .common import ThemeHttpCase


@tagged('post_install', '-at_install')
class TestThemeControllerSecurity(ThemeHttpCase):
    def test_internal_user_cannot_change_global_theme(self):
        self.login(self.internal)
        for path, params in [
            ('save_styles', {'kwargs': {'changed_styles': '{}', 'object_class': 'test'}}),
            ('reset_to_default', {}),
            ('set_advanced_data', {'args': [{'vals': self.preferences()}]}),
        ]:
            with self.subTest(endpoint=path):
                self.assert_access_denied(self.rpc('/theme_studio/' + path, params))
        self.assertFalse(self.parameters.get_str('backend_theme_infinito.dynamic_css'))

    def test_admin_can_save_read_and_reset_css(self):
        self.login(self.admin)
        result = self.rpc('/theme_studio/save_styles', {'kwargs': {
            'changed_styles': json.dumps({'color': 'red'}), 'object_class': 'test',
        }})
        self.assertTrue(result['result'])
        self.assertIn('color: red !important', self.parameters.get_str('backend_theme_infinito.dynamic_css'))
        self.assertEqual(self.rpc('/theme_studio/get_current_style', {
            'kwargs': {'selector': '.test'},
        })['result'], [['color', 'red ']])
        self.assertTrue(self.rpc('/theme_studio/reset_to_default')['result'])
        self.assertFalse(self.parameters.get_str('backend_theme_infinito.dynamic_css'))

    def test_css_requires_internal_authenticated_user(self):
        self.login(self.internal)
        self.assertEqual(self.url_open('/backend_theme_infinito/dynamic_styles.css').status_code, 200)
        self.login(self.portal)
        response = self.url_open('/backend_theme_infinito/dynamic_styles.css')
        self.assertEqual(response.status_code, 403)
        self.authenticate(None, None)
        response = self.url_open('/backend_theme_infinito/dynamic_styles.css', allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))

    def test_personal_editing_permissions_and_user_isolation(self):
        self.login(self.internal)
        params = {'args': [{'vals': self.preferences()}]}
        self.assert_access_denied(self.rpc('/theme_studio/set_advanced_data_user', params))
        self.parameters.set_bool('backend_theme_infinito.is_user_edit', True)
        other_values = self.other.read(['is_rtl', 'loader_class', 'dark_start'])[0]
        self.assertTrue(self.rpc('/theme_studio/set_advanced_data_user', params)['result'])
        self.assertTrue(self.internal.is_rtl)
        self.assertEqual(self.internal.loader_class, 'ring')
        self.assertEqual(self.internal.dark_start, 20.5)
        self.assertEqual(self.other.read(['is_rtl', 'loader_class', 'dark_start'])[0], other_values)
        self.login(self.portal)
        self.assert_access_denied(self.rpc('/theme_studio/set_advanced_data_user', params))

    def test_bookmark_add_deduplicate_and_private_remove(self):
        action = self.env['ir.actions.client'].create({'name': 'Theme action', 'tag': 'theme_test'})
        menu = self.env['ir.ui.menu'].create({'name': 'Theme menu', 'action': f'ir.actions.client,{action.id}'})
        params = {'args': {'menu': {
            'actionId': action.id, 'menuId': menu.id, 'menuUrl': '/odoo/theme-test', 'name': 'Theme menu',
        }}}
        self.login(self.internal)
        for _ in range(2):
            self.assertTrue(self.rpc('/theme_studio/add_menu_bookmarks', params)['result'])
        bookmarks = self.env['infinito.menu.bookmark'].search([('menu_id', '=', menu.id)])
        self.assertEqual(len(bookmarks), 1)
        self.assertEqual(bookmarks.user_id, self.internal)
        self.login(self.other)
        self.assertTrue(self.rpc('/theme_studio/add_menu_bookmarks', params)['result'])
        self.assertTrue(self.rpc('/theme_studio/remove_menu_bookmarks', params)['result'])
        self.assertTrue(bookmarks.exists())
        self.login(self.internal)
        self.assertTrue(self.rpc('/theme_studio/remove_menu_bookmarks', params)['result'])
        self.assertFalse(bookmarks.exists())

    def test_recent_apps_are_private(self):
        menu = self.env['ir.ui.menu'].create({'name': 'Recent app'})
        self.env['recent.apps'].create({'app_id': menu.id, 'user_id': self.other.id})
        self.login(self.internal)
        self.assertEqual(self.rpc('/theme_studio/get_recent_apps')['result'], [])
        self.assertTrue(self.rpc('/theme_studio/add_recent_app', {'args': [{'appId': menu.id}]})['result'])
        rows = self.rpc('/theme_studio/get_recent_apps')['result']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['user_id'][0], self.internal.id)

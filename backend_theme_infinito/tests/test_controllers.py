import json

from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user
from odoo.addons.backend_theme_infinito.controllers.main import _minify_css_string

ROUTE = '/theme_studio/'
ADV = {
    'userEdit': True, 'loaderClass': 'default',
    'infinitoDarkStart': 19.0, 'infinitoDarkEnd': 5.0,
    'sidebar': True, 'fullscreen': True, 'sidebarIcon': True,
    'sidebarName': True, 'sidebarCompany': True, 'sidebarUser': True,
    'recentApps': True, 'fullScreenApp': True, 'infinitoRtl': False,
    'infinitoDark': False, 'infinitoDarkMode': 'all',
    'infinitoBookmark': True,
}


@tagged('post_install', '-at_install')
class TestThemeStudioControllers(HttpCase):

    def _rpc(self, route, params=None):
        response = self.url_open(
            route,
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call',
                             'params': params or {}}),
            headers={'Content-Type': 'application/json'})
        return response.json()

    def _param(self, key):
        return self.env['ir.config_parameter'].sudo().get_param(key)

    def test_save_and_get_style(self):
        self.authenticate('admin', 'admin')
        res = self._rpc(ROUTE + 'save_styles', {'kwargs': {
            'changed_styles': json.dumps({'color': 'red'}),
            'object_class': 'o_test'}})
        self.assertTrue(res['result'])
        self.assertIn('o_test', self._param('backend_theme_infinito.dynamic_css'))
        res = self._rpc(ROUTE + 'get_current_style', {'kwargs': {'selector': '.o_test'}})
        self.assertIn(['color', 'red'], res['result'])
        res = self._rpc(ROUTE + 'get_current_style', {'kwargs': {'selector': '.nope'}})
        self.assertFalse(res['result'])

    def test_admin_only_routes_reject_plain_user(self):
        new_test_user(self.env, login='theme_plain', groups='base.group_user')
        self.authenticate('theme_plain', 'theme_plain')
        for route, params in (
            ('save_styles', {'kwargs': {'changed_styles': '{}', 'object_class': 'x'}}),
            ('reset_to_default', {}),
            ('set_advanced_data', {'args': [{'vals': ADV}]}),
        ):
            self.assertIn('error', self._rpc(ROUTE + route, params), route)

    def test_reset_to_default(self):
        self.authenticate('admin', 'admin')
        self.env['ir.config_parameter'].sudo().set_param(
            'backend_theme_infinito.dynamic_css', '.a{color:red}')
        self.assertTrue(self._rpc(ROUTE + 'reset_to_default')['result'])
        self.assertFalse(self._param('backend_theme_infinito.dynamic_css'))

    def test_serve_dynamic_styles(self):
        response = self.url_open('/backend_theme_infinito/dynamic_styles.css')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/css', response.headers['Content-Type'])

    def test_set_advanced_data(self):
        self.authenticate('admin', 'admin')
        res = self._rpc(ROUTE + 'set_advanced_data', {'args': [{'vals': ADV}]})
        self.assertTrue(res['result'])
        self.assertEqual(self._param('backend_theme_infinito.is_user_edit'), 'True')
        self.assertFalse(self._rpc(ROUTE + 'set_advanced_data', {'args': []})['result'])

    def test_set_advanced_data_user(self):
        self.authenticate('admin', 'admin')
        res = self._rpc(ROUTE + 'set_advanced_data_user', {'args': [{'vals': ADV}]})
        self.assertTrue(res['result'])
        self.assertFalse(self._rpc(ROUTE + 'set_advanced_data_user', {'args': []})['result'])

    def test_recent_apps_limit_and_listing(self):
        self.authenticate('admin', 'admin')
        for menu in self.env['ir.ui.menu'].search([], limit=7):
            self._rpc(ROUTE + 'add_recent_app', {'args': [{'appId': menu.id}]})
        admin = self.env.ref('base.user_admin')
        self.assertLessEqual(
            self.env['recent.apps'].sudo().search_count([('user_id', '=', admin.id)]), 5)
        res = self._rpc(ROUTE + 'get_recent_apps')
        self.assertIsInstance(res['result'], list)

    def test_menu_bookmarks(self):
        self.authenticate('admin', 'admin')
        menu = self.env['ir.ui.menu'].search([], limit=1)
        admin = self.env.ref('base.user_admin')
        Bookmark = self.env['infinito.menu.bookmark'].sudo()
        domain = [('user_id', '=', admin.id), ('menu_id', '=', menu.id)]
        payload = {'args': {'menu': {
            'actionId': False, 'menuId': menu.id,
            'menuUrl': '/odoo/test', 'name': 'My mark'}}}
        self.assertTrue(self._rpc(ROUTE + 'add_menu_bookmarks', payload)['result'])
        self.assertEqual(len(Bookmark.search(domain)), 1)
        payload['args']['menu']['name'] = 'Renamed'
        self._rpc(ROUTE + 'add_menu_bookmarks', payload)
        self.env.invalidate_all()
        self.assertEqual(Bookmark.search(domain).name, 'Renamed')
        self.assertFalse(self._rpc(ROUTE + 'add_menu_bookmarks', {'args': {'menu': {}}})['result'])
        self.assertTrue(self._rpc(ROUTE + 'remove_menu_bookmarks', payload)['result'])
        self.assertFalse(Bookmark.search(domain))
        self.assertFalse(self._rpc(ROUTE + 'remove_menu_bookmarks', {'args': {'menu': {}}})['result'])

    def test_get_presets(self):
        self.authenticate('admin', 'admin')
        self.assertTrue(self._rpc(ROUTE + 'get_presets')['result'])

    def test_minify_branches(self):
        out = _minify_css_string(
            '.a{pointer-events:none;color:red !important;margin:0}.a{padding:1px}')
        self.assertNotIn('pointer-events', out)
        self.assertIn('color:red !important;', out)
        self.assertIn('margin:0 !important;', out)
        self.assertIn('padding:1px !important;', out)

    def test_add_recent_app_without_app_id(self):
        self.authenticate('admin', 'admin')
        self._rpc(ROUTE + 'add_recent_app', {'args': []})  # line 242
        self._rpc(ROUTE + 'add_recent_app', {'args': [{}]})  # line 240

    def test_bookmark_branches(self):
        self.authenticate('admin', 'admin')
        menu = self.env['ir.ui.menu'].search([], limit=1)
        action = self.env['ir.actions.actions'].search([], limit=1)
        cases = (
            {'menuId': menu.id, 'menuUrl': False, 'name': False},  # 293, 307 / remove 357
            {'menuUrl': '/odoo/only-url', 'name': 'U'},  # 309 / remove 359
            {'actionId': action.id, 'menuUrl': False, 'name': False},  # 295-297, 311 / remove 361
            {'menuId': 999999999, 'menuUrl': '/odoo/ghost', 'name': False},  # 291, AND/OR branch
            {'menuId': menu.id, 'menuUrl': '/odoo/both', 'name': 'B'},  # AND/OR branch
        )
        for case in cases:
            for _ in range(2):  # the second call takes the "existing bookmark" update path
                res = self._rpc(ROUTE + 'add_menu_bookmarks', {'args': {'menu': case}})
                self.assertTrue(res['result'], case)
            res = self._rpc(ROUTE + 'remove_menu_bookmarks', {'args': {'menu': case}})
            self.assertTrue(res['result'], case)
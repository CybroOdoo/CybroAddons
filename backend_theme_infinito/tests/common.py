from odoo.tests import HttpCase
from odoo.tests.common import new_test_user


class ThemeHttpCase(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.internal = new_test_user(cls.env, login='theme_internal', groups='base.group_user')
        cls.other = new_test_user(cls.env, login='theme_other', groups='base.group_user')
        cls.admin = new_test_user(cls.env, login='theme_admin', groups='base.group_system')
        cls.portal = new_test_user(cls.env, login='theme_portal', groups='base.group_portal')
        cls.env['res.users.settings'].create({'user_id': cls.portal.id})
        cls.parameters = cls.env['ir.config_parameter'].sudo()

    def setUp(self):
        super().setUp()
        self.parameters.set_bool('backend_theme_infinito.is_user_edit', False)
        self.parameters.set_str('backend_theme_infinito.dynamic_css', '')

    def rpc(self, path, params=None):
        return self.url_open(path, json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 1, 'params': params or {},
        }).json()

    def login(self, user):
        self.authenticate(user.login, user.login)

    def preferences(self):
        return {
            'userEdit': True, 'sidebar': True, 'fullscreen': False,
            'sidebarIcon': True, 'sidebarName': True, 'sidebarCompany': False,
            'sidebarUser': True, 'recentApps': False, 'fullScreenApp': False,
            'infinitoRtl': True, 'infinitoDark': True,
            'infinitoDarkMode': 'schedule', 'infinitoBookmark': True,
            'loaderClass': 'ring', 'infinitoDarkStart': 20.5, 'infinitoDarkEnd': 6.25,
        }

    def assert_access_denied(self, response):
        self.assertEqual(response['error']['data']['name'], 'odoo.exceptions.AccessError')

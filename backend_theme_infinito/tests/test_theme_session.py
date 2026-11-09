from odoo.tests import tagged

from .common import ThemeHttpCase
from ..models.ir_http import float_to_time, to_bool


@tagged('post_install', '-at_install')
class TestThemeSession(ThemeHttpCase):
    def session_info(self, user):
        self.login(user)
        response = self.rpc('/web/session/get_session_info')
        self.assertNotIn('error', response)
        return response['result']

    def test_global_flags_and_schedule_use_real_parameters(self):
        for key, value in {
            'is_sidebar_enabled': 'False', 'is_recent_apps': 'True',
            'is_rtl': 'True', 'dark_start': '20.5', 'dark_end': '6.25',
        }.items():
            self.parameters.set_str('backend_theme_infinito.' + key, value)
        data = self.session_info(self.internal)
        self.assertIs(data['sidebar'], False)
        self.assertIs(data['recentApps'], True)
        self.assertIs(data['infinitoRtl'], True)
        self.assertIs(data['infinitoCanManageTheme'], False)
        self.assertEqual(data['infinitoDarkStart'], '20:30')
        self.assertEqual(data['infinitoDarkEnd'], '06:15')
        self.assertEqual(data['uid'], self.internal.id)

    def test_personal_preferences_override_global_defaults(self):
        self.parameters.set_bool('backend_theme_infinito.is_user_edit', True)
        self.parameters.set_bool('backend_theme_infinito.is_rtl', False)
        self.internal.write({
            'is_sidebar_enabled': True, 'is_sidebar_icon': False,
            'is_rtl': True, 'loader_class': 'rotating', 'dark_start': 20.5,
        })
        data = self.session_info(self.internal)
        self.assertIs(data['userEdit'], True)
        self.assertIs(data['sidebar'], True)
        self.assertIs(data['sidebarIcon'], False)
        self.assertIs(data['infinitoRtl'], True)
        self.assertEqual(data['loaderClass'], 'rotating')
        self.assertEqual(data['infinitoDarkStart'], '20:30')

    def test_admin_capability_and_private_bookmark_serialization(self):
        self.env['infinito.menu.bookmark'].create({
            'user_id': self.admin.id, 'name': 'Sales', 'url': '/odoo/sales',
        })
        self.env['infinito.menu.bookmark'].create({
            'user_id': self.other.id, 'name': 'Private', 'url': '/odoo/private',
        })
        data = self.session_info(self.admin)
        self.assertIs(data['infinitoCanManageTheme'], True)
        self.assertEqual(len(data['infinitoMenuBookmarks']), 1)
        self.assertEqual(data['infinitoMenuBookmarks'][0]['short_name'], 'SA')

    def test_portal_session_has_no_theme_preferences(self):
        data = self.session_info(self.portal)
        self.assertNotIn('sidebar', data)
        self.assertNotIn('infinitoMenuBookmarks', data)

    def test_boolean_and_time_conversion(self):
        for value in [False, None, '', 'False', '0']:
            self.assertIs(to_bool(value), False)
        for value in [True, 'True', '1', 'yes']:
            self.assertIs(to_bool(value), True)
        self.assertEqual(float_to_time(0), '00:00')
        self.assertEqual(float_to_time(23.5), '23:30')

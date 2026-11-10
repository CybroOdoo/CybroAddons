from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.backend_theme_infinito import icon_hooks


@tagged('post_install', '-at_install')
class TestIconHooks(TransactionCase):

    def test_all_icon_files_exist(self):
        for filename in set(icon_hooks.MENU_ICON_MAP.values()):
            self.assertTrue(icon_hooks._theme_icon_b64(filename), filename)

    def test_post_init_hook(self):
        menu = self.env['ir.ui.menu'].create({'name': 'Contacts'})
        asset = self.env['ir.asset'].create({
            'name': 'stale', 'bundle': 'web.assets_backend',
            'path': 'backend_theme_infinito/static/src/css/dynamic_styles.css'})
        icon_hooks.icons_post_init_hook(self.env)
        self.assertEqual(menu.web_icon_data, icon_hooks._theme_icon_b64('contact.png'))
        self.assertFalse(asset.exists())
        param = self.env['ir.config_parameter'].sudo().get_param
        self.assertEqual(param('backend_theme_infinito.is_sidebar_enabled'), 'True')

    def test_uninstall_hook(self):
        menu = self.env['ir.ui.menu'].create({'name': 'Contacts'})
        icon_hooks.icons_post_init_hook(self.env)
        icon_hooks.icons_uninstall_hook(self.env)
        self.assertNotEqual(menu.web_icon_data, icon_hooks._theme_icon_b64('contact.png'))

    def test_uninstall_hook_survives_errors(self):
        menu = self.env['ir.ui.menu'].create({'name': 'Contacts'})
        icon_hooks.icons_post_init_hook(self.env)
        with patch.object(icon_hooks, '_theme_icon_b64', side_effect=OSError):
            icon_hooks.icons_uninstall_hook(self.env)
        self.assertTrue(menu.exists())
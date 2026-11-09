from odoo.tests import HttpCase, tagged
from odoo.addons.web.tests.test_js import unit_test_error_checker


@tagged('post_install', '-at_install')
class TestThemeUI(HttpCase):
    def test_theme_hoot(self):
        # Restrict the browser run to this addon's test modules.
        self.browser_js(
            '/web/tests?headless&loglevel=2&preset=desktop&timeout=15000&id=242dd51f',
            '', login='admin', timeout=180,
            success_signal='[HOOT] Test suite succeeded',
            error_checker=unit_test_error_checker,
        )

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import os
import re

from odoo.tests import TransactionCase, tagged

MODULE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _theme_files(*folders, extensions):
    """Yield (relative_path, content) of the theme's own source files."""
    for folder in folders:
        for root, _dirs, files in os.walk(os.path.join(MODULE_PATH, folder)):
            for name in files:
                if name.endswith(extensions):
                    path = os.path.join(root, name)
                    with open(path, encoding='utf-8') as handle:
                        yield os.path.relpath(path, MODULE_PATH), handle.read()


@tagged('post_install', '-at_install')
class TestThemeSourceRules(TransactionCase):
    """Source-level guards: Odoo 20 dropped Font Awesome and t-esc."""

    def test_no_font_awesome_left(self):
        """No Font Awesome class or CDN may remain in views, JS or CSS."""
        pattern = re.compile(
            r'\bfa-(?:solid|regular|brands)\b|\bfa fa-|class="[^"]*\bfa-[a-z]|font-?awesome',
            re.IGNORECASE,
        )
        offenders = []
        for rel, content in _theme_files('views', 'data', 'static/src', extensions=('.xml', '.js', '.css', '.scss')):
            for number, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    offenders.append(f'{rel}:{number}')
        self.assertFalse(offenders, 'Font Awesome is not supported in Odoo 20: %s' % offenders)

    def test_no_t_esc(self):
        """Templates must use t-out; t-esc is deprecated for the Odoo 20 target."""
        offenders = [
            rel for rel, content in _theme_files('views', 'data', extensions=('.xml',))
            if re.search(r'\bt-esc\b', content)
        ]
        self.assertFalse(offenders, 't-esc found, use t-out instead: %s' % offenders)

    def test_icon_names_exist_in_odoo_icon_set(self):
        """Every data-icon used by the theme must be in Odoo's Material Symbols subset
        (otherwise the icon renders blank). Brand icons (oi_*) are skipped."""
        import odoo.addons.web as web_addon
        wishlist = os.path.join(
            os.path.dirname(web_addon.__file__), 'tooling', 'icons', 'icons_wishlist.txt')
        if not os.path.exists(wishlist):
            self.skipTest('icons_wishlist.txt not found in this Odoo version')
        with open(wishlist, encoding='utf-8') as handle:
            available = {line.strip() for line in handle if line.strip()}

        used = {}
        for rel, content in _theme_files('views', 'static/src/js', extensions=('.xml', '.js')):
            for name in re.findall(r'data-icon=["\']([a-z0-9_]+)["\']', content):
                used.setdefault(name, rel)
        missing = {
            name: rel for name, rel in used.items()
            if not name.startswith('oi_') and name not in available
        }
        self.assertFalse(missing, 'Icons not available in Odoo 20: %s' % missing)

    def test_no_external_icon_cdn(self):
        """The layout must not pull third-party stylesheets for icons."""
        for rel, content in _theme_files('views', extensions=('.xml',)):
            self.assertNotIn('cdnjs.cloudflare.com', content, rel)

    def test_manifest_targets_odoo_20(self):
        manifest = self.env['ir.module.module'].search([('name', '=', 'theme_velora')])
        self.assertTrue(manifest.latest_version.startswith('20.0'), manifest.latest_version)

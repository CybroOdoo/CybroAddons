# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
"""
Unit tests for database_delete_protection/controllers/database_delete_protection.py

All external dependencies (odoo config, http, lxml, file_open, qweb_render)
are patched via unittest.mock so no real Odoo environment or filesystem access
is required.
"""
import unittest
from unittest.mock import MagicMock, patch, mock_open

from odoo.tests.common import BaseCase, tagged

# ---------------------------------------------------------------------------
# Module-level patch targets
# ---------------------------------------------------------------------------
CONTROLLERS_MODULE = (
    'odoo.addons.database_delete_protection.controllers'
    '.database_delete_protection'
)


@tagged('post_install', '-at_install')
class TestDatabaseControllerRenderTemplate(BaseCase):
    """Tests for Database._render_template, which builds QWeb context and
    renders the database manager template with deletion-protection awareness."""

    def _get_controller_instance(self):
        """Return a bare Database controller instance without calling __init__."""
        from odoo.addons.database_delete_protection.controllers.database_delete_protection import (
            Database,
        )
        return Database.__new__(Database)

    def _common_patches(self):
        """Return a dict of patch objects shared across most tests."""
        mock_config = MagicMock()
        mock_config.__getitem__ = MagicMock(return_value=True)
        mock_config.get = MagicMock(return_value=False)
        mock_config.verify_admin_password = MagicMock(return_value=False)
        return {
            'odoo_config': patch(
                f'{CONTROLLERS_MODULE}.odoo.tools.config',
                mock_config,
            ),
            'db_list_lang': patch(
                f'{CONTROLLERS_MODULE}.odoo.service.db.exp_list_lang',
                return_value=[],
            ),
            'db_list_countries': patch(
                f'{CONTROLLERS_MODULE}.odoo.service.db.exp_list_countries',
                return_value=[],
            ),
            'db_list_incompatible': patch(
                f'{CONTROLLERS_MODULE}.odoo.service.db.list_db_incompatible',
                return_value=[],
            ),
            'http_db_list': patch(
                f'{CONTROLLERS_MODULE}.http.db_list',
                return_value=['mydb'],
            ),
            'qweb_render': patch(
                f'{CONTROLLERS_MODULE}.qweb_render',
                return_value='<html></html>',
            ),
            'file_open': patch(
                f'{CONTROLLERS_MODULE}.file_open',
                mock_open(read_data='<html></html>'),
            ),
            'html_doc': patch(
                f'{CONTROLLERS_MODULE}.html.document_fromstring',
                return_value=MagicMock(),
            ),
            'html_frag': patch(
                f'{CONTROLLERS_MODULE}.html.fragment_fromstring',
                return_value=MagicMock(),
            ),
        }

    # ------------------------------------------------------------------
    # Test 1 – manage defaults to True when not supplied
    # ------------------------------------------------------------------
    def test_render_template_sets_manage_default(self):
        """_render_template should set d['manage'] = True when not provided."""
        patches = self._common_patches()
        started = {k: v.start() for k, v in patches.items()}
        try:
            ctrl = self._get_controller_instance()
            ctrl._render_template()
            # qweb_render is called; the context 'd' is its second argument
            call_args = started['qweb_render'].call_args
            context_d = call_args[0][1]          # positional arg index 1
            self.assertTrue(context_d.get('manage'),
                            "'manage' should default to True")
        finally:
            for p in patches.values():
                p.stop()

    # ------------------------------------------------------------------
    # Test 2 – db_delete_restrict config is parsed into a list
    # ------------------------------------------------------------------
    def test_render_template_with_db_delete_restrict(self):
        """When db_delete_restrict is set, delete_restrict list is built
        from comma-separated values with spaces stripped."""
        patches = self._common_patches()
        mock_config = MagicMock()
        mock_config.__getitem__ = MagicMock(return_value=True)
        mock_config.verify_admin_password = MagicMock(return_value=False)
        mock_config.get = MagicMock(return_value='db1, db2, db3')
        patches['odoo_config'] = patch(
            f'{CONTROLLERS_MODULE}.odoo.tools.config', mock_config
        )

        started = {k: v.start() for k, v in patches.items()}
        try:
            ctrl = self._get_controller_instance()
            ctrl._render_template()
            call_args = started['qweb_render'].call_args
            context_d = call_args[0][1]
            self.assertIn('delete_restrict', context_d,
                          "'delete_restrict' must be in context")
            self.assertEqual(
                sorted(context_d['delete_restrict']),
                ['db1', 'db2', 'db3'],
                "Parsed list should match split/stripped config value",
            )
        finally:
            for p in patches.values():
                p.stop()

    # ------------------------------------------------------------------
    # Test 3 – no delete_restrict key when config is absent
    # ------------------------------------------------------------------
    def test_render_template_without_db_delete_restrict(self):
        """When db_delete_restrict is not configured, delete_restrict should
        NOT appear in the template context."""
        patches = self._common_patches()
        started = {k: v.start() for k, v in patches.items()}
        try:
            ctrl = self._get_controller_instance()
            ctrl._render_template()
            call_args = started['qweb_render'].call_args
            context_d = call_args[0][1]
            self.assertNotIn('delete_restrict', context_d,
                             "'delete_restrict' must be absent without config")
        finally:
            for p in patches.values():
                p.stop()

    # ------------------------------------------------------------------
    # Test 4 – AccessDenied falls back to request.db
    # ------------------------------------------------------------------
    def test_render_template_access_denied(self):
        """When http.db_list() raises AccessDenied, databases falls back to
        [request.db] when request.db is set."""
        import odoo.exceptions
        patches = self._common_patches()
        patches['http_db_list'] = patch(
            f'{CONTROLLERS_MODULE}.http.db_list',
            side_effect=odoo.exceptions.AccessDenied,
        )

        mock_request = MagicMock()
        mock_request.db = 'fallback_db'
        patches['request'] = patch(
            f'{CONTROLLERS_MODULE}.request', mock_request
        )

        started = {k: v.start() for k, v in patches.items()}
        try:
            ctrl = self._get_controller_instance()
            ctrl._render_template()
            call_args = started['qweb_render'].call_args
            context_d = call_args[0][1]
            self.assertEqual(
                context_d.get('databases'), ['fallback_db'],
                "Should fall back to [request.db] on AccessDenied",
            )
        finally:
            for p in patches.values():
                p.stop()

    # ------------------------------------------------------------------
    # Test 5 – qweb_render called with 'database_manager' template name
    # ------------------------------------------------------------------
    def test_render_template_calls_qweb_render(self):
        """_render_template must call qweb_render with 'database_manager'
        as the first argument."""
        patches = self._common_patches()
        started = {k: v.start() for k, v in patches.items()}
        try:
            ctrl = self._get_controller_instance()
            result = ctrl._render_template()
            started['qweb_render'].assert_called_once()
            first_arg = started['qweb_render'].call_args[0][0]
            self.assertEqual(first_arg, 'database_manager',
                             "First arg to qweb_render must be 'database_manager'")
            self.assertEqual(result, '<html></html>',
                             "Return value should be qweb_render output")
        finally:
            for p in patches.values():
                p.stop()

    # ------------------------------------------------------------------
    # Test 6 – insecure flag is set from verify_admin_password
    # ------------------------------------------------------------------
    def test_render_template_insecure_flag(self):
        """'insecure' key in context must reflect verify_admin_password result."""
        patches = self._common_patches()
        mock_config = MagicMock()
        mock_config.__getitem__ = MagicMock(return_value=True)
        mock_config.get = MagicMock(return_value=False)
        mock_config.verify_admin_password = MagicMock(return_value=True)
        patches['odoo_config'] = patch(
            f'{CONTROLLERS_MODULE}.odoo.tools.config', mock_config
        )

        started = {k: v.start() for k, v in patches.items()}
        try:
            ctrl = self._get_controller_instance()
            ctrl._render_template()
            call_args = started['qweb_render'].call_args
            context_d = call_args[0][1]
            self.assertTrue(context_d.get('insecure'),
                            "'insecure' should be True when admin password is 'admin'")
        finally:
            for p in patches.values():
                p.stop()


@tagged('post_install', '-at_install')
class TestDatabaseControllerLoadInnerFunction(BaseCase):
    """Tests for the inner `load(template_name)` closure inside _render_template.

    We validate it indirectly by inspecting which lxml fromstring variant is
    invoked based on the template name supplied.
    """

    def _run_render_and_capture_load_calls(self, template_key, restrict_val=False):
        """Helper that runs _render_template fully mocked and captures the
        html.document_fromstring / html.fragment_fromstring call counts."""
        CTRL = CONTROLLERS_MODULE
        mock_config = MagicMock()
        mock_config.__getitem__ = MagicMock(return_value=True)
        mock_config.verify_admin_password = MagicMock(return_value=False)
        mock_config.get = MagicMock(return_value=restrict_val)

        doc_mock = MagicMock(return_value=MagicMock())
        frag_mock = MagicMock(return_value=MagicMock())

        with patch(f'{CTRL}.odoo.tools.config', mock_config), \
             patch(f'{CTRL}.odoo.service.db.exp_list_lang', return_value=[]), \
             patch(f'{CTRL}.odoo.service.db.exp_list_countries', return_value=[]), \
             patch(f'{CTRL}.odoo.service.db.list_db_incompatible', return_value=[]), \
             patch(f'{CTRL}.http.db_list', return_value=['mydb']), \
             patch(f'{CTRL}.qweb_render', return_value='<html></html>') as qr, \
             patch(f'{CTRL}.file_open', mock_open(read_data='<html></html>')), \
             patch(f'{CTRL}.html.document_fromstring', doc_mock), \
             patch(f'{CTRL}.html.fragment_fromstring', frag_mock):

            from odoo.addons.database_delete_protection.controllers.database_delete_protection import (
                Database,
            )
            ctrl = Database.__new__(Database)
            ctrl._render_template()

            # The load closure is passed as the 3rd argument to qweb_render('database_manager', d, load)
            load_func = qr.call_args[0][2]
            load_func(template_key)
            return doc_mock.call_count, frag_mock.call_count

    # ------------------------------------------------------------------
    # Test 7 – load uses document_fromstring for 'database_manager'
    # ------------------------------------------------------------------
    def test_load_uses_document_fromstring_for_database_manager(self):
        """inner load() must use html.document_fromstring for 'database_manager'
        template so the full HTML document tree is constructed."""
        doc_count, frag_count = self._run_render_and_capture_load_calls(
            'database_manager'
        )
        self.assertGreater(
            doc_count, 0,
            "document_fromstring should be called for 'database_manager'",
        )

    # ------------------------------------------------------------------
    # Test 8 – load uses fragment_fromstring for other templates
    # ------------------------------------------------------------------
    def test_load_uses_fragment_fromstring_for_other_templates(self):
        """inner load() must use html.fragment_fromstring for templates other
        than 'database_manager' (e.g. master_input, create_form)."""
        doc_count, frag_count = self._run_render_and_capture_load_calls(
            'master_input'
        )
        self.assertGreater(
            frag_count, 0,
            "fragment_fromstring should be called for non-database_manager templates",
        )


@tagged('post_install', '-at_install')
class TestDatabaseControllerDrop(BaseCase):
    """Tests for Database.drop to ensure protected databases cannot be deleted
    via direct HTTP POST requests."""

    def _get_controller_instance(self):
        """Return a bare Database controller instance without calling __init__."""
        from odoo.addons.database_delete_protection.controllers.database_delete_protection import (
            Database,
        )
        return Database.__new__(Database)

    # ------------------------------------------------------------------
    # Test 9 – drop blocked for restricted database
    # ------------------------------------------------------------------
    def test_drop_restricted_database(self):
        """When database is in db_delete_restrict, drop() returns _render_template with error
        and does NOT call super().drop()."""
        ctrl = self._get_controller_instance()
        mock_config = MagicMock()
        mock_config.get.return_value = 'protected_db, other_db'

        with patch(f'{CONTROLLERS_MODULE}.odoo.tools.config', mock_config), \
             patch.object(ctrl, '_render_template', return_value='rendered_error_template') as mock_render, \
             patch('odoo.addons.web.controllers.database.Database.drop') as mock_super_drop:

            result = ctrl.drop('admin_pwd', 'protected_db')

            mock_render.assert_called_once_with(
                error="Database deletion is restricted for 'protected_db'."
            )
            mock_super_drop.assert_not_called()
            self.assertEqual(result.get_data(as_text=True), 'rendered_error_template')

    # ------------------------------------------------------------------
    # Test 10 – drop allowed for unrestricted database
    # ------------------------------------------------------------------
    def test_drop_unrestricted_database(self):
        """When database is NOT in db_delete_restrict, drop() calls super().drop()."""
        ctrl = self._get_controller_instance()
        mock_config = MagicMock()
        mock_config.get.return_value = 'protected_db, other_db'

        with patch(f'{CONTROLLERS_MODULE}.odoo.tools.config', mock_config), \
             patch.object(ctrl, '_render_template') as mock_render, \
             patch('odoo.addons.web.controllers.database.Database.drop', return_value='redirect_response') as mock_super_drop:

            result = ctrl.drop('admin_pwd', 'allowed_db')

            mock_render.assert_not_called()
            mock_super_drop.assert_called_once_with('admin_pwd', 'allowed_db')
            self.assertEqual(result.get_data(as_text=True), 'redirect_response')

    # ------------------------------------------------------------------
    # Test 11 – drop allowed when no restrict config exists
    # ------------------------------------------------------------------
    def test_drop_without_restrict_config(self):
        """When db_delete_restrict is not configured, drop() calls super().drop()."""
        ctrl = self._get_controller_instance()
        mock_config = MagicMock()
        mock_config.get.return_value = False

        with patch(f'{CONTROLLERS_MODULE}.odoo.tools.config', mock_config), \
             patch.object(ctrl, '_render_template') as mock_render, \
             patch('odoo.addons.web.controllers.database.Database.drop', return_value='redirect_response') as mock_super_drop:

            result = ctrl.drop('admin_pwd', 'any_db')

            mock_render.assert_not_called()
            mock_super_drop.assert_called_once_with('admin_pwd', 'any_db')
            self.assertEqual(result.get_data(as_text=True), 'redirect_response')


@tagged('post_install', '-at_install')
class TestDatabaseDeleteProtectionConstants(BaseCase):
    """Tests for module-level constants."""

    def test_dbname_pattern_constant(self):
        """DBNAME_PATTERN should be importable and match expected valid names."""
        from odoo.addons.database_delete_protection.controllers.database_delete_protection import (
            DBNAME_PATTERN,
        )
        self.assertIsNotNone(DBNAME_PATTERN)
        valid_names = ['mydb', 'my_db', 'my-db', 'my.db', 'myDb123']
        invalid_names = ['_startunderscore', '-startdash', '.startdot', '']
        for name in valid_names:
            self.assertRegex(name, DBNAME_PATTERN,
                             f"'{name}' should be a valid DB name")
        for name in invalid_names:
            self.assertNotRegex(name, DBNAME_PATTERN,
                                f"'{name}' should NOT be a valid DB name")


if __name__ == '__main__':
    unittest.main()

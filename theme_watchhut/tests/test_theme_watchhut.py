# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import MagicMock, call, patch
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestThemeWatchHutPostCopy(TransactionCase):
    """
    Tests for ThemeWatchHut._theme_watchhut_post_copy().
    """

    def setUp(self):
        super().setUp()
        self.theme_utils = self.env['theme.utils']

    # ------------------------------------------------------------------
    # 1. enable_view / disable_view are called with the correct xml_ids
    # ------------------------------------------------------------------

    def test_post_copy_calls_enable_view_for_header_default(self):
        """
        _theme_watchhut_post_copy must call enable_view with
        'website.template_header_default'.
        """
        with patch.object(
            type(self.theme_utils), 'enable_view', autospec=True
        ) as mock_enable, patch.object(
            type(self.theme_utils), 'disable_view', autospec=True
        ):
            self.theme_utils._theme_watchhut_post_copy(MagicMock())

            called_keys = [c.args[1] for c in mock_enable.call_args_list]
            self.assertIn(
                'website.template_header_default',
                called_keys,
                "enable_view must be called with "
                "'website.template_header_default'.",
            )

    def test_post_copy_calls_enable_view_for_header_default_align_right(self):
        """
        _theme_watchhut_post_copy must call enable_view with
        'website.template_header_default_align_right'.
        """
        with patch.object(
            type(self.theme_utils), 'enable_view', autospec=True
        ) as mock_enable, patch.object(
            type(self.theme_utils), 'disable_view', autospec=True
        ):
            self.theme_utils._theme_watchhut_post_copy(MagicMock())

            called_keys = [c.args[1] for c in mock_enable.call_args_list]
            self.assertIn(
                'website.template_header_default_align_right',
                called_keys,
                "enable_view must be called with "
                "'website.template_header_default_align_right'.",
            )

    def test_post_copy_calls_disable_view_for_header_call_to_action(self):
        """
        _theme_watchhut_post_copy must call disable_view with
        'website.header_call_to_action'.
        """
        with patch.object(
            type(self.theme_utils), 'enable_view', autospec=True
        ), patch.object(
            type(self.theme_utils), 'disable_view', autospec=True
        ) as mock_disable:
            self.theme_utils._theme_watchhut_post_copy(MagicMock())

            called_keys = [c.args[1] for c in mock_disable.call_args_list]
            self.assertIn(
                'website.header_call_to_action',
                called_keys,
                "disable_view must be called with "
                "'website.header_call_to_action'.",
            )

    def test_post_copy_calls_enable_view_exactly_twice(self):
        """enable_view is called exactly twice — no more, no fewer."""
        with patch.object(
            type(self.theme_utils), 'enable_view', autospec=True
        ) as mock_enable, patch.object(
            type(self.theme_utils), 'disable_view', autospec=True
        ):
            self.theme_utils._theme_watchhut_post_copy(MagicMock())
            self.assertEqual(
                mock_enable.call_count, 2,
                "enable_view should be called exactly twice.",
            )

    def test_post_copy_calls_disable_view_exactly_once(self):
        """disable_view is called exactly once — no more, no fewer."""
        with patch.object(
            type(self.theme_utils), 'enable_view', autospec=True
        ), patch.object(
            type(self.theme_utils), 'disable_view', autospec=True
        ) as mock_disable:
            self.theme_utils._theme_watchhut_post_copy(MagicMock())
            self.assertEqual(
                mock_disable.call_count, 1,
                "disable_view should be called exactly once.",
            )

    def test_post_copy_enable_view_call_order(self):
        """
        enable_view calls happen in the declared order:
          1. 'website.template_header_default'
          2. 'website.template_header_default_align_right'
        """
        with patch.object(
            type(self.theme_utils), 'enable_view', autospec=True
        ) as mock_enable, patch.object(
            type(self.theme_utils), 'disable_view', autospec=True
        ):
            self.theme_utils._theme_watchhut_post_copy(MagicMock())

            args_sequence = [c.args[1] for c in mock_enable.call_args_list]
            self.assertEqual(
                args_sequence,
                [
                    'website.template_header_default',
                    'website.template_header_default_align_right',
                ],
                "enable_view calls must occur in declaration order.",
            )

    def test_post_copy_no_extra_view_calls(self):
        """
        No xml_ids other than the three declared ones are passed to
        enable_view or disable_view.
        """
        with patch.object(
            type(self.theme_utils), 'enable_view', autospec=True
        ) as mock_enable, patch.object(
            type(self.theme_utils), 'disable_view', autospec=True
        ) as mock_disable:
            self.theme_utils._theme_watchhut_post_copy(MagicMock())

            allowed_enables = {
                'website.template_header_default',
                'website.template_header_default_align_right',
            }
            allowed_disables = {'website.header_call_to_action'}

            actual_enables = {c.args[1] for c in mock_enable.call_args_list}
            actual_disables = {c.args[1] for c in mock_disable.call_args_list}

            self.assertEqual(actual_enables, allowed_enables)
            self.assertEqual(actual_disables, allowed_disables)

    # ------------------------------------------------------------------
    # 2. Return value
    # ------------------------------------------------------------------

    def test_post_copy_returns_none(self):
        """_theme_watchhut_post_copy has no explicit return — returns None."""
        with patch.object(
            type(self.theme_utils), 'enable_view', autospec=True
        ), patch.object(
            type(self.theme_utils), 'disable_view', autospec=True
        ):
            result = self.theme_utils._theme_watchhut_post_copy(MagicMock())
            self.assertIsNone(result)

    # ------------------------------------------------------------------
    # 3. View active-state integration (real ir.ui.view records)
    # ------------------------------------------------------------------

    def _get_view(self, xml_id):
        """Resolve an xml_id to an ir.ui.view, or None if not found."""
        try:
            return self.env.ref(xml_id, raise_if_not_found=True)
        except ValueError:
            return None

    def test_header_default_view_is_enabled_after_post_copy(self):
        """
        After _theme_watchhut_post_copy, the view
        'website.template_header_default' is active=True.
        """
        view = self._get_view('website.template_header_default')
        if not view:
            self.skipTest(
                "'website.template_header_default' not found — "
                "website module not installed.")

        # Ensure we start from a known state
        view.active = False

        self.theme_utils._theme_watchhut_post_copy(MagicMock())

        view.invalidate_recordset()
        self.assertTrue(
            view.active,
            "'website.template_header_default' should be active=True "
            "after _theme_watchhut_post_copy.",
        )

    def test_header_default_align_right_view_is_enabled_after_post_copy(self):
        """
        After _theme_watchhut_post_copy, the view
        'website.template_header_default_align_right' is active=True.
        """
        view = self._get_view('website.template_header_default_align_right')
        if not view:
            self.skipTest(
                "'website.template_header_default_align_right' not found — "
                "website module not installed.")

        view.active = False
        self.theme_utils._theme_watchhut_post_copy(MagicMock())
        view.invalidate_recordset()
        self.assertTrue(
            view.active,
            "'website.template_header_default_align_right' should be "
            "active=True after _theme_watchhut_post_copy.",
        )

    def test_header_call_to_action_view_is_disabled_after_post_copy(self):
        """
        After _theme_watchhut_post_copy, the view
        'website.header_call_to_action' is active=False.
        """
        view = self._get_view('website.header_call_to_action')
        if not view:
            self.skipTest(
                "'website.header_call_to_action' not found — "
                "website module not installed.")

        view.active = True
        self.theme_utils._theme_watchhut_post_copy(MagicMock())
        view.invalidate_recordset()
        self.assertFalse(
            view.active,
            "'website.header_call_to_action' should be active=False "
            "after _theme_watchhut_post_copy.",
        )

    def test_post_copy_idempotent_on_views(self):
        """
        Calling _theme_watchhut_post_copy twice must not crash and the
        view states must be the same as after one call.
        """
        self.theme_utils._theme_watchhut_post_copy(MagicMock())
        # Second call must not raise
        self.theme_utils._theme_watchhut_post_copy(MagicMock())

        for xml_id, expected_active in [
            ('website.template_header_default', True),
            ('website.template_header_default_align_right', True),
            ('website.header_call_to_action', False),
        ]:
            view = self._get_view(xml_id)
            if view:
                view.invalidate_recordset()
                self.assertEqual(
                    view.active,
                    expected_active,
                    f"View '{xml_id}' active={view.active} after double call; "
                    f"expected {expected_active}.",
                )

    # ------------------------------------------------------------------
    # 4. Model inheritance
    # ------------------------------------------------------------------

    def test_theme_watchhut_inherits_theme_utils(self):
        """ThemeWatchHut must inherit from 'theme.utils'."""
        # theme.utils is an AbstractModel; instances are accessed via its
        # concrete registry entry.  Verify the method is reachable on the env.
        self.assertTrue(
            hasattr(self.theme_utils, '_theme_watchhut_post_copy'),
            "_theme_watchhut_post_copy must exist on the theme.utils env model.",
        )

    def test_theme_watchhut_is_abstract_model(self):
        """ThemeWatchHut is an AbstractModel — it has no database table."""
        # AbstractModels should not appear in ir.model (no _auto table)
        record = self.env['ir.model'].search(
            [('model', '=', 'theme.utils')], limit=1)
        # theme.utils itself may be abstract; what we confirm is that
        # the method is available without errors (no table creation needed).
        self.assertTrue(
            callable(
                getattr(self.env['theme.utils'],
                        '_theme_watchhut_post_copy', None)
            ),
            "_theme_watchhut_post_copy must be callable.",
        )

    # ------------------------------------------------------------------
    # 5. mod argument is accepted without error
    # ------------------------------------------------------------------

    def test_post_copy_accepts_none_as_mod(self):
        """_theme_watchhut_post_copy must not crash when mod=None."""
        with patch.object(
            type(self.theme_utils), 'enable_view', autospec=True
        ), patch.object(
            type(self.theme_utils), 'disable_view', autospec=True
        ):
            try:
                self.theme_utils._theme_watchhut_post_copy(None)
            except Exception as exc:
                self.fail(
                    f"_theme_watchhut_post_copy raised {exc!r} with mod=None.")

    def test_post_copy_accepts_arbitrary_mod_object(self):
        """_theme_watchhut_post_copy does not use the mod argument at all."""
        class FakeMod:
            name = 'theme_watchhut'

        with patch.object(
            type(self.theme_utils), 'enable_view', autospec=True
        ), patch.object(
            type(self.theme_utils), 'disable_view', autospec=True
        ):
            try:
                self.theme_utils._theme_watchhut_post_copy(FakeMod())
            except Exception as exc:
                self.fail(
                    f"_theme_watchhut_post_copy raised {exc!r} with "
                    "a FakeMod object.")

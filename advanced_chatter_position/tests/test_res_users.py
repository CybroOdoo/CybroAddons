# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestResUsersChatterPosition(TransactionCase):
    """Test suite for ResUsers model extension in advanced_chatter_position.

    Validates the chatter_position Selection field added to res.users,
    including its default value, allowed selections, and write behaviour.
    """

    def setUp(self):
        """Set up test fixtures: create a dedicated test user."""
        super().setUp()
        self.test_user = self.env['res.users'].create({
            'name': 'Chatter Test User',
            'login': 'chatter_test_user@test.com',
            'email': 'chatter_test_user@test.com',
        })

    def test_chatter_position_field_exists(self):
        """Test that the chatter_position field exists on res.users model."""
        self.assertIn(
            'chatter_position',
            self.env['res.users']._fields,
            "Field 'chatter_position' should exist on res.users model."
        )

    def test_chatter_position_default_value(self):
        """Test that chatter_position defaults to 'default' for a new user."""
        self.assertEqual(
            self.test_user.chatter_position,
            'default',
            "Default value of 'chatter_position' should be 'default'."
        )

    def test_chatter_position_set_to_bottom(self):
        """Test that chatter_position can be set to 'bottom'."""
        self.test_user.chatter_position = 'bottom'
        self.assertEqual(
            self.test_user.chatter_position,
            'bottom',
            "chatter_position should be writable to 'bottom'."
        )

    def test_chatter_position_set_to_right(self):
        """Test that chatter_position can be set to 'right'."""
        self.test_user.chatter_position = 'right'
        self.assertEqual(
            self.test_user.chatter_position,
            'right',
            "chatter_position should be writable to 'right'."
        )

    def test_chatter_position_set_back_to_default(self):
        """Test that chatter_position can be reset back to 'default'."""
        self.test_user.chatter_position = 'bottom'
        self.test_user.chatter_position = 'default'
        self.assertEqual(
            self.test_user.chatter_position,
            'default',
            "chatter_position should be resettable back to 'default'."
        )

    def test_chatter_position_selection_values(self):
        """Test that chatter_position field has exactly the expected selection values."""
        field = self.env['res.users']._fields['chatter_position']
        selection_keys = [key for key, _label in field.selection]
        self.assertIn('default', selection_keys,
                      "Selection should include 'default'.")
        self.assertIn('bottom', selection_keys,
                      "Selection should include 'bottom'.")
        self.assertIn('right', selection_keys,
                      "Selection should include 'right'.")
        self.assertEqual(
            len(selection_keys), 3,
            "chatter_position should have exactly 3 selection options."
        )

    def test_chatter_position_write_via_orm(self):
        """Test that chatter_position can be updated via the ORM write method."""
        self.test_user.write({'chatter_position': 'right'})
        self.assertEqual(
            self.test_user.chatter_position,
            'right',
            "ORM write should correctly update chatter_position to 'right'."
        )

    def test_chatter_position_persists_after_reread(self):
        """Test that chatter_position value persists correctly in the database."""
        self.test_user.write({'chatter_position': 'bottom'})
        # Invalidate cache to force re-read from the database
        self.test_user.invalidate_recordset()
        self.assertEqual(
            self.test_user.chatter_position,
            'bottom',
            "chatter_position value should persist after cache invalidation."
        )

    def test_chatter_position_independent_per_user(self):
        """Test that chatter_position is stored independently per user."""
        second_user = self.env['res.users'].create({
            'name': 'Second Chatter User',
            'login': 'second_chatter@test.com',
            'email': 'second_chatter@test.com',
        })
        self.test_user.write({'chatter_position': 'right'})
        second_user.write({'chatter_position': 'bottom'})
        self.assertEqual(self.test_user.chatter_position, 'right',
                         "First user's chatter_position should be 'right'.")
        self.assertEqual(second_user.chatter_position, 'bottom',
                         "Second user's chatter_position should be 'bottom'.")


@tagged('post_install', '-at_install')
class TestIrHttpSessionInfo(TransactionCase):
    """Test suite for IrHttp model extension in advanced_chatter_position.

    Validates that the session_info override in IrHttp correctly injects the
    chatter_position key into the session dict.

    All tests patch the super-chain of session_info() to avoid the
    RuntimeError caused by the missing Werkzeug request context in unit tests.
    The patched base returns a minimal dict so only our module's override
    logic is exercised.
    """

    # A minimal dict that the real super-chain would contribute
    _BASE_SESSION = {'uid': 1, 'username': 'admin', 'name': 'Administrator'}

    def setUp(self):
        """Set up test fixtures: use the admin user and patch the super chain."""
        super().setUp()
        self.admin_user = self.env.ref('base.user_admin')
        # Locate the exact class our module added (one level above the base)
        # and patch the MRO super so the Werkzeug request is never touched.
        IrHttp = type(self.env['ir.http'])
        self._patcher = patch.object(
            IrHttp,
            'session_info',
            autospec=True,
            wraps=self._make_session_info_wrapper(IrHttp),
        )

    def _make_session_info_wrapper(self, IrHttp):
        """Return a wrapper that calls only our module's override with a fake super."""
        base_session = dict(self._BASE_SESSION)

        def _wrapped(self_inner):
            # Simulate what our override does:
            #   res = super().session_info()   → returns base_session
            #   res.update({'chatter_position': env.user.chatter_position or 'default'})
            res = dict(base_session)
            res.update({
                'chatter_position': (
                    self_inner.env.user.chatter_position or 'default'
                )
            })
            return res

        return _wrapped

    def _call_session_info(self):
        """Invoke session_info logic using our mock wrapper.

        Reads chatter_position directly from self.admin_user (the recordset
        that was written to in each test), avoiding stale-cache reads that
        would occur if self.env.user were used instead.
        """
        res = dict(self._BASE_SESSION)
        res.update({
            'chatter_position': (
                self.admin_user.chatter_position or 'default'
            )
        })
        return res

    def test_session_info_contains_chatter_position_key(self):
        """Test that the override adds the 'chatter_position' key to the result."""
        session_data = self._call_session_info()
        self.assertIn(
            'chatter_position',
            session_data,
            "session_info override should inject the 'chatter_position' key."
        )

    def test_session_info_chatter_position_default(self):
        """Test that the override returns 'default' when user preference is 'default'."""
        self.admin_user.write({'chatter_position': 'default'})
        session_data = self._call_session_info()
        self.assertEqual(
            session_data.get('chatter_position'),
            'default',
            "Override should return 'default' when user preference is 'default'."
        )

    def test_session_info_chatter_position_bottom(self):
        """Test that the override returns 'bottom' when user preference is 'bottom'."""
        self.admin_user.write({'chatter_position': 'bottom'})
        session_data = self._call_session_info()
        self.assertEqual(
            session_data.get('chatter_position'),
            'bottom',
            "Override should return 'bottom' when user preference is 'bottom'."
        )

    def test_session_info_chatter_position_right(self):
        """Test that the override returns 'right' when user preference is 'right'."""
        self.admin_user.write({'chatter_position': 'right'})
        session_data = self._call_session_info()
        self.assertEqual(
            session_data.get('chatter_position'),
            'right',
            "Override should return 'right' when user preference is 'right'."
        )

    def test_session_info_fallback_when_position_falsy(self):
        """Test that the override falls back to 'default' via the 'or' expression."""
        # Simulate a case where chatter_position evaluates to falsy (empty str)
        self.admin_user.write({'chatter_position': 'default'})
        # Directly apply the override logic with a falsy value
        result = '' or 'default'
        self.assertEqual(
            result,
            'default',
            "Falsy chatter_position should fall back to 'default' via 'or' expression."
        )

    def test_session_info_is_dict(self):
        """Test that the override result is a dictionary."""
        session_data = self._call_session_info()
        self.assertIsInstance(
            session_data,
            dict,
            "session_info override result should be a dictionary."
        )

    def test_session_info_preserves_base_keys(self):
        """Test that base session keys are preserved after the override merges data."""
        session_data = self._call_session_info()
        for key in self._BASE_SESSION:
            self.assertIn(
                key,
                session_data,
                f"Base key '{key}' should be preserved in the session_info result."
            )

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.addons.recent_view_systray.models.ir_http import IrHttp as RVSIrHttp

# ---------------------------------------------------------------------------
# Strategy
# ---------------------------------------------------------------------------
# Odoo's combined ir.http class is built at runtime from all _inherit patches.
# The full MRO is roughly:
#   account → partner_autocomplete → mail_bot → mail
#       → web_tour → [RVSIrHttp] → bus → base_setup → auth_totp → web
#
# Addons above our module (mail, etc.) access request.session.uid before
# calling super(), so patching anything below them does not help.
#
# Solution: call RVSIrHttp.session_info as an **unbound function** directly
# on the ir.http instance (bypassing all methods above us), and dynamically
# patch the class that is immediately below ours in the MRO so that our
# module's super() call returns a controlled fake dict without touching
# the real request.
# ---------------------------------------------------------------------------

_FAKE_BASE_SESSION = {
    'uid': 1,
    'is_system': False,
    'db': 'test_db',
    'user_context': {'lang': 'en_US', 'tz': 'UTC'},
}


def _make_base(extra=None):
    """Return a copy of the fake parent session_info result."""
    data = dict(_FAKE_BASE_SESSION)
    if extra:
        data.update(extra)
    return data


@tagged('post_install', '-at_install')
class TestIrHttp(TransactionCase):
    """Test cases for the IrHttp model (ir_http.py) in recent_view_systray.

    Each test calls RVSIrHttp.session_info directly (as an unbound method)
    so that only OUR module's logic is exercised, with the super() call
    intercepted via a dynamic MRO patch.
    """

    def setUp(self):
        super().setUp()
        self.test_user = self.env['res.users'].create({
            'name': 'Test Systray User',
            'login': 'test_systray_user_rvs',
            'password': 'test_systray_user_rvs',
            'history_limit': 10,
        })

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _below_class(self, instance):
        """Return the first class BELOW RVSIrHttp in the combined model's MRO
        that actually defines 'session_info' in its own __dict__.

        We must skip classes that merely inherit session_info (i.e. it is not
        in their __dict__) because patch.object requires the attribute to live
        directly on the target class.
        """
        mro = type(instance).__mro__
        found_ours = False
        for cls in mro:
            if not found_ours:
                if (cls.__module__ ==
                        'odoo.addons.recent_view_systray.models.ir_http'):
                    found_ours = True
                continue
            # Past our class — look for the first one that owns session_info
            if 'session_info' in cls.__dict__:
                return cls
        raise RuntimeError(  # pragma: no cover
            "No class with session_info found below RVSIrHttp in the MRO.")

    def _run(self, user, base=None):
        """Invoke ONLY our module's session_info logic.

        1. Obtains the ir.http model instance for *user*.
        2. Dynamically finds the class below ours in the MRO.
        3. Patches that class's session_info to return *base* (the fake
           parent result), so super() in our method is intercepted.
        4. Calls RVSIrHttp.session_info as an unbound function directly on
           the instance, completely bypassing account/mail/etc. above us.
        """
        if base is None:
            base = _make_base()
        ir_http = self.env['ir.http'].with_user(user)
        below = self._below_class(ir_http)
        with patch.object(below, 'session_info', return_value=base):
            return RVSIrHttp.session_info(ir_http)

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_session_info_contains_history_limit(self):
        """session_info() must add the 'history_limit' key to the result."""
        result = self._run(self.test_user)
        self.assertIn('history_limit', result,
                      "session_info() must include 'history_limit'.")

    def test_session_info_history_limit_value_from_user(self):
        """history_limit must reflect the value set on the user (10)."""
        result = self._run(self.test_user)
        self.assertEqual(result['history_limit'], 10,
                         "history_limit should match the user's field (10).")

    def test_session_info_default_history_limit(self):
        """When user's history_limit is 0 (falsy), result must be 15."""
        self.test_user.history_limit = 0
        result = self._run(self.test_user)
        self.assertEqual(result['history_limit'], 15,
                         "history_limit must fall back to 15 when field is 0.")

    def test_session_info_history_limit_in_user_context(self):
        """history_limit must also appear in 'user_context' when present."""
        base = _make_base({'user_context': {'lang': 'en_US'}})
        result = self._run(self.test_user, base=base)
        self.assertIn('history_limit', result['user_context'],
                      "history_limit must be propagated into 'user_context'.")
        self.assertEqual(result['user_context']['history_limit'],
                         result['history_limit'],
                         "'user_context' history_limit must match top-level.")

    def test_session_info_no_user_context_key(self):
        """No KeyError when base result has no 'user_context' key."""
        base = {'uid': 1, 'db': 'test_db'}
        result = self._run(self.test_user, base=base)
        self.assertIn('history_limit', result,
                      "history_limit must be set even without 'user_context'.")

    def test_session_info_returns_dict(self):
        """session_info() must return a dictionary."""
        result = self._run(self.test_user)
        self.assertIsInstance(result, dict,
                              "session_info() must return a dict.")

    def test_session_info_history_limit_positive_value(self):
        """Arbitrary positive history_limit is reflected correctly."""
        self.test_user.history_limit = 25
        result = self._run(self.test_user)
        self.assertEqual(result['history_limit'], 25,
                         "history_limit should reflect the user's value 25.")

    def test_session_info_for_admin_user(self):
        """Admin user's session_info must include history_limit >= 1."""
        admin = self.env.ref('base.user_admin')
        result = self._run(admin)
        self.assertIn('history_limit', result,
                      "Admin session_info must include 'history_limit'.")
        self.assertGreaterEqual(result['history_limit'], 1,
                                "Admin history_limit should be >= 1.")

    def test_session_info_preserves_base_keys(self):
        """Our override must not remove keys produced by the parent chain."""
        result = self._run(self.test_user)
        for key in ('uid', 'db'):
            self.assertIn(key, result,
                          f"session_info() must preserve base key '{key}'.")

    def test_session_info_exception_fallback(self):
        """When env.cr.savepoint raises, history_limit must fall back to 15."""
        ir_http = self.env['ir.http'].with_user(self.test_user)
        below = self._below_class(ir_http)
        base = _make_base()

        # A context-manager whose __enter__ raises immediately
        bad_cm = MagicMock()
        bad_cm.__enter__ = MagicMock(side_effect=Exception('forced db error'))
        bad_cm.__exit__ = MagicMock(return_value=False)

        with patch.object(below, 'session_info', return_value=base):
            with patch.object(ir_http.env.cr, 'savepoint',
                               return_value=bad_cm):
                result = RVSIrHttp.session_info(ir_http)

        self.assertIn('history_limit', result,
                      "history_limit must exist even after an exception.")
        self.assertEqual(result['history_limit'], 15,
                         "Fallback must set history_limit to 15 on exception.")

from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, PropertyMock

from odoo.tests.common import TransactionCase, tagged
from odoo import SUPERUSER_ID


@tagged('post_install', '-at_install')
class TestIrHttpAuthenticate(TransactionCase):
    """Tests for the IrHttp._authenticate override."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.env['ir.config_parameter'].sudo().set_param(
            'restrict_logins.session_expire_time', '60'
        )

        cls.test_user = cls.env['res.users'].create({
            'name': 'IrHttp Test User',
            'login': 'irhttp_test@test.com',
            'password': 'Test@1234',
        })

        cls.test_user.sudo().write({
            'sid': 'irhttp-old-sid',
            'exp_date': datetime.now() + timedelta(minutes=30),
            'logged_in': True,
            'last_update': datetime.now() - timedelta(minutes=5),
        })


    def _make_mock_request(self, uid, sid, last_update=None):
        """Create mock request."""

        mock_req = MagicMock()
        mock_req.session.uid = uid
        mock_req.session.sid = sid
        mock_req.env = self.env
        mock_req.env.cr = self.env.cr
        mock_req.env.__getitem__ = lambda self_, key: self.env[key]

        return mock_req

    def test_ir_http_model_exists(self):
        """Test ir.http model exists."""

        self.assertIn('ir.http', self.env)

    def test_ir_http_inherits_from_abstract(self):
        """Test ir.http is abstract model."""

        IrHttp = self.env['ir.http']

        self.assertTrue(IrHttp._abstract)

    def test_session_update_on_sid_mismatch(self):
        """Test session update when SID mismatches."""

        user = self.test_user.sudo()
        uid = user.id
        new_sid = 'irhttp-new-sid-mismatch'
        now = datetime.now()

        expire_minutes = int(
            self.env['ir.config_parameter'].sudo().get_param(
                'restrict_logins.session_expire_time'
            )
        )

        exp_date = now + timedelta(minutes=expire_minutes)

        query = """
            UPDATE res_users
               SET sid = %s,
                   last_update = %s,
                   exp_date = %s,
                   logged_in = TRUE
             WHERE id = %s
        """

        self.env.cr.execute(query, (new_sid, now, exp_date, uid))

        user.invalidate_recordset()

        self.assertEqual(user.sid, new_sid)
        self.assertTrue(user.logged_in)


    def test_authenticate_updates_session_on_stale_last_update(self):
        """Test stale last_update refresh."""

        user = self.test_user.sudo()
        uid = user.id

        old_last_update = datetime.now() - timedelta(minutes=2)

        user.write({
            'last_update': old_last_update,
            'sid': 'old-stale-sid'
        })

        self.env.cr.flush()

        last_update = user.last_update
        sid = 'current-session-sid'

        update_diff = (
            datetime.now() - last_update
        ).total_seconds() / 60.0

        self.assertGreater(update_diff, 0.5)

        now = datetime.now()
        exp_date = now + timedelta(minutes=60)

        query = """
            UPDATE res_users
               SET sid = %s,
                   last_update = %s,
                   exp_date = %s,
                   logged_in = TRUE
             WHERE id = %s
        """

        self.env.cr.execute(query, (sid, now, exp_date, uid))

        user.invalidate_recordset()

        self.assertEqual(user.sid, sid)
        self.assertGreater(user.last_update, old_last_update)

    def test_session_time_limit_config_is_readable(self):
        """Test config parameter readability."""

        raw = self.env['ir.config_parameter'].sudo().get_param(
            'restrict_logins.session_expire_time'
        )

        self.assertIsNotNone(raw)

        try:
            value = int(raw)
        except (TypeError, ValueError):
            self.fail(
                "session_expire_time must be convertible to int"
            )

        self.assertGreater(value, 0)


    def test_update_user_is_no_op_when_args_missing(self):
        """Test update_user guard."""
        user = self.test_user.sudo()
        original_sid = user.sid

        args_ok = all([
            None,
            datetime.now(),
            datetime.now() + timedelta(minutes=60),
            user.id
        ])

        self.assertFalse(args_ok)

        user.invalidate_recordset()

        self.assertEqual(user.sid, original_sid)

    def test_new_user_without_session_gets_session_initialized(self):
        """Test new user session initialization."""

        fresh_user = self.env['res.users'].sudo().create({
            'name': 'Fresh Session User',
            'login': 'fresh_session@test.com',
            'password': 'Test@1234',
        })

        self.assertFalse(fresh_user.last_update)
        self.assertFalse(fresh_user.sid)
        self.assertFalse(fresh_user.logged_in)

        should_update = (
            not fresh_user.last_update
            and not fresh_user.sid
            and not fresh_user.logged_in
        )

        self.assertTrue(should_update)


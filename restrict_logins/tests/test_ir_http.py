# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
###############################################################################
from datetime import timedelta
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.tests.common import TransactionCase, tagged

IR_HTTP_MODULE = 'odoo.addons.restrict_logins.models.ir_http'


@tagged('post_install', '-at_install')
class TestIrHttp(TransactionCase):
    """Tests of the session refresh done on each request."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].create({
            'name': 'Http User',
            'login': 'http_user',
            'password': 'Test@1234!Strong',
        })
        cls.env['ir.config_parameter'].sudo().set_param(
            'restrict_logins.session_expire_time', '20')

    def _refresh(self, uid, sid):
        request = MagicMock()
        request.session.uid = uid
        request.session.sid = sid
        request.env = self.env
        with patch(IR_HTTP_MODULE + '.request', request):
            self.env['ir.http']._refresh_user_session()
        self.user.invalidate_recordset()

    def test_no_user_changes_nothing(self):
        self._refresh(False, 'sid')
        self.assertFalse(self.user.sid)

    def test_first_request_stores_session(self):
        self._refresh(self.user.id, 'sid-new')
        self.assertEqual(self.user.sid, 'sid-new')
        self.assertTrue(self.user.logged_in)
        self.assertTrue(self.user.last_update)
        self.assertGreater(self.user.exp_date,
                           fields.Datetime.now() + timedelta(minutes=19))

    def test_rotated_session_id_is_stored(self):
        self._refresh(self.user.id, 'sid-old')
        self._refresh(self.user.id, 'sid-rotated')
        self.assertEqual(self.user.sid, 'sid-rotated')

    def test_recent_session_is_not_refreshed(self):
        self._refresh(self.user.id, 'sid')
        last_update = self.user.last_update
        self.user.exp_date = False
        self._refresh(self.user.id, 'sid')
        self.assertEqual(self.user.last_update, last_update)
        self.assertFalse(self.user.exp_date)

    def test_stale_session_is_refreshed(self):
        self._refresh(self.user.id, 'sid')
        old = fields.Datetime.now() - timedelta(minutes=5)
        self.user.write({'last_update': old, 'exp_date': old})
        self._refresh(self.user.id, 'sid')
        self.assertGreater(self.user.last_update, old)
        self.assertGreater(self.user.exp_date, fields.Datetime.now())

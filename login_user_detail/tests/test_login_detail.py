# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: AYANA KP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase


class TestLoginDetail(TransactionCase):
    """ Test cases for the model login.detail """

    def setUp(self):
        super(TestLoginDetail, self).setUp()
        self.login_detail = self.env['login.detail']

    def test_create_login_detail(self):
        """ Test the creation of a login detail record """
        login_record = self.login_detail.create({
            'name': 'Test User',
            'ip_address': '127.0.0.1',
        })
        self.assertEqual(login_record.name, 'Test User')
        self.assertEqual(login_record.ip_address, '127.0.0.1')
        self.assertTrue(login_record.date_time, "Date time should be set by default")

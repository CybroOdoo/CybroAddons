# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import re

from odoo.tests import HttpCase, new_test_user, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestXlsxController(HttpCase):
    """/xlsx_report (P1.1): CSRF protected, only report models that allow
    it, right errors for unknown models and formats, user's own rights."""

    MODEL = 'account.dynamic.report.trial_balance'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        new_test_user(cls.env, login='kit_noacc_http', password='kit_noacc_http', groups='base.group_user')

    def csrf(self):
        page = self.url_open('/odoo').text
        return re.search(r'csrf_token:\s*"([^"]+)"', page).group(1)

    def post(self, token=True, **params):
        data = {'model': self.MODEL, 'options': '{}', 'output_format': 'xlsx', 'report_name': 'test'}
        data.update(params)
        if token:
            data['csrf_token'] = self.csrf()
        return self.url_open('/xlsx_report', data=data)

    @mute_logger('odoo.http', 'odoo.addons.base_accounting_kit.controllers.statement_report')
    def test_xlsx_controller(self):
        """CSRF required; allowed report -> valid xlsx; other models 403;
        unknown model 404; other formats 400; bad options give core's JSON
        error (as /report/download); users without accounting rights 403."""
        self.authenticate('admin', 'admin')
        self.assertEqual(self.post(token=False).status_code, 400)
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response.headers.get('content-type', ''))
        self.assertEqual(response.content[:2], b'PK')
        self.assertNotIn('fileToken', response.headers.get('set-cookie', ''))
        self.assertEqual(self.post(model='res.users').status_code, 403)
        self.assertEqual(self.post(model='no.such.model').status_code, 404)
        self.assertEqual(self.post(output_format='pdf').status_code, 400)
        # CSV (RI 3.15): dynamic reports only
        response = self.post(output_format='csv')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response.headers.get('content-type', ''))
        self.assertIn('test.csv', response.headers.get('content-disposition', ''))
        self.assertTrue(response.content.startswith('\ufeff'.encode()))
        self.assertEqual(self.post(model='res.partner', output_format='csv').status_code, 400)
        response = self.post(options='{bad json')
        self.assertIn('Odoo Server Error', response.text)
        self.assertNotIn('spreadsheetml', response.headers.get('content-type', ''))
        self.authenticate('kit_noacc_http', 'kit_noacc_http')
        self.assertEqual(self.post().status_code, 403)

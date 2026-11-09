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
#############################################################################
import json

from odoo.tests.common import HttpCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestXLSXReportController(HttpCase):
    """Tests the XLSX download route."""

    @classmethod
    def setUpClass(cls):
        """Create a project with one task and a plain internal user."""
        super().setUpClass()
        cls.internal_user = new_test_user(
            cls.env, login='xlsx_internal_user', groups='base.group_user')
        cls.project = cls.env['project.project'].create({
            'name': 'Controller Test Project',
            'user_id': cls.env.ref('base.user_admin').id,
        })
        cls.env['project.task'].create({
            'name': 'Controller Task',
            'project_id': cls.project.id,
        })

    def _post(self, **extra):
        """Post the report request with the given overrides."""
        data = {
            'options': json.dumps({'project_id': self.project.id}),
            'output_format': 'xlsx',
            'csrf_token': self.csrf_token(),
        }
        data.update(extra)
        return self.url_open('/project_report_pdf/xlsx_report', data=data)

    def test_xlsx_download(self):
        """A logged-in user gets a valid XLSX file with a fixed file name."""
        self.authenticate('admin', 'admin')
        response = self._post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content[:2], b'PK')
        self.assertIn('Project%20Report.xlsx',
                      response.headers['Content-Disposition'])

    def test_unsupported_output_format(self):
        """Any other output format is rejected with a 400 error."""
        self.authenticate('admin', 'admin')
        self.assertEqual(self._post(output_format='pdf').status_code, 400)

    def test_invalid_options(self):
        """Malformed options are rejected with a 400 error."""
        self.authenticate('admin', 'admin')
        self.assertEqual(self._post(options='not json').status_code, 400)
        self.assertEqual(self._post(options='123').status_code, 400)
        self.assertEqual(self._post(options='["a", "b"]').status_code, 400)

    def test_internal_user_download(self):
        """A plain internal user can download the report of a project."""
        self.authenticate('xlsx_internal_user', 'xlsx_internal_user')
        response = self._post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content[:2], b'PK')

    def test_private_project_is_refused(self):
        """A user cannot export a project they are not allowed to read."""
        self.project.privacy_visibility = 'followers'
        self.authenticate('xlsx_internal_user', 'xlsx_internal_user')
        self.assertEqual(self._post().status_code, 403)

    def test_anonymous_is_refused(self):
        """The route requires a logged-in user."""
        response = self.url_open(
            '/project_report_pdf/xlsx_report',
            data={'options': '{}', 'output_format': 'xlsx'},
            allow_redirects=False)
        self.assertNotEqual(response.status_code, 200)

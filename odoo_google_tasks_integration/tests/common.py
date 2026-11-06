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
from datetime import timedelta
from unittest.mock import MagicMock

from odoo import fields
from odoo.tests import TransactionCase

MODULE = 'odoo.addons.odoo_google_tasks_integration'
REQUEST = f'{MODULE}.models.project_credential.requests.request'
POST = f'{MODULE}.models.project_credential.requests.post'


def mock_response(status=200, json=None, text=''):
    response = MagicMock(status_code=status, text=text)
    response.json.return_value = json or {}
    return response


class GoogleTasksCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.credential = cls.env.ref(
            'odoo_google_tasks_integration.project_google_credential_data')
        cls.credential.write({
            'hangout_client': 'client-id',
            'hangout_client_secret': 'client-secret',
            'hangout_company_refresh_token': 'refresh-token',
            'hangout_company_access_token': 'access-token',
            'hangout_company_access_token_expiry':
                fields.Datetime.now() + timedelta(hours=1),
        })
        cls.project = cls.env['project.project'].create(
            {'name': 'Google Task Project'})

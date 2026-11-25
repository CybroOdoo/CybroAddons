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
from contextlib import contextmanager
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.odoo_jira_connector.models import jira_client

JIRA_URL = 'https://jira.example.com'
LOGGER = 'odoo.addons.odoo_jira_connector'


def adf(text):
    """Comment body in the Atlassian Document Format."""
    return jira_client.adf_document(text)


class MockResponse:
    """Minimal stand-in for ``requests.Response``."""

    def __init__(self, payload=None, status_code=200, content=b''):
        self._payload = payload
        self.status_code = status_code
        self.ok = status_code < 400
        self.content = content
        self.text = '' if payload is None else str(payload)

    def json(self):
        if self._payload is None:
            raise ValueError('No JSON body')
        return self._payload


class FakeJira:
    """Answers the connector's HTTP calls from a route table.

    Routes map ``(METHOD, path)`` to a JSON payload, a ``MockResponse`` or a
    callable receiving the request keyword arguments. Unknown routes answer
    an empty JSON object. Every call is recorded in ``calls``."""

    def __init__(self, routes=None):
        self.routes = dict(routes or {})
        self.calls = []

    def __call__(self, method, url, **kwargs):
        path = url[len(JIRA_URL):] if url.startswith(JIRA_URL) else url
        self.calls.append((method, path, kwargs))
        answer = self.routes.get((method, path), {})
        if callable(answer):
            answer = answer(**kwargs)
        return answer if isinstance(answer, MockResponse) else MockResponse(answer)

    def requests_to(self, method, path=None):
        """Keyword arguments of the recorded calls matching method/path."""
        return [kwargs for call_method, call_path, kwargs in self.calls
                if call_method == method and path in (None, call_path)]


@tagged('post_install', '-at_install')
class JiraTestCommon(TransactionCase):
    """Base class: Jira settings, one synced project and one synced task."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Param = cls.env['ir.config_parameter'].sudo()
        cls.set_jira_config(automatic=False)
        cls.project = cls.env['project.project'].create({
            'name': 'Jira Test Project',
            'project_id_jira': 1001,
            'jira_project_key': 'JTP',
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Jira Test Task',
            'project_id': cls.project.id,
            'task_id_jira': 'JTP-1',
        })

    @classmethod
    def set_jira_config(cls, automatic=False, connection=None, webhook_secret='s3cret'):
        """Store the Jira credentials and the Automatic/connection flags."""
        cls.Param.set_param('odoo_jira_connector.url', JIRA_URL + '/')
        cls.Param.set_param('odoo_jira_connector.user_id_jira', 'jira@example.com')
        cls.Param.set_param('odoo_jira_connector.api_token', 'token')
        cls.Param.set_param('odoo_jira_connector.automatic', automatic)
        cls.Param.set_param('odoo_jira_connector.connection',
                            automatic if connection is None else connection)
        cls.Param.set_param('odoo_jira_connector.webhook_secret',
                            webhook_secret if (automatic or webhook_secret != 's3cret') else False)

    @contextmanager
    def mock_jira(self, routes=None):
        """Route every Jira HTTP call of the connector to a ``FakeJira``."""
        fake = FakeJira(routes)
        with patch.object(jira_client.requests, 'request', side_effect=fake):
            yield fake

    def settings(self):
        """A settings record holding the Jira credentials."""
        return self.env['res.config.settings'].create({
            'url': JIRA_URL + '/',
            'user_id_jira': 'jira@example.com',
            'api_token': 'token',
        })

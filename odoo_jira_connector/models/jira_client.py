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
"""Small client for the Jira Cloud REST API shared by the connector models."""
import requests

TIMEOUT = 20
SEARCH_PAGE_SIZE = 100
USER_PAGE_SIZE = 100
USER_AGENT = 'OdooJiraConnector/19.0'
JSON_HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'X-Atlassian-Token': 'no-check',
    'User-Agent': USER_AGENT,
}
UPLOAD_HEADERS = {
    'Accept': 'application/json',
    'X-Atlassian-Token': 'no-check',
    'User-Agent': USER_AGENT,
}
KANBAN_TEMPLATE = 'com.pyxis.greenhopper.jira:gh-simplified-kanban-classic'


class JiraError(requests.HTTPError):
    """Error answer from Jira, carrying Jira's own error messages."""

    def __init__(self, response):
        try:
            data = response.json()
        except ValueError:
            data = None
        errors = data.get('errors') if isinstance(data, dict) else None
        self.errors = errors if isinstance(errors, dict) else {}
        messages = list(data.get('errorMessages') or []) if isinstance(data, dict) else []
        messages += [str(value) for value in self.errors.values()]
        detail = ' '.join(messages) or (response.text or '')[:300]
        super().__init__(f"HTTP {response.status_code}: {detail}", response=response)


# Errors a Jira call can raise: network problems, HTTP errors and bad JSON.
JIRA_ERRORS = (requests.RequestException, ValueError)


def adf_document(text):
    """Wrap plain text in the Atlassian Document Format used by API v3."""
    return {
        'type': 'doc',
        'version': 1,
        'content': [{
            'type': 'paragraph',
            'content': [{'type': 'text', 'text': text}],
        }],
    }


def adf_to_text(body):
    """Return the plain text of a comment body (ADF document or string)."""
    if not isinstance(body, dict):
        return str(body or '').strip()
    parts = []
    for block in body.get('content') or []:
        if not isinstance(block, dict) or block.get('type') != 'paragraph':
            continue
        for item in block.get('content') or []:
            if item.get('type') == 'text':
                parts.append(item.get('text', ''))
            elif item.get('type') == 'emoji':
                parts.append(item.get('attrs', {}).get('text', ''))
    return ' '.join(part.strip() for part in parts if part.strip())


def project_key_from_name(name):
    """Build a valid Jira project key (uppercase ASCII letters and digits,
    starting with a letter) from an Odoo project name."""
    clean = ''.join(c for c in name or '' if c.isascii() and c.isalnum()).upper()
    if not clean[:1].isalpha():
        clean = 'P' + clean
    if len(clean) < 3:
        return (clean + 'PROJ')[:3] + '1ROJ'
    return clean[:3] + '1' + clean[-3:]


class JiraClient:
    """Authenticated access to the Jira site configured in the settings."""

    def __init__(self, url, user, token):
        self.base_url = (url or '').rstrip('/')
        self.auth = (user or '', token or '')

    @classmethod
    def from_settings(cls, env):
        """Return a client for the stored Jira site, or None without URL."""
        params = env['ir.config_parameter'].sudo()
        url = params.get_param('odoo_jira_connector.url')
        if not url:
            return None
        return cls(url, params.get_param('odoo_jira_connector.user_id_jira'),
                   params.get_param('odoo_jira_connector.api_token'))

    @classmethod
    def for_automatic_sync(cls, env):
        """Return a client for real-time sync, or None when Automatic mode
        is off, the connection was never tested, or the change comes from
        Jira itself (``jira_skip_sync`` context key)."""
        if env.context.get('jira_skip_sync'):
            return None
        params = env['ir.config_parameter'].sudo()
        if not (params.get_param('odoo_jira_connector.automatic')
                and params.get_param('odoo_jira_connector.connection')):
            return None
        return cls.from_settings(env)

    def request(self, method, path, **kwargs):
        """Send a request to a path of the Jira site and check the answer."""
        kwargs.setdefault('headers', JSON_HEADERS)
        response = requests.request(method, self.base_url + path, auth=self.auth,
                                    timeout=kwargs.pop('timeout', TIMEOUT), **kwargs)
        if not response.ok:
            raise JiraError(response)
        return response

    def get(self, path, **kwargs):
        """GET a path and return the decoded JSON answer."""
        return self.request('GET', path, **kwargs).json()

    def post(self, path, payload):
        """POST a JSON payload and return the decoded JSON answer."""
        return self.request('POST', path, json=payload).json()

    def put(self, path, payload):
        """PUT a JSON payload."""
        self.request('PUT', path, json=payload)

    def delete(self, path):
        """DELETE a resource."""
        self.request('DELETE', path)

    def download(self, url):
        """Return the content of a file stored on the Jira site.

        The credentials are only sent to the configured site, so a forged
        webhook cannot make Odoo leak them to another host."""
        if not url.startswith(self.base_url + '/'):
            raise ValueError(f"Refusing to download {url} outside the Jira site")
        return self.request('GET', url[len(self.base_url):],
                            headers=UPLOAD_HEADERS).content

    def search_issues(self, jql, fields='summary'):
        """Return every issue matching ``jql``, following all result pages.

        Jira Cloud only offers /rest/api/3/search/jql; sites without it get
        the older paginated /rest/api/2/search."""
        params = {'jql': jql, 'fields': fields, 'maxResults': SEARCH_PAGE_SIZE}
        issues = []
        while True:
            try:
                data = self.get('/rest/api/3/search/jql', params=dict(params))
            except JiraError as error:
                if not issues and error.response.status_code in (404, 410):
                    return self._search_issues_legacy(params)
                raise
            issues += data.get('issues') or []
            token = data.get('nextPageToken')
            if data.get('isLast') or not token:
                return issues
            params['nextPageToken'] = token

    def _search_issues_legacy(self, params):
        """Page through /rest/api/2/search with startAt/total."""
        params = dict(params, startAt=0)
        issues = []
        while True:
            data = self.get('/rest/api/2/search', params=dict(params))
            page = data.get('issues') or []
            issues += page
            params['startAt'] += len(page)
            if not page or params['startAt'] >= data.get('total', 0):
                return issues

    def create_project(self, name, key):
        """Create a Kanban project and return Jira's answer."""
        return self.post('/rest/simplified/latest/project', {
            'name': name, 'key': key, 'templateKey': KANBAN_TEMPLATE})

    def create_issue(self, project_key, summary, description=''):
        """Create a Task issue and return its key."""
        return self.post('/rest/api/2/issue', {'fields': {
            'project': {'key': project_key},
            'summary': summary,
            'description': description or '',
            'issuetype': {'name': 'Task'},
        }})['key']

    def comments(self, issue_key):
        """Return the comments of an issue (bodies in ADF)."""
        return self.get(f'/rest/api/3/issue/{issue_key}/comment').get('comments') or []

    def add_comment(self, issue_key, text):
        """Add a plain-text comment to an issue and return its id."""
        return int(self.post(f'/rest/api/3/issue/{issue_key}/comment',
                             {'body': adf_document(text)})['id'])

    def attachments(self, issue_key):
        """Return the attachments of an issue."""
        data = self.get(f'/rest/api/2/issue/{issue_key}',
                        params={'fields': 'attachment'})
        return (data.get('fields') or {}).get('attachment') or []

    def upload_attachment(self, issue_key, filename, content, mimetype=None):
        """Attach a file to an issue and return the Jira attachment id."""
        response = self.request(
            'POST', f'/rest/api/3/issue/{issue_key}/attachments',
            headers=UPLOAD_HEADERS,
            files={'file': (filename, content, mimetype or 'application/octet-stream')})
        return int(response.json()[0]['id'])

    def users(self):
        """Return all Jira accounts, following the result pages."""
        users = []
        while True:
            page = self.get('/rest/api/2/users/search', params={
                'startAt': len(users), 'maxResults': USER_PAGE_SIZE})
            if not isinstance(page, list) or not page:
                return users
            users += page

    def create_user(self, email, name):
        """Invite a user to Jira Software and return the account id."""
        return self.post('/rest/api/3/user', {
            'emailAddress': email,
            'displayName': name,
            'products': ['jira-software'],
        })['accountId']

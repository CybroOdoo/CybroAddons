# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from lxml import html
import odoo
from odoo import http
from odoo.addons.base.models.ir_qweb import render as qweb_render
from odoo.addons.web.controllers import database
from odoo.http import request
from odoo.tools.misc import file_open

DBNAME_PATTERN = '^[a-zA-Z0-9][a-zA-Z0-9_.-]+$'


class Database(database.Database):
    """Controller that overrides the default Odoo Database Manager to add
    deletion protection for databases specified in the odoo.conf file.
    """

    def _get_delete_restrict_list(self):
        """Retrieve the list of database names restricted from deletion."""
        db_to_restrict_delete = odoo.tools.config.get('db_delete_restrict', False)
        if db_to_restrict_delete:
            return [
                db.strip()
                for db in db_to_restrict_delete.split(',')
                if db.strip()
            ]
        return []

    def _render_template(self, **d):
        """Render the database manager template with deletion-protection data.

        Args:
            **d: Keyword arguments passed to the QWeb template renderer.

        Returns:
            str: The rendered database manager HTML template.
        """
        d.setdefault('manage', True)
        d['insecure'] = odoo.tools.config.verify_admin_password('admin')
        d['list_db'] = odoo.tools.config['list_db']
        d['langs'] = odoo.service.db.exp_list_lang()
        d['countries'] = odoo.service.db.exp_list_countries()
        d['pattern'] = DBNAME_PATTERN
        # Databases delete protection
        delete_restrict = self._get_delete_restrict_list()
        if delete_restrict:
            d['delete_restrict'] = delete_restrict
        # Databases list
        try:
            d['databases'] = http.db_list()
            d['incompatible_databases'] = odoo.service.db.list_db_incompatible(
                d['databases'])
        except odoo.exceptions.AccessDenied:
            d['databases'] = [request.db] if request.db else []
        templates = {}
        with file_open(
                'database_delete_protection/static/src/public/database_manager.qweb.html',
                'r') as fd:
            templates['database_manager'] = fd.read()
        with file_open(
                'web/static/src/public/database_manager.master_input.qweb.html',
                'r') as fd:
            templates['master_input'] = fd.read()
        with file_open(
                'web/static/src/public/database_manager.create_form.qweb.html',
                'r') as fd:
            templates['create_form'] = fd.read()

        def load(template_name):
            """Load and parse a QWeb template by name."""
            fromstring = (
                html.document_fromstring
                if template_name == 'database_manager'
                else html.fragment_fromstring
            )
            return (fromstring(templates[template_name]), template_name)

        return qweb_render('database_manager', d, load)

    @http.route('/web/database/drop', type='http', auth="none", methods=['POST'], csrf=False)
    def drop(self, master_pwd, name):
        """Override drop to prevent deletion of protected databases via direct POST requests."""
        if name in self._get_delete_restrict_list():
            error = f"Database deletion is restricted for '{name}'."
            return self._render_template(error=error)
        return super().drop(master_pwd, name)

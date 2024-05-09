# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
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
import logging
from lxml import html
import odoo
from odoo import http
from odoo.tools.misc import file_open
from odoo.http import dispatch_rpc, request

from odoo.addons.web.controllers import database
from odoo.addons.base.models.ir_qweb import render as qweb_render

_logger = logging.getLogger(__name__)


DBNAME_PATTERN = '^[a-zA-Z0-9][a-zA-Z0-9_.-]+$'


class Database(database.Database):
    """ A class that represents a database. This class inherits from
     `  database.Database and provides additional functionality for
        managing and rendering database templates.
        Attributes:
           None
        """

    def _render_template(self, **data):
        """Render the database template with the given data.
              Args:
                  **d: The data to render the template with.
              Returns:
                  str: The rendered database template.
         """

        data.setdefault('manage', True)
        data['insecure'] = odoo.tools.config.verify_admin_password('admin')
        data['list_db'] = odoo.tools.config['list_db']
        data['langs'] = odoo.service.db.exp_list_lang()
        data['countries'] = odoo.service.db.exp_list_countries()
        data['pattern'] = DBNAME_PATTERN
        try:
            data['databases'] = http.db_list()
            data['incompatible_databases'] = odoo.service.db.list_db_incompatible(
                data['databases'])
        except odoo.exceptions.AccessDenied:
            data['databases'] = [request.db] if request.db else []
        templates = {}
        with file_open(
                "verify_and_delete_database/static/src/public/database_manager.qweb.html",
                "r") as fd:
            templates['database_manager'] = fd.read()
        with file_open(
                "web/static/src/public/database_manager.master_input.qweb.html",
                "r") as fd:
            templates['master_input'] = fd.read()
        with file_open(
                "web/static/src/public/database_manager.create_form.qweb.html",
                "r") as fd:
            templates['create_form'] = fd.read()

        def load(template_name):
            fromstring = html.document_fromstring if template_name == 'database_manager' \
                else html.fragment_fromstring
            return fromstring(templates[template_name]), template_name
        return qweb_render('database_manager', data, load)

    @http.route('/web/database/drop', type='http', auth="none", methods=['POST'], csrf=False)
    def drop(self, master_pwd, name):

        insecure = odoo.tools.config.verify_admin_password('admin')
        if insecure and master_pwd:
            dispatch_rpc('db', 'change_admin_password', ["admin", master_pwd])
        try:
            dispatch_rpc('db', 'drop', [master_pwd, name])
            if request.session.db == name:
                request.session.logout()
            return request.redirect('/web/database/manager')
        except Exception as e:
            _logger.exception("Database deletion error.")
            error = "Database deletion error: %s" % (str(e) or repr(e))
            return self._render_template(error=error)

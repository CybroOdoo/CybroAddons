# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
from lxml import html

import odoo
from odoo import http
from odoo.tools.misc import file_open
from odoo.http import request
from odoo.addons.web.controllers import main
from odoo.addons.base.models.ir_qweb import render as qweb_render


DBNAME_PATTERN = '^[a-zA-Z0-9][a-zA-Z0-9_.-]+$'


class Database(main.Database):
    """A class that represents a database.
       This class inherits from `database.Database` and provides
       additional functionality for managing and rendering
       database templates.
       Attributes:
           None
       """

    def _render_template(self, **d):
        """Render the database template with the given data.
              Args:
                  **d: The data to render the template with.
              Returns:
                  str: The rendered database template.
         """
        d.setdefault('manage', True)
        d['insecure'] = odoo.tools.config.verify_admin_password('admin')
        d['list_db'] = odoo.tools.config['list_db']
        d['langs'] = odoo.service.db.exp_list_lang()
        d['countries'] = odoo.service.db.exp_list_countries()
        d['pattern'] = DBNAME_PATTERN
        try:
            d['databases'] = http.db_list()
            d['incompatible_databases'] = odoo.service.\
                db.list_db_incompatible(d['databases'])
        except odoo.exceptions.AccessDenied:
            d['databases'] = [request.db] if request.db else []
        templates = {}
        with file_open(
                "verify_and_delete_database/static/src/public/database_manager.qweb.html",
                "r") as fd:
            templates['database_manager'] = fd.read()
        with file_open(
                "web/static/src/public/database_manager.master_input.qweb.html", "r") as fd:
            templates['master_input'] = fd.read()
        with file_open(
                "web/static/src/public/database_manager.create_form.qweb.html", "r") as fd:
            templates['create_form'] = fd.read()

        def load(template_name,options):
            fromstring = html.document_fromstring if \
                template_name == 'database_manager' \
                else html.fragment_fromstring
            return fromstring(templates[template_name]), template_name
        return qweb_render('database_manager', d, load=load)

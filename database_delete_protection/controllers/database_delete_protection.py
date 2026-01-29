# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ajmunnisa K P @cybrosys(odoo@cybrosys.com)
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
from odoo.tools.misc import file_open
from odoo.addons.base.models.ir_qweb import render as qweb_render
from odoo.addons.web.controllers.main import Database

DBNAME_PATTERN = '^[a-zA-Z0-9][a-zA-Z0-9_.-]+$'
db_monodb = http.db_monodb


class Database(Database):
    """A class that represents a database.
       Attributes: None
    """
    def _render_template(self, **d):
        """ Render the database template with the given data.
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
        # databases list
        d['databases'] = []
        # databases delete protection
        db_to_restrict_delete = odoo.tools.config.get('db_delete_restrict',
                                                      False)
        if db_to_restrict_delete:
            databases_restrict_delete = db_to_restrict_delete.replace(" ", "")
            d['delete_restrict'] = databases_restrict_delete.split(',')
        # databases list
        try:
            d['databases'] = http.db_list()
            d['incompatible_databases'] = odoo.service.db.list_db_incompatible(
                d['databases'])
        except odoo.exceptions.AccessDenied:
            monodb = db_monodb()
            if monodb:
                d['databases'] = [monodb]
        templates = {}
        with file_open(
                "database_delete_protection/static/src/public/database_manager.qweb.html",
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

        def load(template_name, options):
            """ This function is responsible for loading the QWeb templates
                 for the given template name and options.
                :returns: The 'database_manager' template.
            """
            fromstring = html.document_fromstring \
                if template_name == 'database_manager' else html.fragment_fromstring
            return (fromstring(templates[template_name]), template_name)

        return qweb_render('database_manager', d, load=load)

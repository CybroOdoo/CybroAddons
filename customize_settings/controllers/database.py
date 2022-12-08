# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

import odoo
from odoo import http
from odoo.http import request
from lxml import html
from odoo.addons.base.models.ir_qweb import render as qweb_render

from odoo.addons.web.controllers.database import Database

DBNAME_PATTERN = '^[a-zA-Z0-9][a-zA-Z0-9_.-]+$'

from odoo.tools.misc import file_open

db_monodb = odoo.tools.config['list_db']


class Debrand(Database):

    def _render_template(self, **d):
        website_name = 'Database'
        dbname = request.db
        uid = (request.session.uid if dbname else None) or odoo.SUPERUSER_ID

        try:
            # create an empty registry
            registry = odoo.modules.registry.Registry(dbname)
            with registry.cursor() as cr:

                cr.execute("""SELECT c.name, c.write_date
                                                FROM res_users u
                                           LEFT JOIN res_company c
                                                  ON c.id = u.company_id
                                               WHERE u.id = %s
                                           """, (uid,))
                row = cr.fetchone()
                website_name = row[0]

        except Exception:
            pass
        d.setdefault('manage', True)
        d['insecure'] = odoo.tools.config.verify_admin_password('admin')
        d['list_db'] = odoo.tools.config['list_db']
        d['langs'] = odoo.service.db.exp_list_lang()
        d['countries'] = odoo.service.db.exp_list_countries()
        d['pattern'] = DBNAME_PATTERN

        d['website_name'] = website_name

        # databases list
        try:
            d['databases'] = http.db_list()
            d['incompatible_databases'] = odoo.service.db.list_db_incompatible(d['databases'])
        except odoo.exceptions.AccessDenied:
            d['databases'] = [request.db] if request.db else []

        templates = {}

        with file_open("customize_settings/static/src/public/database_manager.qweb.html", "r") as fd:
            templates['database_manager'] = fd.read()
        with file_open("web/static/src/public/database_manager.master_input.qweb.html", "r") as fd:
            templates['master_input'] = fd.read()
        with file_open("web/static/src/public/database_manager.create_form.qweb.html", "r") as fd:
            templates['create_form'] = fd.read()

        def load(template_name):
            fromstring = html.document_fromstring if template_name == 'database_manager' else html.fragment_fromstring
            return (fromstring(templates[template_name]), template_name)

        return qweb_render('database_manager', d, load)

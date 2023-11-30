# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
from . import models
from . import wizard

from odoo import api, SUPERUSER_ID


def uninstall_hook(cr, registry):
    """
        It deactivates associated form views, deletes records from the
        'ir_model_fields' table, and unlinks the 'employee.dynamic.fields'
        records.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    fields = env['employee.dynamic.fields'].search([])
    for field in fields:
        field.form_view_id.active = False
        query = """delete FROM ir_model_fields WHERE name = %s"""
        env.cr.execute(query, [field.name])
    fields.unlink()

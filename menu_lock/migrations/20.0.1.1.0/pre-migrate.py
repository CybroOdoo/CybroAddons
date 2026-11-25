# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo import SUPERUSER_ID, api
from odoo.tools import SQL


def migrate(cr, version):
    context = api.Environment(cr, SUPERUSER_ID, {})['res.users']._crypt_context()
    for table, old_column in [('res_users', 'login_password'), ('menu_password', 'password')]:
        table = SQL.identifier(table)
        column = SQL.identifier(old_column)
        cr.execute(SQL('ALTER TABLE %s ADD COLUMN menu_lock_hash varchar', table))
        cr.execute(SQL("SELECT id, %s FROM %s WHERE %s IS NOT NULL", column, table, column))
        for record_id, password in cr.fetchall():
            if password:
                cr.execute(SQL('UPDATE %s SET menu_lock_hash = %s WHERE id = %s',
                               table, context.hash(password), record_id))
        cr.execute(SQL('ALTER TABLE %s DROP COLUMN %s', table, column))

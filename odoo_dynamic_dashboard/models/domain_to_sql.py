# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.info)
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
###############################################################################
from odoo import api, models
from odoo.tools import SQL


@api.private
def get_query(self, domain, operation, field, start_date=None, end_date=None,
              group_by=False):
    """Dashboard Block Query Builder.

    Build the aggregation query of a dashboard block as an :class:`SQL` object.
    The result always exposes a ``value`` column, plus a column named after
    ``group_by`` when one is given.

    ``_search()`` already applies the record rules of the calling user, so no
    extra access filtering is needed here.
    """
    query = self._search(domain)
    table = query.table
    # Only a whitelisted aggregate ever reaches the SQL string: ``operation``
    # is a Selection, but this method is reachable on every model.
    if operation == 'sum' and field:
        value = SQL("COALESCE(SUM(%s), 0) AS value", table[field.name])
    elif operation == 'avg' and field:
        value = SQL("COALESCE(AVG(%s), 0) AS value", table[field.name])
    else:
        value = SQL("COUNT(*) AS value")
    select_parts = [value]
    if 'create_date' in self._fields:
        if start_date and start_date != 'null':
            query.add_where(SQL("%s >= %s", table['create_date'], start_date))
        if end_date and end_date != 'null':
            query.add_where(SQL("%s <= %s", table['create_date'], end_date))
    if group_by:
        group_sql = table[group_by.name]
        select_parts.append(
            SQL("%s AS %s", group_sql, SQL.identifier(group_by.name)))
        query.groupby = group_sql
    return query.select(*select_parts)


models.BaseModel.get_query = get_query

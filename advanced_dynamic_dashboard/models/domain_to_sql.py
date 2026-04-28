# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models

def get_sql(from_string, where_string, from_params , where_params):
    """Fetch all params and compine from and where params"""
    return from_string, where_string, from_params + where_params

def get_query(self, args, operation, field, start_date=None, end_date=None,
              group_by=False, apply_ir_rules=False):
    """ Dashboard block Query Creation """
    # Use _search instead of _where_calc
    query = self._search(
        domain=args,  # 'args' is the domain
        offset=0,
        limit=None,
        order=None,
        active_test=True,  # Matches your old active_test=True
        bypass_access=not apply_ir_rules  # If apply_ir_rules=True, don't bypass (apply rules); else bypass
    )

    # The rest of your code remains the same...
    if operation and field:
        data = 'COALESCE(%s(%s.%s),0) AS value' % (
            operation.upper(), self._table, field.name)
        join = ''
        group_by_str = ''
        if group_by:
            if group_by.ttype == 'many2one':
                relation_model = group_by.relation.replace('.', '_')
                join = ' INNER JOIN %s on "%s".id = "%s".%s' % (
                    relation_model, relation_model, self._table, group_by.name)
                rec_name = self.env[group_by.relation]._rec_name_fallback()
                data = data + ',"%s".%s AS %s' % (
                    relation_model, rec_name, group_by.name)
                group_by_str = ' Group by "%s".%s' % (relation_model, rec_name)
            else:
                data = data + ',"%s".%s' % (self._table, group_by.name)
                group_by_str = ' Group by "%s".%s' % (
                    self._table, str(group_by.name))
    else:
        data = '"%s".id' % (self._table)
    # from_clause, where_clause, where_clause_params = query.get_sql()
    from_string, from_params = query.from_clause
    where_string, where_params = query.where_clause
    from_clause, where_clause, where_clause_params= get_sql(from_string, where_string, from_params , where_params)


    where_str = where_clause and (" WHERE %s" % where_clause) or ''
    extra_where = []
    if start_date and start_date != 'null':
        extra_where.append(f'"{self._table}"."create_date" >= \'{start_date}\'')
    if end_date and end_date != 'null':
        extra_where.append(f'"{self._table}"."create_date" <= \'{end_date}\'')
    if extra_where:
        if where_str:
            where_str += " AND " + " AND ".join(extra_where)
        else:
            where_str = " WHERE " + " AND ".join(extra_where)

    query_str = 'SELECT %s FROM ' % data + from_clause + join + where_str + group_by_str

    def format_param(x):
        """Format the input as a string, handling tuples and single values appropriately."""
        if not isinstance(x, tuple):
            return "'" + str(x) + "'"
        elif isinstance(x, tuple) and len(x) == 1:
            return "(" + str(x[0]) + ")"
        else:
            return str(x)

    exact_query = query_str % tuple(map(format_param, where_clause_params))
    return exact_query


models.BaseModel.get_query = get_query

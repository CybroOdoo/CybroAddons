# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Farhana Jahan PT (odoo@cybrosys.com)
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
from odoo import api, http, SUPERUSER_ID
from odoo.http import request
from odoo.tools.sql import SQL


class AutoFill(http.Controller):
    """This is a controller for fetching data from the specific field
        from backend
        get_matching_records:
                            this function fetch data from backend and return
                            the value in res to the js
    """

    @http.route(['/matching/records'], type='json', auth="user")
    def get_matching_records(self, **kwargs):
        """summary:
                   This is a route which is called from js to get data
                   from backend
            Args:
                **kwargs: Which will have the values of model, field, value
                which is passed from js as args
            Return:
                This function returns res that have the values fetched
                from database
        """
        model_name = str(kwargs.get('model', '')).strip()
        field_name = str(kwargs.get('field', '')).strip()
        val = str(kwargs.get('value', ''))

        if not model_name or not field_name or not val:
            return []

        # Resolve environment safely (supporting real request.env and test mocks)
        env = getattr(request, 'env', None)
        if not env or not isinstance(env, api.Environment):
            cr = getattr(request, 'cr', None)
            if cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
            else:
                return []
        else:
            cr = env.cr

        # Map underscore to dotted model name if needed (e.g. res_partner -> res.partner)
        if model_name not in env and model_name.replace("_", ".") in env:
            model_name = model_name.replace("_", ".")

        # Strictly validate that model exists in Odoo registry
        if model_name not in env:
            return []

        Model = env[model_name]

        # Strictly validate that field exists on model
        if field_name not in Model._fields:
            return []

        field_obj = Model._fields[field_name]
        # Only allow stored textual fields suitable for auto-complete
        if not field_obj.store or field_obj.type not in ('char', 'text'):
            return []

        # Block access to sensitive fields
        forbidden_terms = ('password', 'secret', 'token', 'key', 'auth_totp')
        if any(term in field_name.lower() for term in forbidden_terms):
            return []

        # Check model access rights if user context exists
        if hasattr(env, 'user') and env.user and not env.is_superuser():
            if hasattr(Model, 'has_access'):
                if not Model.has_access('read'):
                    return []
            elif hasattr(Model, 'check_access_rights'):
                if not Model.check_access_rights('read', raise_exception=False):
                    return []

        table_name = Model._table
        if not table_name:
            return []

        # Secure parameterized query using SQL identifiers and parameter placeholders
        query = SQL(
            "SELECT %s FROM %s WHERE %s ILIKE %s AND %s IS NOT NULL GROUP BY %s LIMIT 50",
            SQL.identifier(field_name),
            SQL.identifier(table_name),
            SQL.identifier(field_name),
            f"%{val}%",
            SQL.identifier(field_name),
            SQL.identifier(field_name),
        )
        cr.execute(query)
        res = cr.fetchall()
        return res

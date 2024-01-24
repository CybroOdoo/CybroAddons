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
from odoo import http
from odoo.http import request


class AutoFill(http.Controller):
    """This is a controller for fetching data from the specific field
        from backend
        get_matching_records:
                            this function fetch data from backend and return
                            the value in res to the js
    """

    @http.route(['/matching/records'], type='json', auth="none")
    def get_matching_records(self, **kwargs):
        """summary:
                   This is a route which is called from js to get data
                   from backend
            Args:
                **kwargs:Which will have the values of model,field,value
                which is passed from js as args
            Return:
                This function returns res that have the values fetched
                from database
        """
        model = str(kwargs.get('model', ''))
        field = str(kwargs.get('field', ''))
        value = str(kwargs.get('value', ''))
        model = model.replace(".", "_")
        cr = request.cr
        if len(value) > 0:
            query = """SELECT %s FROM %s WHERE %s ~* '%s' GROUP BY %s""" % (
                field, model, field, value, field)
            cr.execute(query)
            res = cr.fetchall()
        else:
            res = []
        return res


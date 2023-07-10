# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Mruthul Raj(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import http
from odoo.http import request


class MatchingRecords(http.Controller):
    """
    Controller class to get matching records based on provided criteria.
    """
    @http.route(['/matching/records'], type='json', auth="none")
    def get_matching_records(self, **kwargs):
        """
        Retrieve matching records based on the provided model, field, and value.
        Returns:
            list: List of matching records.
        """
        model = str(kwargs['model'])
        field = str(kwargs['field'])
        model = model.replace(".", "_")
        if len(str(kwargs['value'])) > 0:
            query = f"SELECT {field} FROM {model} WHERE " \
                    f"{field} ~* '{str(kwargs['value'])}' GROUP BY {field}"
            request.cr.execute(query)
            res = request.cr.fetchall()
        else:
            res = []
        return res

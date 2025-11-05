# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Avinash Nk(<https://www.cybrosys.com>)
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

from odoo.http import request
from odoo import http


class GetMatchingRecords(http.Controller):

    @http.route(['/matching/records'], type='json', auth="none")
    def get_matching_records(self, **kwargs):
        model = str(kwargs['model'])
        field = str(kwargs['field'])
        value = str(kwargs['value'])
        model = model.replace(".", "_")
        cr = request.cr
        if len(value) > 0:
            query = """SELECT %s FROM %s WHERE %s ~* '%s' GROUP BY %s""" % (field, model, field, value, field)
            cr.execute(query)
            res = cr.fetchall()
        else:
            res = []
        return res

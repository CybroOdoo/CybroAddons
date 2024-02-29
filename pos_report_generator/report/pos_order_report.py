# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
################################################################################
from odoo import api, models


class PosReport(models.AbstractModel):
    """To retrieve the report days"""
    _name = 'report.pos_report_generator.pos_order_report'
    _description = 'POS Report Generator'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
            This method is used to retrieve report values for a POS order
            report.
        """
        if self.env.context.get('pos_order_report'):
            if data.get('report_data'):
                data.update({'report_main_line_data': data.get('report_data')[
                    'report_lines'],
                             'Filters': data.get('report_data')['filters'],
                             'company': self.env.company,
                             })
            return data

# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
from odoo import api, models


class PosOrder(models.AbstractModel):
    _name = 'report.all_in_one_pos_kit.pos_order_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
            Retrieves report values based on the given docids and data.
            If the context indicates that this is a POS order report, it processes the report data.

            :param docids: List of document IDs for which to generate the report.
            :param data: Dictionary containing report data and filters.
            :return: Updated data dictionary for report generation.
        """
        if self.env.context.get('pos_order_report'):
            if data.get('report_data'):
                data.update({'report_main_line_data': data.get('report_data')[
                    'report_lines'],
                             'Filters': data.get('report_data')['filters'],
                             'company': self.env.company,
                             })
            return data

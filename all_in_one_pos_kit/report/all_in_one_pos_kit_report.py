# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
from odoo import api, models


class PosOrder(models.AbstractModel):
    """Model to generate the POS order report."""
    _name = 'report.all_in_one_pos_kit.pos_order_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Get the report values for generating the POS order report.
        :param docids: The IDs of the records to include in the report.
        :param data: Additional data for generating the report (optional).
        :return: A dictionary containing the report values."""
        if self.env.context.get('pos_order_report'):
            if data.get('report_data'):
                data.update({
                    'report_main_line_data': data.get('report_data')[
                        'report_lines'],
                    'Filters': data.get('report_data')['filters'],
                    'company': self.env.company})
            return data

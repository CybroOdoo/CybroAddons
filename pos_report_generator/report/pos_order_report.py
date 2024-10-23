# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, models


class PosReport(models.AbstractModel):
    """ To retrieve the report days """
    _name = 'report.pos_report_generator.pos_order_report'
    _description = 'POS Report Generator'

    @api.model
    def _get_report_values(self, docids, data=None):
        """ This method is used to retrieve report values for a POS order
        report."""
        if self.env.context.get('pos_order_report'):
            if data.get('report_data'):
                data.update({'report_main_line_data': data.get('report_data')[
                    'report_lines'],
                        'Filters': data.get('report_data')['filters'],
                        'company': self.env.company,
                    })
            return data

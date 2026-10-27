# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: (odoo@cybrosys.com)
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
    _name = 'report.all_in_one_pos_kit.pos_order_report'
    _description = 'POS Report Generator'

    @api.model
    def _get_report_values(self, docids, data=None):
        """ This method is used to retrieve report values for a POS order
        report."""
        data = dict(data or {})
        report_data = data.get('report_data') or {}
        data.setdefault('doc_ids', docids)
        data.setdefault('doc_model', data.get('model'))
        data.update({
            'report_main_line_data': report_data.get('report_lines') or [],
            'Filters': report_data.get('filters') or {},
            'company': self.env.company,
        })
        return data

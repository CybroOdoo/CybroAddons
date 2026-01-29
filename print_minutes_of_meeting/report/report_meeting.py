# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Irfan T @ Cybrosys, (odoo@cybrosys.com)
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


class ReportMeeting(models.AbstractModel):
    """Model for pdf meeting report"""
    _name = 'report.meeting'
    _description = 'Report Meeting'

    @api.model
    def _get_report_values(self, docids, data=None):
        """Function to get the report data values to print"""
        return {
            'doc_ids': docids,
            'doc_model': 'calendar.event',
            'docs': self.env['calendar.event'].browse(docids),
            'data': data,
        }

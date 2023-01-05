# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Noorjahan @ Cybrosys, (odoo@cybrosys.com)
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
from odoo import models, api


class ReportMinutesofMeeting(models.AbstractModel):
    _name = 'report.print_minutes_of_meeting.report_mom_template'
    _description = 'Minutes of meeting'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['calendar.event'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'calendar.event',
            'docs': docs,
            'data': data,
        }

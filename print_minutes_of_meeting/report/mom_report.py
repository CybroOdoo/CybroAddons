# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, models


class ReportMinutesofMeeting(models.AbstractModel):
    """ Class for adding minutes of meeting report """
    _name = 'report.print_minutes_of_meeting.report_mom_template'
    _description = 'Minutes of Meeting'

    @api.model
    def _get_report_values(self, docids, data=None):
        """ Get report values """
        docs = self.env['calendar.event'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'calendar.event',
            'docs': docs,
            'data': data,
        }

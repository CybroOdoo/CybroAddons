# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2015-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime
import time
from openerp import models, fields


class MrpProgressBar(models.Model):

    _inherit = 'mrp.production.workcenter.line'

    def time_progress(self):
        for records in self:
            if records.state == 'startworking':
                if records.date_planned and records.date_planned_end:
                    start_date = datetime.strptime(records.date_planned, "%Y-%m-%d %H:%M:%S")
                    end_date = datetime.strptime(records.date_planned_end, "%Y-%m-%d %H:%M:%S")
                    # convert to unix timestamp
                    start_date_seconds = time.mktime(start_date.timetuple())
                    end_date_seconds = time.mktime(end_date.timetuple())
                    today_seconds = time.mktime(datetime.today().timetuple())
                    total_diff = end_date_seconds - start_date_seconds
                    current_diff = today_seconds - start_date_seconds
                    percentage = ((current_diff / total_diff) * 100)
                    if percentage > 100:
                        percentage = 100
                    if percentage < 0.0:
                        percentage = 0
                    records.write({'progress_bar': percentage})

    progress_bar = fields.Float(string="Progress", readonly=True)
    progress_bar_compute = fields.Float(string="Progress compute", compute="time_progress")

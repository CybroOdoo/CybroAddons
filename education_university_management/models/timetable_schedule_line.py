# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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
from odoo import api, fields, models


class TimeTableScheduleLine(models.Model):
    """ Manages the schedule for subjects and faculty while
        creating timetable"""
    _name = 'timetable.schedule.line'
    _description = 'Timetable Schedule'
    _rec_name = 'period_id'

    period_id = fields.Many2one('timetable.period',
                                string="Period", required=True,
                                help="select period")
    faculty_id = fields.Many2one('university.faculty',
                                 string='Faculty', required=True,
                                 help="Set faculty who is taking ")
    time_from = fields.Float(string='From', related='period_id.time_from',
                             readonly=False,
                             help="Start and End time of Period.")
    time_till = fields.Float(string='Till', related='period_id.time_to',
                             readonly=False,
                             help="Start and End time of Period.")
    subject = fields.Many2one('university.subject',
                              string='Subjects', required=True,
                              help="Select the subject to schedule timetable")
    week_day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string='Week', required=True, help="Select week for scheduling period")
    timetable_id = fields.Many2one('university.timetable',
                                   required=True, string="Timetable",
                                   help="Relation to university.timetable")
    batch_id = fields.Many2one('university.batch', string='Batch',
                               help="Batch")

    @api.model
    def create(self, vals):
        """ This method overrides the create method to automatically store
            :param vals (dict): Dictionary containing the field values for the
                                new timetable schedule line.
            :returns class:`timetable.schedule.line`The created timetable
                            schedule line record.
        """
        res = super(TimeTableScheduleLine, self).create(vals)
        res.batch_id = res.timetable_id.batch_id.id
        return res

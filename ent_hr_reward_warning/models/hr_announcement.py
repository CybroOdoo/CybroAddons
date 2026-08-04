# -*- coding: utf-8 -*-
################################################################################
#
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrAnnouncement(models.Model):
    """ Model for creating announcements. """
    _name = 'hr.announcement'
    _description = 'HR Announcement'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Code No:', default='New', copy=False, readonly=True,
                       help="Sequence Number of the Announcement")
    announcement_reason = fields.Text(string='Title',
                                      required=True,
                                      help="Announcement Subject")
    state = fields.Selection(
        [('draft', 'Draft'), ('to_approve', 'Waiting For Approval'),
         ('approved', 'Approved'), ('rejected', 'Refused'),
         ('expired', 'Expired')],
        string='Status', default='draft',
        tracking=True, help="State of the Announcement")
    requested_date = fields.Date(string='Requested Date',
                                 default=datetime.now().strftime('%Y-%m-%d'),
                                 help="Create Date of Record")
    attachment_ids = fields.Many2many(comodel_name='ir.attachment',
                                      relation='doc_warning_rel',
                                      column1='doc_id', column2='attach_id4',
                                      string="Attachment",
                                      help='You can attach the copy of your '
                                           'Letter')
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                 default=lambda self: self.env.user.company_id,
                                 readonly=True, help="Login user Company")
    is_announcement = fields.Boolean(string='Is general Announcement?',
                                     help="To set Announcement as general "
                                          "announcement")
    announcement_type = fields.Selection(
        [('employee', 'By Employee'), ('department', 'By Department'),
         ('job_position', 'By Job Position')],
        help="Select the type of employee")
    employee_ids = fields.Many2many(comodel_name='hr.employee',
                                    relation='hr_employee_announcements',
                                    column1='announcement', column2='employee',
                                    string='Employees',
                                    help="Employee's which want to see this "
                                         "announcement")
    department_ids = fields.Many2many(comodel_name='hr.department',
                                      relation='hr_department_announcements',
                                      column1='announcement',
                                      column2='department',
                                      string='Departments',
                                      help="Department's which want to see "
                                           "this announcement")
    position_ids = fields.Many2many(comodel_name='hr.job',
                                    relation='hr_job_position_announcements',
                                    column1='announcement',
                                    column2='job_position',
                                    string='Job Positions',
                                    help="Job Position's which want to see "
                                         "this announcement")
    announcement = fields.Html(string='Letter', help="Announcement Content")
    date_start = fields.Date(string='Start Date', default=fields.Date.today(),
                             required=True, help="Start date of "
                                                 "announcement want"
                                                 " to see")
    date_end = fields.Date(string='End Date', default=fields.Date.today(),
                           required=True, help="End date of "
                                               "announcement want too"
                                               " see")

    def action_reject(self):
        """For rejecting the announcement"""
        self.state = 'rejected'

    def action_approve(self):
        """For approving the announcement"""
        self.state = 'approved'

    def action_send(self):
        """For sending the announcement approval"""
        self.state = 'to_approve'

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        """Check the date condition"""
        if self.date_start > self.date_end:
            raise ValidationError("Start date must be less than End Date")

    @api.model_create_multi
    def create(self, vals_list):
        """Creating sequence for announcement"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                if vals.get('is_announcement'):
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'hr.announcement.general')
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code(
                        'hr.announcement')
        return super(HrAnnouncement, self).create(vals_list)

    def get_expiry_state(self):
        """
        Function is used for Expiring Announcement based on expiry date
        it activate from the crone job.
        """
        announcement = self.search([
            ('state', '!=', 'rejected'),
            ('date_end', '<', fields.Date.today()),
        ])
        announcement.write({
            'state': 'expired'
        })

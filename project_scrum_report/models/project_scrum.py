# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2016-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Jesni Banu(<http://www.cybrosys.com>)
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
from openerp import models, api, fields, _


class ProjectScrum(models.Model):
    _name = 'project.scrum'

    name = fields.Char(string='Scrum Code')
    user_id = fields.Many2one('res.users', string='User')
    date = fields.Date(string='Date')
    scrum_plan = fields.One2many('scrum.plan', 'scrum_plan_obj', string='Scrum Plan')
    scrum_report = fields.One2many('scrum.report', 'scrum_report_obj', string='Scrum Report')
    state = fields.Selection([('plan', 'Scrum Plan'),
                              ('working', 'Working'),
                              ('report', 'Scrum Report'),
                              ('done', 'Done')], string='State', default='plan', readonly=1)

    _sql_constraints = [('scrum_unique', 'unique(user_id, date)', 'A user can only have one Scrum with same date')]
    _defaults = {
        'user_id': lambda obj, cr, uid, context: uid,
        'date': lambda *a: datetime.now().strftime('%Y-%m-%d')
    }

    @api.multi
    def create_scrum_report(self):
        scrum_report_obj = self.env['scrum.report']
        for each in self.scrum_plan:
            scrum_report_obj.create({'task': each.task.id,
                                     'project': each.project.id,
                                     'scrum_report_obj': each.scrum_plan_obj.id,
                                     'worked_hrs': each.planned_hrs,
                                     'remarks': each.remarks,
                                     'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                     'status': each.status
                                     })
        self.state = 'report'

    @api.model
    def create(self, vals):
        result = super(ProjectScrum, self).create(vals)
        result['name'] = 'Scrum_' + result['date'] + '_' + result['user_id'].name
        result['state'] = 'working'
        return result

    @api.multi
    def send(self):
        email_from = self.env['mail.message']._get_default_from()
        partner_ids = [3]
        mail_content = "Hi sir, <br/> Please go through the work report of today.<br/> <br/>"
        mail_content += "<table border='3px solid black' width='100%'>" \
                        "<tr>" \
                        "<th>SI NO</th><th>TASK</th><th>PROJECT</th><th>WORKED HOURS</th><th>STATUS</th><th>REMARKS" \
                        "</th></tr>"
        count = 1
        for each in self.scrum_report:
            if each.project.user_id.partner_id.id not in partner_ids:
                partner_ids.append(each.project.user_id.partner_id.id)
            mail_content += "<tr>" \
                            "<td style='text-align: center;'>%s</td><td>%s</td><td>%s</td>" \
                            "<td style='text-align: center;'>%s</td><td>%s</td><td>%s</td></tr>"\
                            % (count, each.task.name, each.project.name, each.worked_hrs,
                               dict(self.env['scrum.report'].fields_get(['status'])['status']['selection'])[each.status]
                               , each.remarks)

            count += 1

        mail_content += "</table>"
        message = self.env['mail.message'].create({
            'subject': _('Daily Work Report_%s_%s') % (self.date, self.user_id.name),
            'body': mail_content,
            'email_from': email_from,
            'reply_to': self.user_id.email,
            'no_auto_thread': True,
            'model': 'project.scrum'
        })
        message.write({'needaction_partner_ids': [(4, pid) for pid in partner_ids]})
        message.write({'partner_ids': [(4, pid) for pid in partner_ids]})
        admin_partner = self.env['res.partner'].browse(3)
        main_content1 = {
            'subject': _('Daily Work Report_%s_%s') % (self.date, self.user_id.name),
            'author_id': self.user_id.partner_id.id,
            'body_html': mail_content,
            'email_to': admin_partner.email,

        }
        self.env['mail.mail'].create(main_content1).send()
        self.state = 'done'


class ScrumPlan(models.Model):
    _name = 'scrum.plan'

    name = fields.Char(string='Scrum Code', related='scrum_plan_obj.name', store=1)
    user_id = fields.Many2one('res.users', string='User', related='scrum_plan_obj.user_id', store=1)
    project_manager = fields.Many2one('res.users', related='project.user_id', store=1)
    date = fields.Datetime(string='Date', store=1, default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    task = fields.Many2one('project.task', string='Task', required=1)
    project = fields.Many2one('project.project', string='Project', related='task.project_id')
    status = fields.Selection([('scheduled', 'Scheduled'),
                               ('on_going', 'On going'),
                               ('halted', 'Halted'),
                               ], required=1, string='Status')
    remarks = fields.Text(string='Remarks', required=1)
    planned_hrs = fields.Float(string='Planned Hours', required=1)
    scrum_plan_obj = fields.Many2one('project.scrum', invisible=1)


class ScrumReport(models.Model):
    _name = 'scrum.report'

    project_manager = fields.Many2one('res.users', related='project.user_id', store=1)
    name = fields.Char(string='Scrum Code', related='scrum_report_obj.name', store=1)
    user_id = fields.Many2one('res.users', string='User', related='scrum_report_obj.user_id', store=1)
    date = fields.Datetime(string='Date', store=1)
    task = fields.Many2one('project.task', string='Task', required=1)
    project = fields.Many2one('project.project', string='Project', related='task.project_id')
    status = fields.Selection([('scheduled', 'Scheduled'),
                               ('on_going', 'On going'),
                               ('halted', 'Halted'),
                               ('completed', 'Completed')], required=1, string='Status')
    remarks = fields.Text(string='Remarks', required=1)
    worked_hrs = fields.Float(string='Worked Hours', required=1)
    scrum_report_obj = fields.Many2one('project.scrum', invisible=1)

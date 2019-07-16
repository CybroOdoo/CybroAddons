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
from openerp import models, fields, api, _


class ApproveRecurrentTask(models.Model):
    _name = 'approve.recurrent.task'

    task = fields.Many2one('project.task', string='Task')
    project = fields.Many2one('project.project', string='Project')
    user_id = fields.Many2one('res.users', string='Requested user')
    team_lead = fields.Many2one('res.users', string='Team lead')
    from_date = fields.Datetime(string='Start time')
    interval_number = fields.Integer(string='Interval Qty')
    interval_type = fields.Selection([('days', 'Days'),
                                      ('weeks', 'Weeks'),
                                      ('months', 'Months')], string='Interval Unit')
    name = fields.Char(string='Name')
    state = fields.Selection([
        ('waiting', 'Waiting For Approval '),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], 'Status', readonly=True, default='waiting', select=True)
    reason = fields.Text(string='Reason')

    @api.multi
    def approve_recurrent_task(self):
        doc_id = self.env.ref('project_recurrent_task.recurrent_document_22')
        rec_inv_doc = self.env['subscription.subscription']
        rec_inv_doc_id = rec_inv_doc.create({'name': self.name + ' ' + 'Task',
                                             'interval_type': self.interval_type,
                                             'interval_number': self.interval_number,
                                             'doc_source': doc_id.model.model + ',' + str(self.task.id),
                                             })
        rec_inv_doc_id.set_process()
        self.state = 'approved'


class WizardReason(models.Model):
    _name = 'wizard.reason'

    @api.multi
    def send_reason(self):
        context = self._context
        approval_obj = self.env['approve.recurrent.task'].search([('id', '=', context.get('approval_id'))])
        approval_obj.write({'state': 'rejected',
                            'reason': self.reason})

    reason = fields.Text(string="Reason")

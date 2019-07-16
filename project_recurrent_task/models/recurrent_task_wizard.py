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
from openerp import models, fields, api, _


class RecurrentTaskWizard(models.TransientModel):
    _name = "wizard.recurrent.task"
    _description = "Recurrent Task"

    name = fields.Char(string='Recurrent document name')
    interval_number = fields.Integer(string='Interval Qty')
    interval_type = fields.Selection([('days', 'Days'),
                                      ('weeks', 'Weeks'),
                                      ('months', 'Months')], string='Interval Unit')

    @api.multi
    def create_recurrent_task(self):
        obj = self.env['approve.recurrent.task']
        task_id = self.env['project.task'].browse(self._context.get('task_id'))
        obj.create({
            'task': task_id.id,
            'project': task_id.project_id.id,
            'user_id': self.env.user.id,
            'team_lead': task_id.project_id.user_id.id,
            'from_date': datetime.today(),
            'interval_number': self.interval_number,
            'interval_type': self.interval_type,
            'name': self.name
        })



# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
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
from odoo import models, api, fields, _
from odoo.exceptions import Warning, ValidationError


class ProjectMaster(models.Model):
    _inherit = 'project.project'

    use_sub_task = fields.Boolean(string="SubTasks", default=True)
    label_sub_tasks = fields.Char(default='SubTasks')


class SubTaskMaster(models.Model):
    _name = 'project.sub_task'

    def stage_find(self, section_id, domain=[], order='sequence'):
        section_ids = []
        if section_id:
            section_ids.append(section_id)
        section_ids.extend(self.mapped('task_ref').ids)
        search_domain = []
        if section_ids:
            search_domain = [('|')] * (len(section_ids) - 1)
            for section_id in section_ids:
                search_domain.append(('task_ids', '=', section_id))
        search_domain += list(domain)
        # perform search, return the first found
        return self.env['project.sub_task.type'].search(search_domain, order=order, limit=1).id

    @api.onchange('task_ref')
    def get_default_stage_id(self):
        """ Gives default stage_id """
        project_id = self.task_ref.id
        if not project_id:
            return False
        self.stage_id = self.stage_find(project_id, [('fold', '=', False)])

    @api.constrains('date_deadline', 'task_ref')
    def date_deadline_validation(self):
        if self.date_deadline > self.task_ref.date_deadline:
            raise ValidationError(_("Your main task will dead at this date"))

    active = fields.Boolean(default=True)
    name = fields.Char(string="Name", requires=True)
    priority = fields.Selection([('0', 'Normal'), ('1', 'High')], 'Priority', select=True, default='0')
    assigned_user = fields.Many2one('res.users', string="Assigned Person", required=1)
    task_ref = fields.Many2one('project.task', string='Task', required=1,
                               default=lambda self: self.env.context.get('default_task_ref'),
                               domain=['|', '|', ('project_id.use_sub_task', '=', True),
                                                                                  ('stage_id.done_state', '=', False),
                                                                                  ('stage_id.cancel_state', '=', False)])
    stage_id = fields.Many2one('project.sub_task.type', string='Stage', select=True,
                               domain="[('task_ids', '=', task_ref)]", copy=False)
    project_id = fields.Many2one('project.project', related='task_ref.project_id', string='Project')
    notes = fields.Html(string='Notes')
    planned_hours = fields.Float(string='Initially Planned Hours',
                                 help='Estimated time to do the Subtask, usually set by the project manager when the '
                                      'task is in draft state.')
    partner_id = fields.Many2one('res.partner', string='Customer', related='task_ref.partner_id', readonly=1)
    color = fields.Integer(string='Color Index')
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=lambda self: [('res_model', '=', self._name)],
                                     auto_join=True, string='Attachments')
    displayed_image_id = fields.Many2one('ir.attachment',
                                         domain="[('res_model', '=', 'project.sub_task'), ('res_id', '=', id), ('mimetype', 'ilike', 'image')]",
                                         string='Displayed Image')

    tag_ids = fields.Many2one('project.sub_task.tags', string='Tags')
    write_date = fields.Datetime(string='Last Modification Date', readonly=True, select=True)
    date_start = fields.Datetime(string='Starting Date', readonly=True, select=True, default=fields.Datetime.now())
    date_deadline = fields.Date(string='Deadline')
    active = fields.Boolean(string='Active', default=True)
    description = fields.Html(String='Description')
    sequence = fields.Integer(string='Sequence', select=True, default=10,
                              help="Gives the sequence order when displaying a list of sub tasks.")
    company_id = fields.Many2one('res.company', string='Company')
    date_last_stage_update = fields.Datetime(string='Last Stage Update', select=True, copy=False, readonly=True,
                                             default=fields.Datetime.now())
    date_assign = fields.Datetime(string='Assigning Date', select=True, copy=False, readonly=True)

    @api.model
    def create(self, vals):
        context = dict(self.env.context)
        if vals.get('task_ref'):
            vals['stage_id'] = self.stage_find(vals.get('task_ref'), [('fold', '=', False)])
        if vals.get('user_id'):
            vals['date_assign'] = fields.Datetime.now()
        task = super(SubTaskMaster, self.with_context(context)).create(vals)
        return task


class TaskMaster(models.Model):
    _inherit = 'project.task'

    sub_task_lines = fields.One2many('project.sub_task', 'task_ref', string='Sub Tasks')
    date_deadline = fields.Date('Deadline', select=True, copy=False, required=1)
    use_sub_task = fields.Boolean(string="SubTasks", related='project_id.use_sub_task')
    subtask_count = fields.Integer(string='Count', compute='sub_task_found')

    @api.depends('sub_task_lines')
    def sub_task_found(self):
        for each in self:
            each.subtask_count = len(each.sub_task_lines)

    @api.constrains('stage_id')
    def restrict(self):
        obj = self.env['project.sub_task.type'].search([('cancel_state', '=', True)])
        if self.stage_id.cancel_state:
            for each in self.sub_task_lines:
                each.write({'stage_id': obj.id})
        if self.stage_id.done_state:
            for each in self.sub_task_lines:
                if not each.stage_id.done_state:
                    raise ValidationError(_("You can't move it to final stage. Some child tasks are not completed yet.!"))

    @api.multi
    def _check_child_task(self):
        for task in self:
            if task.sub_task_lines:
                for child in task.sub_task_lines:
                    if child.stage_id and not child.stage_id.fold:
                        raise Warning("Sub task still open.\nPlease cancel or complete child task first.")
                    else:
                        child.unlink()
        return True

    @api.multi
    def unlink(self):
        self._check_child_task()
        res = super(TaskMaster, self).unlink()
        return res

    @api.multi
    def write(self, vals):
        if vals.get('alias_model'):
            model_ids = self.pool.get('ir.model').search(
                                                         [('model', '=', vals.get('alias_model', 'project.sub_task'))])
            vals.update(alias_model_id=model_ids[0])
        res = super(TaskMaster, self).write(vals)
        if 'active' in vals:
            tasks = self.with_context(active_test=False).mapped('sub_task_lines')
            tasks.write({'active': vals['active']})
        return res


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    done_state = fields.Boolean(string='Final Stage',
                                help='This stage is Final Stage.')
    cancel_state = fields.Boolean(string='Cancel Stage',
                                  help='This stage is Cancel Stage.')

    @api.onchange('done_state', 'cancel_state')
    def set_done(self):
        obj = self.env['project.task.type'].search([])
        if self.done_state is True:
            for each in obj:
                if each.id != self.id:
                    each.write({'done_state': False})
        if self.cancel_state is True:
            for each in obj:
                if each.id != self.id:
                    each.write({'cancel_state': False})


class ProjectSubTaskType(models.Model):
    _name = 'project.sub_task.type'
    _description = 'Sub Task Stage'
    _order = 'sequence'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(string='Description', translate=True)
    sequence = fields.Integer(string='Sequence')
    task_ids = fields.Many2many('project.task', string="Task Ids")
    legend_priority = fields.Char(string='Priority Management Explanation', translate=True,
                                  help='Explanation text to help users using the star and priority mechanism on stages '
                                       'or issues that are in this stage.')
    legend_blocked = fields.Char(string='Kanban Blocked Explanation', translate=True,
                                 help='Override the default value displayed for the blocked state for kanban selection,'
                                      'when the task or issue is in that stage.')
    legend_done = fields.Char(string='Kanban Valid Explanation', translate=True,
                              help='Override the default value displayed for the done state for kanban selection, when '
                                   'the task or issue is in that stage.')
    legend_normal = fields.Char(string='Kanban Ongoing Explanation', translate=True,
                                help='Override the default value displayed for the normal state for kanban selection, '
                                     'when the task or issue is in that stage.')
    fold = fields.Boolean(string='Folded in Tasks Pipeline',
                          help='This stage is folded in the kanban view when '
                               'there are no records in that stage to display.')
    done_state = fields.Boolean(string='Final Stage',
                                help='This stage is Final Stage.')
    cancel_state = fields.Boolean(string='Cancel Stage',
                                  help='This stage is Cancel Stage.')

    @api.onchange('done_state', 'cancel_state')
    def set_done(self):
        obj = self.env['project.task.type'].search([])
        if self.done_state is True:
            for each in obj:
                if each.id != self.id:
                    each.write({'done_state': False})
        if self.cancel_state is True:
            for each in obj:
                if each.id != self.id:
                    each.write({'cancel_state': False})

    def _get_default_task_ids(self, cr, uid, ctx=None):
        if ctx is None:
            ctx = {}
        default_task_ids = ctx.get('default_task_ids')
        return [default_task_ids] if default_task_ids else None

    _defaults = {
        'sequence': 1,
        'task_ids': _get_default_task_ids,
    }
    _order = 'sequence'


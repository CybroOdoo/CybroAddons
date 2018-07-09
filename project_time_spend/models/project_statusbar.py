from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class ProjectCustom(models.Model):
    _inherit = 'project.task'

    @api.model
    def _check_ami_responsible(self):
        """ Checks if user is responsible for this request
        @return: Dictionary of values
        """
        flag_poject_manager = self.env['res.users'].has_group('project.group_project_manager')
        flag_project_user = self.env['res.users'].has_group('project.group_project_user')
        for each in self:

            if flag_poject_manager:
                each.get_user = True
            elif flag_project_user:
                each.get_user = False
            else:
                each.get_user = False

    get_user = fields.Boolean(string='Is Top User', compute=_check_ami_responsible)
    done_time=fields.Datetime(compute='done_date',string="Color")
    progress1 = fields.Integer(string="Working Time Progress(%)", copy=False, readonly=True)

    deadline_color = fields.Char(compute='compute_color',)
    task_time = fields.Float(string="Time Range", copy=True)
    date_deadline_ex = fields.Datetime('Deadline', select=True, copy=False, required=True)
    kanban_state = fields.Selection(
        [('normal', 'In Progress'), ('blocked', 'Blocked'), ('done', 'Ready for next stage')], 'Kanban State',
        track_visibility='onchange',
        help="A task's kanban state indicates special situations affecting it:\n"
             " * Normal is the default situation\n"
             " * Blocked indicates something is preventing the progress of this task\n"
             " * Ready for next stage indicates the task is ready to be pulled to the next stage",
        required=False, copy=False)

    _defaults = {
        'get_user': True,
    }

    def compute_color(self):

        obj = self.env['project.task']
        obj1 = obj.search([])
        now = fields.Datetime.from_string(fields.Datetime.now())
        for obj2 in obj1:

            obj3 = obj2
            if obj3.stage_id.name != 'Done' and obj3.stage_id.name != 'Cancelled' and obj3.stage_id.name != 'Verified':

                end_date = fields.Datetime.from_string(obj3.date_deadline_ex)

                deadline_count = relativedelta(end_date, now)
                if deadline_count.seconds < 0:
                   obj3.deadline_color = 'red'
                else:
                    obj3.deadline_color = 'nothing'

            elif obj3.stage_id.name == 'Done' or obj3.stage_id.name == 'Verified':

                if obj3.progress1 < 100:
                        obj3.deadline_color = 'green'
                else:
                        obj3.deadline_color = 'red'

    def process_demo_scheduler_queue(self):

        obj = self.env['project.task']
        obj1 = obj.search([])
        now = fields.Datetime.from_string(fields.Datetime.now())
        for obj2 in obj1:
            obj3 = obj2
            if obj3.stage_id.name != 'Done' and obj3.stage_id.name != 'Cancelled' and obj3.stage_id.name != 'Verified':
                start_date = fields.Datetime.from_string(obj3.date_assign)
                end_date = fields.Datetime.from_string(obj3.date_deadline_ex)
                if obj3.date_deadline_ex and obj3.date_assign and end_date > start_date:
                    if now < end_date:
                        dif_tot = relativedelta(end_date, start_date)
                        dif_minut = dif_tot.hours * 60 + dif_tot.minutes
                        diff1 = end_date - start_date
                        total_minut = int(diff1.days) * 24 * 60 + dif_minut
                        dif2_tot = relativedelta(now, start_date)
                        dif2_minut = dif2_tot.hours * 60 + dif2_tot.minutes
                        diff2 = now - start_date
                        used_minut = int(diff2.days) * 24 * 60 + dif2_minut
                        if total_minut != 0:
                            obj3.progress1 = ((used_minut * 100) / total_minut)
                        else:
                            obj3.progress1 = 100
                    else:
                        obj3.progress1 = 100
                else:
                    obj3.progress1 = 0

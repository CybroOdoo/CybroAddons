from openerp import models, fields, api, _, tools


class ProjectTaskInherit(models.Model):
    _inherit = 'project.task'

    user_id = fields.Many2one('res.users', 'Assigned to', select=True, track_visibility='onchange',
                              domain=[('active', '=', 'True'), ('partner_id.active', '=', 'True')])
    reviewer_id = fields.Many2one('res.users', 'Reviewer', select=True, track_visibility='onchange',
                                  domain=[('active', '=', 'True'), ('partner_id.active', '=', 'True')])
    partner_id = fields.Many2one('res.partner', 'Customer', domain=[('active', '=', 'True')])


class ProjectProjectInherit(models.Model):
    _inherit = 'project.project'

    user_id = fields.Many2one('res.users', 'Project Manager',
                              domain=[('active', '=', 'True'), ('partner_id.active', '=', 'True')])
    members = fields.Many2many('res.users', 'project_user_rel', 'project_id', 'uid', 'Project Members',
                               help="Project's members are users who can have an access to the tasks related to this project.",
                               states={'close': [('readonly', True)], 'cancelled': [('readonly', True)]},
                               domain=[('active', '=', 'True'), ('partner_id.active', '=', 'True')])


class ProjectIssueInherit(models.Model):
    _inherit = 'project.issue'

    user_id = fields.Many2one('res.users', 'Assigned to', required=False, select=1, track_visibility='onchange',
                              domain=[('active', '=', 'True'), ('partner_id.active', '=', 'True')])
    partner_id = fields.Many2one('res.partner', 'Contact', select=1,
                                 domain=[('active', '=', 'True')])


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    user_id = fields.Many2one('res.users', string='User', default=_default_user,
                              domain=[('active', '=', 'True'), ('partner_id.active', '=', 'True')])


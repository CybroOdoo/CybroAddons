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
from odoo import api, fields, models, _


class HrEmployee(models.Model):
    """ Inherited model for adding announcement features to employee model. """
    _inherit = 'hr.employee'

    announcement_count = fields.Integer(
        compute='_compute_announcement_count',
        string='# Announcements',
        help="Count of Announcements")

    def _get_announcement_domain(self, now_date):
        """Returns domain to fetch all relevant announcements for the employee."""
        return [
            ('state', 'in', ('approved', 'done')),
            ('date_start', '<=', now_date),
            '|', '|', '|',
            ('is_announcement', '=', True),
            ('employee_ids', 'in', self.id),
            ('department_ids', 'in', self.department_id.id),
            ('position_ids', 'in', self.job_id.id),
        ]

    @api.depends('department_id', 'job_id')
    def _compute_announcement_count(self):
        """Compute announcement count for each employee."""
        now_date = fields.Date.today()
        for obj in self:
            announcements = self.env['hr.announcement'].sudo().search(
                obj._get_announcement_domain(now_date))
            obj.announcement_count = len(announcements)

    def action_announcement_view(self):
        """Announcement view for each employee."""
        now_date = fields.Date.today()
        announcement_ids = self.env['hr.announcement'].sudo().search(
            self._get_announcement_domain(now_date)).ids
        view_id = self.env.ref(
            'ent_hr_reward_warning.hr_announcement_view_form').id
        if announcement_ids:
            if len(announcement_ids) > 1:
                return {
                    'domain': [('id', 'in', announcement_ids)],
                    'view_mode': 'list,form',
                    'res_model': 'hr.announcement',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Announcements'),
                }
            else:
                return {
                    'view_mode': 'form',
                    'res_model': 'hr.announcement',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Announcements'),
                    'res_id': announcement_ids[0],
                }

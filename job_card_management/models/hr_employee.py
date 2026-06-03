# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
################################################################################
from odoo import models, fields


class HrEmployee(models.Model):
    """Inheriting the model for adding new field"""
    _inherit = "hr.employee"

    workshop_position = fields.Selection([('leader', 'Leader'), ('worker', 'Worker')],
                                         help="Work shop position of Employee",
                                         string='Workshop Position')


class ProjectTask(models.Model):
    """Inheriting the model for adding new field"""
    _inherit = 'project.task'

    job_card_id = fields.Many2one('job.card', help="Job Card ID",
                                  string='Job Card ID')


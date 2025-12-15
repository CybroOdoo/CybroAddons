# -*- coding: utf-8 -*-
###################################################################################
#    Job Card Management
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Manasa T P (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import models, fields


class HrEmployee(models.Model):
    """Inherit the model hr employee"""
    _inherit = "hr.employee"

    workshop_position = fields.Selection([('leader', 'Leader'), ('worker', 'Worker')], string="Workshop Position")


class ProjectTask(models.Model):
    _inherit = 'project.task'

    job_card_id = fields.Many2one('job.card', string="Job Card")


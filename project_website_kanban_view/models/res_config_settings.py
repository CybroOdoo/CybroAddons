# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """
    This class extends the 'res.config.settings' model to add a new
    configuration parameter for controlling the number of tasks per page in the
    kanban view.
    """
    _inherit = 'res.config.settings'

    task_per_pager = fields.Integer(
        string="Tasks per page in Kanban View",
        help="Number of tasks per page in the website portal Kanban view.",
        config_parameter='project_website_kanban_view.task_per_pager')

    @api.constrains('task_per_pager')
    def _check_task_per_pager(self):
        for record in self:
            if record.task_per_pager <= 0:
                raise ValidationError(
                    _("Task per page cannot be 0. Please configure a valid value.")
                )
    
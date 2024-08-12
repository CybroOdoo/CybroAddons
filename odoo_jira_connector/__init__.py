# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya B (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from . import controllers, models
from odoo.exceptions import UserError


def pre_init_hook(env):
    queue_job = env['ir.model.data'].sudo().search(
        [('module', '=', 'queue_job')])
    queue_job_cron_jobrunner = env['ir.model.data'].search(
        [('module', '=', 'queue_job_cron_jobrunner')])
    if not queue_job_cron_jobrunner or not queue_job:
        raise UserError("Please make sure you have added and installed Queue "
                        "Job and Queue Job Cron Jobrunner in your system")

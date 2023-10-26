# -*- coding: utf-8 -*-
################################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Ayana K P (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """ This is an Odoo model for system configuration settings related to
    overdue task notifications. It inherits from the 'res.config.settings'
    model and adds boolean and integer fields for configuring
    overdue task notifications. """

    _inherit = "res.config.settings"

    notification = fields.Boolean(string="Overdue Notification",
                                  config_parameter='task_overdue_email_odoo'
                                  '.notification',help="Enable this will allow "
                                  "to send task overdue notifications")
    overdue_days = fields.Integer(
        string="Overdue Days :", config_parameter='task_overdue_email_odoo'
        '.overdue_days',help="specify how many days overdue a task  must be "
        "before a notification is sent.")

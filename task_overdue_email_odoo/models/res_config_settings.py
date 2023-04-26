# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
#
################################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """This is an Odoo model for system configuration settings related to overdue
    task notifications. It inherits from the 'res.config.settings' model and adds
    boolean and integer fields for configuring overdue task notifications."""

    _inherit = "res.config.settings"

    notification = fields.Boolean(string="Overdue Notification",
                                  help="The string parameter specifies the label or name of the field as it will appear in the user interface (in this case, ""Overdue Notification")
    overdue_days = fields.Integer(string="Overdue Days :",
                                  help="specify how many days overdue a task  must be before a notification is sent.")

    def set_values(self):
        """Overrides the default `set_values` method of the `res.config.settings` model to save the current
        values of the `notification` and `overdue_days` fields to the corresponding configuration parameters in the
        database."""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'task_overdue_email_odoo.notification', self.notification)
        self.env['ir.config_parameter'].set_param(
            'task_overdue_email_odoo.overdue_days', self.overdue_days)

    @api.model
    def get_values(self):
        """Overrides the default `get_values` method of the `res.config.settings` model to retrieve the current
        values of the `notification` and `overdue_days` fields from the corresponding configuration parameters in the
        database.
        """
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            notification=params.get_param('task_overdue_email_odoo.notification'),
            overdue_days=params.get_param('task_overdue_email_odoo.overdue_days')
        )
        return res

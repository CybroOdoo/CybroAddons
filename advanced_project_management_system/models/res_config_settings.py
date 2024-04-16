# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """ Added document expiry notification expiry mail details """
    _inherit = "res.config.settings"

    is_project_category = fields.Boolean(
        string='Enable Project Category',
        help="Enabling project category",
        config_parameter='advanced_project_management_system.is_project_category')
    document_expiry_notification = fields.Boolean(
        string='Document Expiry Notification',
        help="For sending document expiry notification",
        config_parameter='advanced_project_management_system.document_expiry_notification')
    notify_customer = fields.Boolean(
        string='Notify Customer',
        help="For notifying the customer",
        config_parameter='advanced_project_management_system.notify_customer')
    on_expiry_notification = fields.Boolean(
        string='On Expiry Date Notification', help="Sent expiry notification",
        config_parameter='advanced_project_management_system.on_expiry_notification')
    email = fields.Char(
        string='Notify Email to', help="Get email id",
        config_parameter='advanced_project_management_system.email')
    notify_days = fields.Integer(
        string='Notify After Expiry Date',
        help="Notification sent before these days",
        config_parameter='advanced_project_management_system.notify_days')
    is_overdue_notification = fields.Boolean(
        string='Overdue Notification?',
        help="For sending overdue notification",
        config_parameter='advanced_project_management_system.is_overdue_notification')
    notification_before = fields.Integer(
        string='Notification Days',
        help="Sent notification before these days",
        config_parameter='advanced_project_management_system.notification_before')

    @api.onchange('is_project_category')
    def _onchange_is_project_category(self):
        """Handles the addition or removal of the current user from the
        `group_project_category` based on the state of `is_project_category`."""
        groups = self.env.ref(
            'advanced_project_management_system.group_project_category')
        if self.is_project_category:
            groups.write({'users': [(4, self.env.user.id)]})
        else:
            groups.write({'users': [(3, self.env.user.id)]})

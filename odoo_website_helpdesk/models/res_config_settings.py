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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Helpdesk settings"""
    _inherit = 'res.config.settings'

    show_create_task = fields.Boolean(
        string="Create Tasks",
        config_parameter='odoo_website_helpdesk.show_create_task',
        help='Allow the users to create project tasks from the tickets.')
    group_show_category = fields.Boolean(
        string="Category",
        implied_group='odoo_website_helpdesk.group_show_category',
        help='Categorize the tickets.')
    product_website = fields.Boolean(
        string="Product On Website",
        config_parameter='odoo_website_helpdesk.product_website',
        help='Let the customers choose the products of the ticket in the '
             'website form.')
    auto_close_ticket = fields.Boolean(
        config_parameter='odoo_website_helpdesk.auto_close_ticket',
        help='Close the tickets automatically after a number of days.')
    no_of_days = fields.Integer(
        config_parameter='odoo_website_helpdesk.no_of_days',
        help='Number of days after which the open tickets are closed.')
    closed_stage_id = fields.Many2one(
        'ticket.stage', string='Closing stage',
        help='Stage of the closed tickets.')
    reply_template_id = fields.Many2one(
        'mail.template',
        domain="[('model', '=', 'ticket.helpdesk')]",
        config_parameter='odoo_website_helpdesk.reply_template_id',
        help='Template proposed when replying to a ticket.')
    helpdesk_menu_show = fields.Boolean(
        'Helpdesk Menu',
        config_parameter='odoo_website_helpdesk.helpdesk_menu_show',
        help='Show the Helpdesk menu on the website.')

    @api.model
    def get_values(self):
        """The closing stage is the stage marked as closing"""
        values = super().get_values()
        values['closed_stage_id'] = self.env['ticket.stage'].search(
            [('closing_stage', '=', True)], limit=1).id
        return values

    def set_values(self):
        """Mark the selected stage as the only closing stage"""
        result = super().set_values()
        if self.closed_stage_id:
            stages = self.env['ticket.stage'].search(
                [('closing_stage', '=', True),
                 ('id', '!=', self.closed_stage_id.id)])
            stages.closing_stage = False
            self.closed_stage_id.closing_stage = True
        return result

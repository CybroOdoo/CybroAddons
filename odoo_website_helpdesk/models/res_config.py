# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class Menu(models.Model):
    """Inheriting the website menu"""
    _inherit = "website.menu"

    def _compute_visible(self):
        """Compute visible"""
        super()._compute_visible()
        show_menu_header = self.env['ir.config_parameter'].sudo().get_param(
            'odoo_website_helpdesk.helpdesk_menu_show')
        for menu in self:
            if menu.name == 'Helpdesk' and show_menu_header == False:
                menu.is_visible = False
            if menu.name == 'Helpdesk' and show_menu_header == True:
                menu.is_visible = True


class Helpdesk(models.TransientModel):
    """Inheriting the res config"""
    _inherit = 'res.config.settings'

    show_create_task = fields.Boolean(string="Create Tasks",
                                      config_parameter='odoo_website_helpdesk.show_create_task',
                                      help='Create Task')
    show_category = fields.Boolean(string="Category",
                                   config_parameter='odoo_website_helpdesk.show_category',
                                   help='Category',
                                   implied_group='odoo_website_helpdesk.group_show_category')
    product_website = fields.Boolean(string="Product On Website",
                                     config_parameter='odoo_website_helpdesk.product_website',
                                     help='Product on website')
    auto_close_ticket = fields.Boolean(string="Auto Close Ticket",
                                       config_parameter='odoo_website_helpdesk.auto_close_ticket',
                                       help='Auto Close ticket')
    no_of_days = fields.Integer(string="No Of Days",
                                config_parameter='odoo_website_helpdesk.no_of_days',
                                help='No of Days')
    closed_stage = fields.Many2one(
        'ticket.stage', string='Closing stage',
        help='Closing Stage',
        config_parameter='odoo_website_helpdesk.closed_stage')

    reply_template_id = fields.Many2one('mail.template',
                                        domain="[('model', '=', 'help.ticket')]",
                                        config_parameter='odoo_website_helpdesk.reply_template_id',
                                        help='Reply Template')
    helpdesk_menu_show = fields.Boolean('Helpdesk Menu',
                                        config_parameter=
                                        'odoo_website_helpdesk.helpdesk_menu_show',
                                        help='Helpdesk menu')

    @api.onchange('closed_stage')
    def closed_stage_a(self):
        """Closing stage function"""
        if self.closed_stage:
            stage = self.closed_stage.id
            in_stage = self.env['ticket.stage'].search([('id', '=', stage)])
            not_in_stage = self.env['ticket.stage'].search([('id', '!=', stage)])
            in_stage.closing_stage = True
            for each in not_in_stage:
                each.closing_stage = False

    @api.constrains('show_category')
    def show_category_subcategory(self):
        """Show category and the sub category"""
        if self.show_category:
            group_cat = self.env.ref(
                'odoo_website_helpdesk.group_show_category')
            group_cat.write({
                'users': [(4, self.env.user.id)]
            })
        else:
            group_cat = self.env.ref(
                'odoo_website_helpdesk.group_show_category')
            group_cat.write({
                'users': [(5, False)]
            })

# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """ Inherits res.config.settings to add new setting for enabling cusomer
    ratings and displaying records in portal. """
    _inherit = 'res.config.settings'

    comment_configuration = fields.Boolean(
        config_parameter='all_in_one_website_kit.comment_configuration',
        string='Comment Configuration', help='Enable/ Disable the feature.')
    is_show_recent_so_q = fields.Boolean(
        string='Is show recent quotation and sale order table',
        config_parameter='all_in_one_website_kit.is_show_recent_so_q',
        help="Enable the field for show the recent quotation and"
             "sale order table ")
    sale_count = fields.Integer(
        string='How many recent records do you want to show?',
        config_parameter='all_in_one_website_kit.sale_count',
        help="The field shows the number of recent records want to show")
    is_show_recent_po_rfq = fields.Boolean(
        string='Is show recent RFQ table?',
        config_parameter='all_in_one_website_kit.is_show_recent_po_rfq',
        help="Enable the field to show the recent RFQ table.")
    purchase_count = fields.Integer(
        string='How many recent records do you want to show?',
        config_parameter='all_in_one_website_kit.purchase_count',
        help="The field shows the number of purchase records want to show.")
    is_show_project = fields.Boolean(
        string='Is show project task table?',
        config_parameter='all_in_one_website_kit.is_show_project',
        help="Enable the field to show the project task table.")
    project_count = fields.Integer(
        string='How many recent records do you want to show?',
        config_parameter='all_in_one_website_kit.project_count',
        help="The field shows the recent project records want to show.")
    is_show_recent_invoice_bill = fields.Boolean(
        string='Is show recent invoice/bill table?',
        config_parameter='all_in_one_website_kit.is_show_recent_invoice_bill',
        help="Enable the field to show the recent invoice/bill.")
    account_count = fields.Integer(
        string='How many recent records do you want to show?',
        config_parameter='all_in_one_website_kit.account_count',
        help="The field shows the number of recent invoice/bill records"
             "want to show.")

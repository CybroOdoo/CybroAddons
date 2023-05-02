# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Megha A P (odoo@cybrosys.com)
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """This class is used to inherit settings and add some fields to get
    number of count of data that needs to
    show in the dashboard"""
    _inherit = 'res.config.settings'

    is_show_recent_so_q = fields.Boolean(
        string='Is show recent quotation and sale order table',
        config_parameter='portal_dashboard.is_show_recent_so_q')
    sale_count = fields.Integer(
        string='How many recent records do you want to show?',
        config_parameter='portal_dashboard.sale_count')
    is_show_recent_po_rfq = fields.Boolean(
        string='Is show recent RFQ table?',
        config_parameter='portal_dashboard.is_show_recent_po_rfq')
    purchase_count = fields.Integer(
        string='How many recent records do you want to show?',
        config_parameter='portal_dashboard.purchase_count')
    is_show_project = fields.Boolean(
        string='Is show project task table?',
        config_parameter='portal_dashboard.is_show_project')
    project_count = fields.Integer(
        string='How many recent records do you want to show?',
        config_parameter='portal_dashboard.project_count')
    is_show_recent_invoice_bill = fields.Boolean(
        string='Is show recent invoice/bill table?',
        config_parameter='portal_dashboard.is_show_recent_invoice_bill')
    account_count = fields.Integer(
        string='How many recent records do you want to show?',
        config_parameter='portal_dashboard.account_count')

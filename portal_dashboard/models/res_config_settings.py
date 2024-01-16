# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICis_show_recent_invoice_billENSE (AGPL v3) for
#    more details.
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
        string='Show recent quotation and sale order table',
        config_parameter='portal_dashboard.is_show_recent_so_q',
        help="Does need to show the  recent quotation and sale order table in "
             "dashboard")
    sale_count = fields.Integer(
        string='How many sale orders do you want to show?',
        config_parameter='portal_dashboard.sale_count',
        help="Count of recent sales records need to show")
    is_show_recent_po_rfq = fields.Boolean(
        string='Show recent RFQ table?',
        config_parameter='portal_dashboard.is_show_recent_po_rfq',
        help="Does need to show the recently created RFQ table")
    purchase_count = fields.Integer(
        string='How many purchase orders do you want to show?',
        config_parameter='portal_dashboard.purchase_count',
        help="Count of recent purchase records need to show")
    is_show_project = fields.Boolean(
        string='Show project task table?',
        config_parameter='portal_dashboard.is_show_project',
        help="Does need to show the show project tasks")
    project_count = fields.Integer(
        string="How many project's do you want to show?",
        config_parameter='portal_dashboard.project_count',
        help="Count of recent project records to show")
    is_show_recent_invoice_bill = fields.Boolean(
        string='Show recent invoice/bill table?',
        config_parameter='portal_dashboard.is_show_recent_invoice_bill',
        help="Does the recent invoice/bill table need to be shown")
    account_count = fields.Integer(
        string='How many invoices do you want to show?',
        config_parameter='portal_dashboard.account_count',
        help="How much recent account's need to be shown")

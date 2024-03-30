# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import exceptions
from odoo import api, fields, models, _


class CrmCommission(models.Model):
    """
    This class represents the Commission Plan.
    """
    _name = 'crm.commission'
    _description = 'CRM Commission'
    _rec_name = "name"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True, help="Name of the Commission")
    active = fields.Boolean('Active', default=True, help="Active")
    date_from = fields.Date(string="From Date", required=True, help="Date from")
    date_to = fields.Date(string="To Date", required=True, help="Date to")
    type = fields.Selection(
        [('product', 'Product wise'),
         ('revenue', 'Revenue wise')], string="Type",
        default="product", help='Type of the commission plan')
    team_id = fields.Many2one('crm.team', string='Sales Team',
                              help="CRM Team")
    user_id = fields.Many2one('res.users', string='Salesperson',
                              help="Sales person")
    product_comm_ids = fields.One2many('commission.product', 'commission_id',
                                       string="Product Wise",
                                       help='Commission Product')
    straight_commission_rate = fields.Float(string='Commission rate (%)',
                                            help='Straight Commission Rate')
    revenue_grd_comm_ids = fields.One2many(
        'commission.graduated',
        'commission_id',
        string="Revenue Graduated Wise", help='Revenue graduated wise')

    revenue_type = fields.Selection(
        [('straight', 'Straight Commission'),
         ('graduated', 'Graduated Commission')],
        string="Revenue Type", help='Revenue Type')

    @api.constrains("date_from", "date_to")
    def _check_date(self):
        """
        Check the validity of date range.

        This method checks whether the 'date_from' is not later than 'date_to'.

        :raise exceptions.ValidationError: If 'date_from' is later than 'date_to'.
        """
        for rec in self:
            if rec.date_to < rec.date_from:
                raise exceptions.ValidationError(
                    _("The From date cannot be earlier than To date.")
                )

    @api.onchange('type')
    def _onchange_type(self):
        """
        Handle the 'type' field change.
        This method handles the 'type' field change and performs actions
        accordingly.
        """
        if self.type == 'revenue':
            self.product_comm_ids = [(5, 0, 0)]
        elif self.type == 'product':
            self.revenue_type = False
            self.straight_commission_rate = False
            self.revenue_grd_comm_ids = [(5, 0, 0)]

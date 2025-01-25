# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V (odoo@cybrosys.com)
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
import datetime
from odoo import api, fields, models


class AccountMove(models.Model):
    """Inherited model 'account.move' """
    _inherit = 'account.move'

    @api.onchange('fee_structure_id')
    def _onchange_fee_structure(self):
        """Set default fee lines based on selected fee structure"""
        for item in self:
            lines = []
            for line in item.fee_structure_id.fee_type_ids:
                name = line.fee_type_id.product_variant_id.description_sale
                if not name:
                    name = line.fee_type_id.product_variant_id.name
                fee_line = {
                    'price_unit': line.fee_amount,
                    'quantity': 1.00,
                    'product_id': line.fee_type_id.product_variant_id,
                    'name': name,
                    'account_id': item.journal_id.default_account_id
                }
                lines.append((0, 0, fee_line))
            item.invoice_line_ids = lines

    @api.onchange('student_id', 'fee_category_id', 'payed_from_date',
                  'payed_to_date')
    def _onchange_student_id(self):
        """Student_id is inherited from res_partner. Set partner_id from
         student_id """
        self.ensure_one()
        lines = []
        for item in self:
            item.invoice_line_ids = lines
            item.partner_id = item.student_id.partner_id
            item.class_division_id = item.student_id.class_division_id
            date_today = datetime.date.today()
            company = self.env.user.company_id
            from_date = item.payed_from_date
            to_date = item.payed_to_date
            if not from_date:
                from_date = company.compute_fiscalyear_dates(date_today)[
                    'date_from']
            if not to_date:
                to_date = date_today
            if item.partner_id and item.fee_category_id:
                invoice_ids = self.env['account.move'].search([
                    ('partner_id', '=', item.partner_id.id),
                    ('invoice_date', '>=', from_date),
                    ('invoice_date', '<=', to_date),
                    ('fee_category_id', '=', item.fee_category_id.id)])
                for invoice in invoice_ids:
                    for line in invoice.invoice_line_ids:
                        fee_line = {
                            'price_unit': line.price_unit,
                            'quantity': line.quantity,
                            'product_id': line.product_id,
                            'price_subtotal': line.price_subtotal,
                            'tax_ids': line.tax_ids,
                            'discount': line.discount,
                            'receipt_no': line.move_name,
                            'date': line.move_id.invoice_date,
                        }
                        lines.append((0, 0, fee_line))
                item.payed_line_ids = lines

    @api.onchange('fee_category_id')
    def _onchange_fee_category_id(self):
        """ Set domain for fee structure based on category"""
        self.invoice_line_ids = None
        return {
            'domain': {
                'fee_structure_id': [
                    ('category_id', '=', self.fee_category_id.id)]

            }
        }

    @api.onchange('fee_category_id')
    def _onchange_fee_category_id(self):
        """Function to get category details"""
        for item in self:
            if item.fee_category_id:
                line = self.fee_category_id.journal_id
                item.journal_id = line

    journal_id = fields.Many2one('account.journal', string='Journal',
                                 required=True, help="Corresponding journal "
                                                     " stores every details of "
                                                     "your transaction.")
    student_id = fields.Many2one('education.student',
                                 string='Admission No', help='Student admission'
                                                             ' number.')
    student_name = fields.Char(string='Name',
                               related='student_id.partner_id.name', store=True,
                               help='Name of student.')
    class_division_id = fields.Many2one('education.class.division',
                                        string='Class', help='Class of the'
                                                             ' student.')
    fee_structure_id = fields.Many2one('education.fee.structure',
                                       string='Fee Structure',
                                       help='Fee structure')
    is_fee = fields.Boolean(string='Is Fee', store=True, default=False,
                            help='Fees boolean to specify whether fee or not.')
    fee_category_id = fields.Many2one('education.fee.category',
                                      string='Category',
                                      help='Category of fees.')
    is_fee_structure = fields.Boolean(string='Have a fee structure?',
                                      related='fee_category_id.fee_structure',
                                      help='Whether fee structure exists.')
    payed_line_ids = fields.One2many('account.move.line', 'partner_id',
                                     string='Payments Done',
                                     readonly=True, store=False,
                                     help='Payment lines.')
    payed_from_date = fields.Date(string='From Date',
                                  help='From date corresponding to the payment')
    payed_to_date = fields.Date(string='To Date',
                                help='To date corresponding to the payment')
    account_id = fields.Many2one('account.account', string='Account',
                                 index=True, ondelete="cascade",
                                 domain="[('deprecated', '=', False),"
                                        " ('company_id', '=', 'company_id')"
                                        ",('is_off_balance', '=', False)]",
                                 check_company=True,
                                 tracking=True, help='Account of '
                                                     'transaction.')
    partner_id = fields.Many2one('res.partner',
                                 string='Partner', help='Partner responsible.')

    @api.model
    def create(self, vals):
        """ Adding two field to invoice. is_fee use to display fee items only
        in fee tree view"""
        partner = self.env['res.partner'].browse(vals.get('partner_id'))
        if vals.get('fee_category_id'):
            vals.update({
                'is_fee': True,
                'student_name': partner.name
            })
        return super().create(vals)

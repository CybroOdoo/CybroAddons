# -*- coding: utf-8 -*-
###############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import io
import json
from datetime import date, datetime
from odoo import api, Command, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
from odoo.tools.misc import xlsxwriter


class TenderManagement(models.Model):
    """ Class for holding tender details. """
    _name = "tender.management"
    _inherit = 'mail.thread'
    _description = 'Tender Management'

    name = fields.Char('Name', required=True, help='Enter the name of the tender.')
    responsible_id = fields.Many2one('res.users', string="Responsible", required=True,
                                     help='Select the person responsible for managing this tender.')
    tender_start_date = fields.Date(string="Tender Start Date", required=True,
                                    help='Specify the date when the tender starts.')
    tender_end_date = fields.Date(string="Tender End Date", required=True,
                                  help='Specify the date when the tender ends.')
    bid_start_date = fields.Date(string="Bid Start Date", required=True,
                                 help='Indicate the start date for accepting bids.')
    bid_end_date = fields.Date(string="Bid End Date", required=True,
                               help='Indicate the deadline for submitting bids.')
    description = fields.Html(string='Description', required=True,
                              help='Provide a detailed description of the tender.')
    tender_category_id = fields.Many2one('tender.category', string="Tender Category", required=True,
                                         help='Select the category that best describes this tender.')
    tender_type = fields.Selection(
        [('single_vendor', 'Single vendor'), ('product_wise_vendor', 'Product wise vendor')],
        string="Tender Type", required=True,
        help='Choose whether the tender is for a single vendor or requires product-wise vendors.')
    address_street = fields.Char(string='Street', required=True, help='Enter the street address related to the tender.')
    address_city = fields.Char(string='City', required=True, help='Enter the city where the tender is located.')
    address_country_id = fields.Many2one('res.country', string='Country', required=True,
                                         help='Select the country where the tender is based.')
    address_state_id = fields.Many2one('res.country.state', string='State', required=True,
                                       help='Select the state or region where the tender is based.')
    tender_product_line_ids = fields.One2many('tender.product.lines', 'tender_id',
                                              help='List of product lines included in this tender.')
    tender_state = fields.Selection(
        [('draft', 'DRAFT'), ('confirm', 'CONFIRM'), ('bid_submission', 'BID SUBMISSION'),
         ('bid_evaluation', 'BID EVALUATION'), ('bid_selection', 'BID SELECTION'),
         ('close', 'CLOSE'), ('cancel', 'CANCEL')],
        default='draft', help='Current status of the tender process.')
    all_bid_count = fields.Integer(compute="_compute_all_bid_count",
                                   help='Total number of bids received for this tender.')
    qualified_bid_count = fields.Integer(compute="_compute_qualified_bid_count",
                                         help='Total number of qualified bids for this tender.')
    evaluation_bid_count = fields.Integer(compute="_compute_evaluation_bid_count",
                                          help='Total number of bids under evaluation.')
    registered_vendors_ids = fields.Many2many('res.partner', string="Registered Vendors",
                                              help='Vendors registered to participate in this tender.')
    legit_bid_count = fields.Integer(compute="_compute_legit_bid_count",
                                     help='Total number of legitimate bids received for this tender.')
    best_bid_id = fields.Many2one('tender.bidding', string='Best Bid',
                                  help='The bid selected as the best option for this tender.')
    purchase_confirmed = fields.Boolean(default=False, help='Indicates whether the purchase has been confirmed.')
    tender_purchase_count = fields.Integer(compute='_compute_tender_purchase_count',
                                           help='Number of purchase orders confirmed for this tender.')
    tender_file_ids = fields.One2many('tender.document', 'tender_id', string="Tender Files", required=True,
                                      help='Upload and manage tender-related documents.')
    purchase_order_ids = fields.Many2many('purchase.order',
                                          help='Purchase orders associated with this tender.')

    def _compute_evaluation_bid_count(self):
        """Computes the count of all evaluation bids for product-wise vendor"""
        for rec in self:
            rec.evaluation_bid_count = self.env['tender.bidding'].search_count(
                [('tender_id', '=', rec.id), ('qualification_stage', '=', 'qualified')])

    def _compute_all_bid_count(self):
        """Computes the count of all bids received for the tender"""
        for rec in self:
            rec.all_bid_count = self.env['tender.bidding'].search_count([('tender_id', '=', rec.id)])

    def _compute_qualified_bid_count(self):
        """Computes the count of all qualified bids for the tender"""
        for rec in self:
            rec.qualified_bid_count = self.env['tender.bidding'].search_count(
                [('qualification_stage', '=', 'qualified'), ('tender_id', '=', rec.id)])

    def _compute_tender_purchase_count(self):
        """Computes the purchase count for current tender"""
        for rec in self:
            rec.tender_purchase_count = self.env['purchase.order'].search_count([('tender_id', '=', rec.id)])

    def _compute_legit_bid_count(self):
        """Computes the count of legit bid for single vendor tender"""
        for rec in self:
            rec.legit_bid_count = self.env['tender.bidding'].search_count(
                [('legit_bid', '=', True), ('tender_id', '=', rec.id), ('qualification_stage', '=', 'qualified')])

    @api.constrains('tender_start_date', 'tender_end_date')
    def _check_tender_date_range(self):
        """Function to validate tender dates"""
        for record in self:
            if record.tender_end_date and record.tender_start_date and record.tender_end_date < record.tender_start_date:
                raise ValidationError(_('Error! Tender End Date must be greater than Tender Start Date.'))

    @api.constrains('bid_start_date', 'bid_end_date')
    def _check_bid_date_range(self):
        """Function to validate bid dates"""
        for record in self:
            if record.bid_end_date and record.bid_start_date and record.bid_end_date < record.bid_start_date:
                raise ValidationError(_('Error! Bid End Date must be greater than Bid Start Date.'))

    def get_tender_details(self):
        """Function to return stock valuation details ,orm call from dashboard js"""
        tenders = self.env['tender.management'].search([])
        bidding = self.env['tender.bidding'].search([])
        tender_categories = self.env['tender.category'].search([])
        tender_types = dict(self._fields['tender_type'].selection)
        return {
            'tender_count': len(tenders),
            'vendors_count': self.env['res.partner'].search_count([('is_vendor', '=', 'True')]),
            'active_tenders_count': len(tenders.filtered(lambda rec: rec.tender_state == 'bid_submission')),
            'tender_category_data': {'category_types': tender_categories.mapped('name'),
                                     'category_type_count': [tenders.search_count([('tender_category_id', '=', rec)])
                                                             for rec in tender_categories.mapped('id')]
                                     },
            'tender_location_count': len(tenders.mapped('address_country_id')),
            'tender_categories_count': len(tender_categories),
            'tender_type_data': {'tender_types': list(tender_types.values()),
                                 'tender_type_count': [tenders.search_count([('tender_type', '=', tender_type)]) for
                                                       tender_type in tender_types.keys()]
                                 },
            'tender_timeline_data': {
                'tenders': tenders.mapped('name'),
                'tender_timeline_data': [(rec.tender_end_date - rec.tender_start_date).days for rec in tenders]

            },
            'active_bid_count': len(bidding.filtered(lambda rec: rec.bidding_state == 'bid_close')),
            'qualified_bid_count': len(bidding.filtered(lambda rec: rec.qualification_stage == 'qualified')),
            'disqualified_bid_count': len(bidding.filtered(lambda rec: rec.qualification_stage == 'disqualified')),
            'edit_request_count': len(bidding.filtered(lambda rec: rec.edit_request == True)),
            'pre_qualification_count': len(bidding.filtered(lambda rec: rec.qualification_stage == 'initial')),
        }

    def action_select_final_bid(self):
        """Function to select the best bid and return bid select/change wizard"""
        best_bid = self.env['tender.bidding'].search([('tender_id', '=', self.id)], order='total_bidding_amount asc',
                                                     limit=1)
        self.best_bid_id = best_bid.id
        return {
            'name': 'Bid Selection Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'bid.selection',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_current_tender_id': self.id, 'default_tender_bid_id': self.best_bid_id.id}
        }

    def action_get_purchase_order(self):
        """Function to return corresponding purchase order"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Single Vendor Purchase Order',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('tender_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def action_bid_evaluation(self):
        """Function to change tender state to bid evaluation stage"""
        self.tender_state = 'bid_evaluation'

    def action_confirm_tender(self):
        """Function to confirms the tender"""
        self.tender_state = 'confirm'

    def action_get_bids(self):
        """Function to returns all bids received for the tender"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'All Bids',
            'view_mode': 'tree,form',
            'res_model': 'tender.bidding',
            'domain': [('tender_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def action_get_qualified_bids(self):
        """Function to returns all qualified bids for the tender"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Qualified Bids',
            'view_mode': 'tree,form',
            'res_model': 'tender.bidding',
            'domain': [('qualification_stage', '=', 'qualified'), ('tender_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def action_get_legit_bids(self):
        """Function to returns all legit bids for single vendor tender"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Legit Bids',
            'view_mode': 'tree,form',
            'res_model': 'tender.bidding',
            'domain': [('qualification_stage', '=', 'qualified'), ('tender_id', '=', self.id),
                       ('legit_bid', '=', 'True')],
            'context': "{'create': False}"
        }

    def action_get_evaluation_bids(self):
        """Function to return evaluation bids"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Evaluation Bids',
            'view_mode': 'tree',
            'res_model': 'tender.bidding.product.lines',
            'domain': [('tender_id', '=', self.id), ('display_type', '=', False), ('bid_qualified', '=', 'qualified')],
            'context': {
                'create': False, "search_default_filter_group_by_product": 1
            },
            'target': 'current',
        }

    def action_confirm_bids(self):
        """Function to confirm selected product wise bids"""
        selected_bids = self.env['tender.bidding.product.lines'].search([('bid_status', '=', 'selected')])
        for rec in selected_bids:
            draft_purchase_order = self.env['purchase.order'].search(
                [('partner_id', '=', rec.vendor_id.id), ('state', '=', 'draft'), ('tender_id', '=', self.id)], limit=1)
            if draft_purchase_order:
                draft_purchase_order.write({
                    'order_line': [fields.Command.create({
                        'product_id': rec.product_id.id,
                        'product_qty': rec.product_qty,
                        'price_unit': rec.product_price,
                        'name': rec.name,
                    })]
                })
                self.update({'purchase_order_ids': [(fields.Command.link(draft_purchase_order.id))]})
            else:
                purchase_order = self.env['purchase.order'].create({
                    'partner_id': rec.vendor_id.id,
                    'partner_ref': rec.tender_bidding_id.name,
                    'date_order': datetime.today().now(),
                    'tender_id': self.id,
                    'order_line': [Command.create({
                        'product_id': rec.product_id.id,
                        'product_qty': rec.product_qty,
                        'price_unit': rec.product_price,
                        'name': rec.name,
                    })]
                })
                self.update({'purchase_order_ids': [(fields.Command.link(purchase_order.id))]})
            self.purchase_confirmed = True
        for rec in self.purchase_order_ids:
            template = self.env.ref('advanced_tender_management.purchase_order_confirmed_template').sudo()
            template.send_mail(rec.id, force_send=True)

    def action_tender_expiration(self):
        """Function to auto expire tenders based on tender start and end date"""
        tenders = self.env['tender.management'].search([('tender_state', '=', 'confirm')])
        today = date.today()
        for rec in tenders:
            if today == rec.bid_start_date:
                rec.tender_state = 'bid_submission'
            elif today > rec.bid_end_date:
                rec.tender_state = 'bid_evaluation'

    def action_import_tender_product_wizard(self):
        """Function to return wizard for importing product lines"""
        return {
            'name': 'Import Tender Product Lines',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'import.tender.product.line',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_print_xlsx_report(self):
        """Function for printing xlsx report"""
        data_list = [{
            'product_id': record.product_id.name,
            'name': record.name,
            'quantity': record.product_qty if record.product_id else record.product_qty,
            'units': record.product_uom_id.name
        } for record in self.tender_product_line_ids]

        data = {
            'model': 'tender.management',
            'tender_product_lines': data_list
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'tender.management',
                     'output_format': 'xlsx',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'report_name': 'Tender Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """Function to get xlsx data"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})
        column_names = ["Product", "Description", "Qty", "Unit of Measure"]
        for col_idx, col_name in enumerate(column_names):
            sheet.write(0, col_idx, col_name, txt)
        column_widths = [20, 30, 10, 20]
        for col_idx, width in enumerate(column_widths):
            sheet.set_column(col_idx, col_idx, width)
        row_num = 1
        for item in data['tender_product_lines']:
            col_idx = 0
            for key, value in item.items():
                if key == 'product_id' and not value:
                    sheet.write(row_num, col_idx, item['name'], txt)
                    break
                else:
                    sheet.write(row_num, col_idx, value, txt)
                    col_idx += 1
            row_num += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

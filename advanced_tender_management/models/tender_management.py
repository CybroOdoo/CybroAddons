# -*- coding: utf-8 -*-
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
import io

import xlsxwriter

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class TenderManagement(models.Model):
    """Tender: the products to buy, the dates and the bids received."""
    _name = "tender.management"
    _inherit = 'mail.thread'
    _description = 'Tender Management'

    # Number of most recent tenders shown in the dashboard timeline
    _DASHBOARD_LIMIT = 30

    name = fields.Char(required=True, help='Enter the name of the tender.')
    responsible_id = fields.Many2one('res.users', required=True,
                                     help='Select the person responsible for managing this tender.')
    tender_start_date = fields.Date(required=True,
                                    help='Specify the date when the tender starts.')
    tender_end_date = fields.Date(required=True,
                                  help='Specify the date when the tender ends.')
    bid_start_date = fields.Date(required=True,
                                 help='Indicate the start date for accepting bids.')
    bid_end_date = fields.Date(required=True,
                               help='Indicate the deadline for submitting bids.')
    description = fields.Html(required=True,
                              help='Provide a detailed description of the tender.')
    tender_category_id = fields.Many2one('tender.category', required=True,
                                         help='Select the category that best describes this tender.')
    tender_type = fields.Selection(
        [('single_vendor', 'Single vendor'), ('product_wise_vendor', 'Product wise vendor')],
        required=True,
        help='Choose whether the tender is for a single vendor or requires product-wise vendors.')
    address_street = fields.Char(string='Street', required=True,
                                 help='Enter the street address related to the tender.')
    address_city = fields.Char(string='City', required=True,
                               help='Enter the city where the tender is located.')
    address_country_id = fields.Many2one('res.country', string='Country', required=True,
                                         help='Select the country where the tender is based.')
    address_state_id = fields.Many2one('res.country.state', string='State', required=True,
                                       help='Select the state or region where the tender is based.')
    tender_product_line_ids = fields.One2many('tender.product.lines', 'tender_id',
                                              help='List of product lines included in this tender.')
    tender_state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'), ('bid_submission', 'Bid Submission'),
         ('bid_evaluation', 'Bid Evaluation'), ('bid_selection', 'Bid Selection'),
         ('close', 'Closed'), ('cancel', 'Cancelled')],
        default='draft', readonly=True, copy=False, tracking=True,
        help='Current status of the tender process.')
    all_bid_count = fields.Integer(compute="_compute_bid_counts",
                                   help='Total number of bids received for this tender.')
    qualified_bid_count = fields.Integer(compute="_compute_bid_counts",
                                         help='Total number of qualified bids for this tender.')
    evaluation_bid_count = fields.Integer(compute="_compute_bid_counts",
                                          help='Total number of bids under evaluation.')
    legit_bid_count = fields.Integer(compute="_compute_bid_counts",
                                     help='Total number of legitimate bids received for this tender.')
    registered_vendors_ids = fields.Many2many('res.partner',
                                              help='Vendors registered to participate in this tender.')
    best_bid_id = fields.Many2one('tender.bidding',
                                  help='The bid selected as the best option for this tender.')
    purchase_confirmed = fields.Boolean(default=False,
                                        help='Indicates whether the purchase has been confirmed.')
    tender_purchase_count = fields.Integer(compute='_compute_tender_purchase_count',
                                           help='Number of purchase orders confirmed for this tender.')
    tender_file_ids = fields.One2many('tender.document', 'tender_id', string="Tender Files",
                                      required=True,
                                      help='Upload and manage tender-related documents.')
    purchase_order_ids = fields.Many2many('purchase.order',
                                          help='Purchase orders associated with this tender.')

    def _compute_bid_counts(self):
        """Count the bids of each tender: all, qualified and legit ones.

        The evaluation count is the number of qualified bids, used for
        product-wise tenders."""
        Bidding = self.env['tender.bidding']
        all_counts = dict(Bidding._read_group(
            [('tender_id', 'in', self.ids)], ['tender_id'], ['__count']))
        qualified_counts = dict(Bidding._read_group(
            [('tender_id', 'in', self.ids), ('qualification_stage', '=', 'qualified')],
            ['tender_id'], ['__count']))
        legit_counts = dict(Bidding._read_group(
            [('tender_id', 'in', self.ids), ('qualification_stage', '=', 'qualified'),
             ('legit_bid', '=', True)],
            ['tender_id'], ['__count']))
        for rec in self:
            rec.all_bid_count = all_counts.get(rec, 0)
            rec.qualified_bid_count = rec.evaluation_bid_count = qualified_counts.get(rec, 0)
            rec.legit_bid_count = legit_counts.get(rec, 0)

    def _compute_tender_purchase_count(self):
        """Count the purchase orders created from each tender."""
        counts = dict(self.env['purchase.order']._read_group(
            [('tender_id', 'in', self.ids)], ['tender_id'], ['__count']))
        for rec in self:
            rec.tender_purchase_count = counts.get(rec, 0)

    @api.constrains('tender_start_date', 'tender_end_date')
    def _check_tender_date_range(self):
        """The tender cannot end before it starts."""
        for record in self:
            if (record.tender_end_date and record.tender_start_date
                    and record.tender_end_date < record.tender_start_date):
                raise ValidationError(self.env._(
                    'The tender end date must be after the tender start date.'))

    @api.constrains('bid_start_date', 'bid_end_date')
    def _check_bid_date_range(self):
        """Bidding cannot end before it starts."""
        for record in self:
            if (record.bid_end_date and record.bid_start_date
                    and record.bid_end_date < record.bid_start_date):
                raise ValidationError(self.env._(
                    'The bid end date must be after the bid start date.'))

    @api.model
    def get_tender_details(self):
        """Figures of the tender dashboard."""
        Tender = self.env['tender.management']
        Bidding = self.env['tender.bidding']
        category_counts = dict(Tender._read_group([], ['tender_category_id'], ['__count']))
        categories = self.env['tender.category'].search([], order='name', limit=100)
        type_counts = dict(Tender._read_group([], ['tender_type'], ['__count']))
        tender_types = dict(self._fields['tender_type']._description_selection(self.env))
        stage_counts = dict(Bidding._read_group([], ['qualification_stage'], ['__count']))
        timeline = Tender.search_read([], ['name', 'tender_start_date', 'tender_end_date'],
                                      order='tender_start_date desc', limit=self._DASHBOARD_LIMIT)
        timeline.reverse()
        return {
            'tender_count': Tender.search_count([]),
            'vendors_count': self.env['res.partner'].search_count([('is_vendor', '=', True)]),
            'active_tenders_count': Tender.search_count([('tender_state', '=', 'bid_submission')]),
            'tender_category_data': {
                'category_types': categories.mapped('name'),
                'category_type_count': [category_counts.get(category, 0) for category in categories],
            },
            'tender_location_count': len(Tender._read_group([], ['address_country_id'])),
            'tender_categories_count': len(categories),
            'tender_type_data': {
                'tender_types': list(tender_types.values()),
                'tender_type_count': [type_counts.get(key, 0) for key in tender_types],
            },
            'tender_timeline_data': {
                'tenders': [tender['name'] for tender in timeline],
                'tender_timeline_data': [
                    (tender['tender_end_date'] - tender['tender_start_date']).days
                    for tender in timeline],
            },
            'active_bid_count': Bidding.search_count([('bidding_state', '=', 'bid_close')]),
            'qualified_bid_count': stage_counts.get('qualified', 0),
            'disqualified_bid_count': stage_counts.get('disqualified', 0),
            'edit_request_count': Bidding.search_count([('edit_request', '=', True)]),
            'pre_qualification_count': stage_counts.get('initial', 0),
        }

    def write(self, vals):
        """Keep the bids in line with the tender stage: when bidding closes,
        pending edit requests are dropped and bids reopened for editing are
        locked again; when the tender is closed or cancelled, the bids still
        open are lost."""
        res = super().write(vals)
        state = vals.get('tender_state')
        if state and state != 'bid_submission':
            bids = self.env['tender.bidding'].search([('tender_id', 'in', self.ids)])
            bids.filtered('edit_request').write({'edit_request': False})
            bids.filtered(lambda bid: bid.bidding_state == 'bid').write({'bidding_state': 'bid_close'})
            if state in ('close', 'cancel'):
                bids.filtered(lambda bid: bid.bidding_state not in ('won', 'lost')).write(
                    {'bidding_state': 'lost'})
        return res

    def _check_tender_state(self, states):
        """Refuse a stage change from a stage not in ``states``."""
        labels = dict(self._fields['tender_state']._description_selection(self.env))
        for tender in self:
            if tender.tender_state not in states:
                raise UserError(self.env._(
                    '%(tender)s is in the %(stage)s stage; this action needs it in: %(allowed)s.',
                    tender=tender.name, stage=labels[tender.tender_state],
                    allowed=', '.join(labels[state] for state in states)))

    def action_select_final_bid(self):
        """Propose the cheapest bid in the bid selection wizard."""
        self.ensure_one()
        self._check_tender_state(['bid_selection'])
        self.best_bid_id = self.env['tender.bidding'].search(
            [('tender_id', '=', self.id)], order='total_bidding_amount asc', limit=1)
        return {
            'name': self.env._('Bid Selection'),
            'type': 'ir.actions.act_window',
            'res_model': 'bid.selection',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_current_tender_id': self.id,
                        'default_tender_bid_id': self.best_bid_id.id},
        }

    def _bid_action(self, name, domain, res_model='tender.bidding', view_mode='list,form'):
        """Window action listing records related to this tender."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_mode': view_mode,
            'res_model': res_model,
            'domain': domain,
            'context': {'create': False},
        }

    def action_get_purchase_order(self):
        """Open the purchase orders of the tender."""
        return self._bid_action(self.env._('Purchase Orders'), [('tender_id', '=', self.id)],
                                res_model='purchase.order')

    def action_get_bids(self):
        """Open all bids received for the tender."""
        return self._bid_action(self.env._('All Bids'), [('tender_id', '=', self.id)])

    def action_get_qualified_bids(self):
        """Open the qualified bids of the tender."""
        return self._bid_action(self.env._('Qualified Bids'), [
            ('qualification_stage', '=', 'qualified'), ('tender_id', '=', self.id)])

    def action_get_legit_bids(self):
        """Open the legit qualified bids of a single vendor tender."""
        return self._bid_action(self.env._('Legit Bids'), [
            ('qualification_stage', '=', 'qualified'), ('tender_id', '=', self.id),
            ('legit_bid', '=', True)])

    def action_get_evaluation_bids(self):
        """Open the qualified bid lines of a product-wise tender, by product."""
        action = self._bid_action(
            self.env._('Evaluation Bids'),
            [('tender_id', '=', self.id), ('display_type', '=', False),
             ('bid_qualified', '=', 'qualified')],
            res_model='tender.bidding.product.lines', view_mode='list')
        action['context'] = {'create': False, 'search_default_filter_group_by_product': 1}
        return action

    def action_confirm_tender(self):
        """Confirm the tender; bidding opens on the bid start date."""
        self._check_tender_state(['draft'])
        self.tender_state = 'confirm'

    def action_bid_evaluation(self):
        """Close bidding and move the tender to bid evaluation."""
        self._check_tender_state(['bid_submission'])
        self.tender_state = 'bid_evaluation'

    def action_start_selection(self):
        """Move the evaluated tender to bid selection."""
        self._check_tender_state(['bid_evaluation'])
        self.tender_state = 'bid_selection'

    def action_close(self):
        """Close the tender."""
        self._check_tender_state(['bid_selection'])
        self.tender_state = 'close'

    def action_cancel(self):
        """Cancel the tender. Bids can no longer be submitted."""
        self._check_tender_state(['draft', 'confirm', 'bid_submission', 'bid_evaluation',
                                  'bid_selection'])
        self.tender_state = 'cancel'

    def action_confirm_bids(self):
        """Create one purchase order per vendor from the lines selected in
        a product-wise tender, email the vendors and close the tender. Bids
        with a chosen line are won, the others lost."""
        self._check_tender_state(['bid_selection'])
        PurchaseOrder = self.env['purchase.order']
        template = self.env.ref('advanced_tender_management.purchase_order_confirmed_template').sudo()
        for tender in self:
            selected_lines = self.env['tender.bidding.product.lines'].search([
                ('tender_id', '=', tender.id), ('bid_status', '=', 'selected')])
            if not selected_lines:
                raise UserError(self.env._(
                    'Confirm at least one bid line of %s in Bids Evaluation first.', tender.name))
            for line in selected_lines:
                order_line = fields.Command.create({
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'price_unit': line.product_price,
                    'name': line.name,
                })
                order = PurchaseOrder.search([
                    ('partner_id', '=', line.vendor_id.id), ('state', '=', 'draft'),
                    ('tender_id', '=', tender.id)], limit=1)
                if order:
                    order.write({'order_line': [order_line]})
                else:
                    order = PurchaseOrder.create({
                        'partner_id': line.vendor_id.id,
                        'partner_ref': line.tender_bidding_id.name,
                        'date_order': fields.Datetime.now(),
                        'tender_id': tender.id,
                        'order_line': [order_line],
                    })
                tender.purchase_order_ids = [fields.Command.link(order.id)]
            winning_bids = selected_lines.tender_bidding_id
            winning_bids.bidding_state = 'won'
            tender.write({'purchase_confirmed': True, 'tender_state': 'close'})
            for order in tender.purchase_order_ids:
                template.send_mail(order.id, force_send=True)

    @api.model
    def action_tender_expiration(self):
        """Scheduled action: open confirmed tenders for bidding on their bid
        start date and move them to evaluation after their bid end date."""
        today = fields.Date.context_today(self)
        for rec in self.search([('tender_state', 'in', ('confirm', 'bid_submission'))]):
            if rec.bid_end_date < today:
                rec.tender_state = 'bid_evaluation'
            elif rec.tender_state == 'confirm' and rec.bid_start_date <= today:
                rec.tender_state = 'bid_submission'

    def action_import_tender_product_wizard(self):
        """Open the wizard importing product lines from an XLSX file."""
        self.ensure_one()
        return {
            'name': self.env._('Import Tender Product Lines'),
            'view_mode': 'form',
            'res_model': 'import.tender.product.line',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_tender_id': self.id},
        }

    def action_print_xlsx_report(self):
        """Download the product lines as an XLSX template."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/tender/{self.id}/product_template',
            'target': 'download',
        }

    def _get_product_template_xlsx(self):
        """Product lines as an XLSX file (bytes): product, description,
        quantity and unit. Sections only fill the first column."""
        self.ensure_one()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        txt = workbook.add_format({'font_size': 10, 'align': 'center'})
        for col, (title, width) in enumerate([
                (self.env._("Product"), 20), (self.env._("Description"), 30),
                (self.env._("Qty"), 10), (self.env._("Unit of Measure"), 20)]):
            sheet.write(0, col, title, txt)
            sheet.set_column(col, col, width)
        for row, line in enumerate(self.tender_product_line_ids, start=1):
            if not line.product_id:
                sheet.write(row, 0, line.name, txt)
                continue
            for col, value in enumerate([line.product_id.name, line.name,
                                         line.product_qty, line.product_uom_id.name]):
                sheet.write(row, col, value or '', txt)
        workbook.close()
        return output.getvalue()

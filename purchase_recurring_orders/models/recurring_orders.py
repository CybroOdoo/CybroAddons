# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Jesni Banu(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from datetime import timedelta
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class Agreement(models.Model):
    _name = 'purchase.recurring_orders.agreement'
    _inherit = ['mail.thread']
    _description = "Recurring orders agreement"

    @api.model
    def __get_next_term_date(self, date, unit, interval):
        if unit == 'days':
            return date + timedelta(days=interval)
        elif unit == 'weeks':
            return date + timedelta(weeks=interval)
        elif unit == 'months':
            return date + relativedelta(months=interval)
        elif unit == 'years':
            return date + relativedelta(years=interval)

    @api.multi
    def _compute_next_expiration_date(self):
        for agreement in self:
            if agreement.prolong == 'fixed':
                agreement.next_expiration_date = agreement.end_date
            elif agreement.prolong == 'unlimited':
                now = fields.Date.from_string(fields.Date.today())
                date = self.__get_next_term_date(
                    fields.Date.from_string(agreement.start_date),
                    agreement.prolong_unit, agreement.prolong_interval)
                while date < now:
                    date = self.__get_next_term_date(
                        date, agreement.prolong_unit,
                        agreement.prolong_interval)
                agreement.next_expiration_date = date
            else:
                agreement.next_expiration_date = self.__get_next_term_date(
                    fields.Date.from_string(agreement.last_renovation_date or
                                            agreement.start_date),
                    agreement.prolong_unit, agreement.prolong_interval)

    def _default_company_id(self):
        company_model = self.env['res.company']
        company_id = company_model._company_default_get('purchase')
        return company_model.browse(company_id.id)

    name = fields.Char(
        string='Name', size=100, index=True, required=True,
        help='Name that helps to identify the agreement')
    number = fields.Char(
        string='Agreement number', index=True, size=32, copy=False,
        help="Number of agreement. Keep empty to get the number assigned by a "
             "sequence.")
    active = fields.Boolean(
        string='Active', default=True,
        help='Unchecking this field, quotas are not generated')
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Supplier', index=True,
        change_default=True, required=True,
        help="Supplier you are making the agreement with")
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        help="Company that signs the agreement", default=_default_company_id)
    start_date = fields.Date(
        string='Start date', index=True, copy=False,
        help="Beginning of the agreement. Keep empty to use the current date")
    prolong = fields.Selection(
        selection=[('recurrent', 'Renewable fixed term'),
                   ('unlimited', 'Unlimited term'),
                   ('fixed', 'Fixed term')],
        string='Prolongation', default='unlimited',
        help="Sets the term of the agreement. 'Renewable fixed term': It sets "
             "a fixed term, but with possibility of manual renew; 'Unlimited "
             "term': Renew is made automatically; 'Fixed term': The term is "
             "fixed and there is no possibility to renew.", required=True)
    end_date = fields.Date(
        string='End date', help="End date of the agreement")
    prolong_interval = fields.Integer(
        string='Interval', default=1,
        help="Interval in time units to prolong the agreement until new "
             "renewable (that is automatic for unlimited term, manual for "
             "renewable fixed term).")
    prolong_unit = fields.Selection(
        selection=[('days', 'days'),
                   ('weeks', 'weeks'),
                   ('months', 'months'),
                   ('years', 'years')],
        string='Interval unit', default='years',
        help='Time unit for the prolongation interval')
    agreement_line = fields.One2many(
        comodel_name='purchase.recurring_orders.agreement.line',
        inverse_name='agreement_id', string='Agreement lines')
    order_line = fields.One2many(
        comodel_name='purchase.order', copy=False, inverse_name='agreement_id',
        string='Orders', readonly=True)
    renewal_line = fields.One2many(
        comodel_name='purchase.recurring_orders.agreement.renewal', copy=False,
        inverse_name='agreement_id', string='Renewal lines', readonly=True)
    last_renovation_date = fields.Date(
        string='Last renovation date',
        help="Last date when agreement was renewed (same as start date if not "
             "renewed)")
    next_expiration_date = fields.Date(
        compute="_compute_next_expiration_date", string='Next expiration date')
    state = fields.Selection(
        selection=[('empty', 'Without orders'),
                   ('first', 'First order created'),
                   ('orders', 'With orders')],
        string='State', readonly=True, default='empty')
    renewal_state = fields.Selection(
        selection=[('not_renewed', 'Agreement not renewed'),
                   ('renewed', 'Agreement renewed')],
        string='Renewal state', readonly=True, default='not_renewed')
    notes = fields.Text('Notes')

    _sql_constraints = [
        ('number_uniq', 'unique(number)', 'Agreement number must be unique !'),
    ]

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.end_date and record.end_date < record.start_date:
                raise exceptions.Warning(
                    _('Agreement end date must be greater than start date'))

    @api.model
    def create(self, vals):
        if not vals.get('start_date'):
            vals['start_date'] = fields.Date.today()
        if not vals.get('number'):
            vals['number'] = self.env['ir.sequence'].get(
                'purchase.r_o.agreement.sequence')
        return super(Agreement, self).create(vals)

    @api.multi
    def write(self, vals):
        value = super(Agreement, self).write(vals)
        if (any(vals.get(x) is not None for x in
                ['active', 'number', 'agreement_line', 'prolong', 'end_date',
                 'prolong_interval', 'prolong_unit', 'partner_id'])):
            self.unlink_orders(fields.Date.today())
        return value

    @api.model
    def copy(self, id, default=None):
        agreement_record = self.browse(id)
        default.update({
            'state': 'empty',
            'active': True,
            'name': '%s*' % agreement_record['name'],
        })
        return super(Agreement, self).copy(id, default=default)

    @api.multi
    def unlink(self):
        for agreement in self:
            if any(agreement.mapped('order_line')):
                raise exceptions.Warning(
                    _('You cannot remove agreements with confirmed orders!'))
        self.unlink_orders(fields.Date.from_string(fields.Date.today()))
        return models.Model.unlink(self)

    @api.multi
    def onchange_start_date(self, start_date=False):
        if not start_date:
            return {}
        result = {'value': {'last_renovation_date': start_date}}
        return result

    @api.model
    def revise_agreements_expirations_planned(self):
        for agreement in self.search([('prolong', '=', 'unlimited')]):
            if agreement.next_expiration_date <= fields.Date.today():
                agreement.write({'prolong': 'unlimited'})
        return True

    @api.model
    def _prepare_purchase_order_vals(self, agreement, date):
        order_vals = {
                        'date_order': date,
                        'date_confirm': date,
                        'origin': agreement.number,
                        'partner_id': agreement.partner_id.id,
                        'state': 'draft',
                        'company_id': agreement.company_id.id,
                        'from_agreement': True,
                        'agreement_id': agreement.id,
                        'location_id': 1,
                        'fiscal_position_id': self.env['account.fiscal.position'].with_context(company_id=agreement.company_id.id).get_fiscal_position(agreement.partner_id.id),
                        'payment_term_id': agreement.partner_id.property_supplier_payment_term_id.id,
                        'currency_id': agreement.partner_id.property_purchase_currency_id.id or self.env.user.company_id.currency_id.id,
                    }
        order_vals['user_id'] = agreement.partner_id.user_id.id
        return order_vals

    @api.model
    def _prepare_purchase_order_line_vals(self, agreement_line, order):
        product_lang = agreement_line.product_id.with_context({
            'lang': order.partner_id.lang,
            'partner_id': order.partner_id.id,
        })
        fpos = order.fiscal_position_id
        order_line_vals = {
            'order_id': order.id,
            'product_id': agreement_line.product_id.id,
            'product_qty': agreement_line.quantity,
            'date_planned': datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'price_unit': 0.0,
            'product_qty': 1.0,
            'product_uom': agreement_line.product_id.uom_po_id.id or agreement_line.product_id.uom_id.id,
            'name': product_lang.display_name,
            'taxes_id': fpos.map_tax(agreement_line.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == self.company_id.id))
        }
        if agreement_line.specific_price:
            order_line_vals['price_unit'] = agreement_line.specific_price
        order_line_vals['taxes_id'] = [(6, 0, tuple(order_line_vals['taxes_id']))]
        if agreement_line.additional_description:
            order_line_vals['name'] += " %s" % (
                agreement_line.additional_description)
        return order_line_vals

    @api.multi
    def create_order(self, date, agreement_lines):
        self.ensure_one()
        order_line_obj = self.env['purchase.order.line'].with_context(
            company_id=self.company_id.id)
        order_vals = self._prepare_purchase_order_vals(self, date)
        order = self.env['purchase.order'].create(order_vals)
        for agreement_line in agreement_lines:
            order_line_vals = self._prepare_purchase_order_line_vals(
                agreement_line, order)
            order_line_obj.create(order_line_vals)
        agreement_lines.write({'last_order_date': fields.Date.today()})
        if self.state != 'orders':
            self.state = 'orders'
        return order

    @api.multi
    def _get_next_order_date(self, line, start_date):
        self.ensure_one()
        next_date = fields.Date.from_string(self.start_date)
        while next_date <= start_date:
            next_date = self.__get_next_term_date(
                next_date, line.ordering_unit, line.ordering_interval)
        return next_date

    @api.multi
    def generate_agreement_orders(self, start_date, end_date):
        self.ensure_one()
        if not self.active:
            return
        lines_to_order = {}
        exp_date = fields.Date.from_string(self.next_expiration_date)
        if exp_date < end_date and self.prolong != 'unlimited':
            end_date = exp_date
        for line in self.agreement_line:
            if not line.active_chk:
                continue
            next_order_date = self._get_next_order_date(line, start_date)
            while next_order_date <= end_date:
                if not lines_to_order.get(next_order_date):
                    lines_to_order[next_order_date] = self.env[
                        'purchase.recurring_orders.agreement.line']
                lines_to_order[next_order_date] |= line
                next_order_date = self._get_next_order_date(
                    line, next_order_date)
        dates = lines_to_order.keys()
        dates.sort()
        for date in dates:
            order = self.order_line.filtered(
                lambda x: (
                    fields.Date.to_string(
                        fields.Datetime.from_string(x.date_order)) ==
                    fields.Date.to_string(date)))
            if not order:
                self.create_order(
                    fields.Date.to_string(date), lines_to_order[date])

    @api.multi
    def generate_initial_order(self):
        self.ensure_one()
        agreement_lines = self.mapped('agreement_line').filtered('active_chk')
        order = self.create_order(self.start_date, agreement_lines)
        self.write({'state': 'first'})
        order.signal_workflow('order_confirm')
        return {
            'domain': "[('id', '=', %s)]" % order.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'context': self.env.context,
            'res_id': order.id,
            'view_id': [self.env.ref('purchase.purchase_order_form').id],
            'type': 'ir.actions.act_window',
            'nodestroy': True
        }

    @api.model
    def generate_next_orders_planned(self, years=1, start_date=None):
        if start_date:
            start_date = fields.Date.from_string(start_date)
        self.search([]).generate_next_orders(
            years=years, start_date=start_date)

    @api.multi
    def generate_next_year_orders(self):
        return self.generate_next_orders(years=1)

    @api.multi
    def generate_next_orders(self, years=1, start_date=None):
        if not start_date:
            start_date = fields.Date.from_string(fields.Date.today())
        end_date = start_date + relativedelta(years=years)
        for agreement in self:
            agreement.generate_agreement_orders(start_date, end_date)
        return True

    @api.model
    def confirm_current_orders_planned(self):
        tomorrow = fields.Date.to_string(
            fields.Date.from_string(fields.Date.today()) + timedelta(days=1))
        orders = self.env['purchase.order'].search([
            ('agreement_id', '!=', False),
            ('state', 'in', ('draft', 'sent')),
            ('date_order', '<', tomorrow)
        ])
        for order in orders:
            order.signal_workflow('order_confirm')

    @api.multi
    def unlink_orders(self, start_date):
        orders = self.mapped('order_line').filtered(
            lambda x: (x.state in ('draft', 'sent') and
                       x.date_order >= start_date))
        orders.unlink()


class AgreementLine(models.Model):
    _name = 'purchase.recurring_orders.agreement.line'

    uom_id = fields.Many2one('product_uom', string="Uom")
    active_chk = fields.Boolean(
        string='Active', default=True,
        help='Unchecking this field, this quota is not generated')
    agreement_id = fields.Many2one(
        comodel_name='purchase.recurring_orders.agreement',
        string='Agreement reference', ondelete='cascade')
    product_id = fields.Many2one(
        comodel_name='product.product', string='Product', ondelete='set null',
        required=True)
    name = fields.Char(
        related="product_id.name", string='Description', store=False)
    additional_description = fields.Char(
        string='Add. description', size=30,
        help='Additional description that will be added to the product '
             'description on orders.')
    quantity = fields.Float(
        string='Quantity', required=True, help='Quantity of the product',
        default=1.0)
    discount = fields.Float(string='Discount (%)', digits=(16, 2))
    ordering_interval = fields.Integer(
        string='Interval', required=True, default=1,
        help="Interval in time units for making an order of this product")
    ordering_unit = fields.Selection(
        selection=[('days', 'days'),
                   ('weeks', 'weeks'),
                   ('months', 'months'),
                   ('years', 'years')],
        string='Interval unit', required=True, default='months')
    last_order_date = fields.Date(
        string='Last order', help='Date of the last Purchase order generated')
    specific_price = fields.Float(
        string='Specific price', digits_compute=dp.get_precision('Purchase Price'),
        help='Specific price for this product. Keep empty to use the list '
             'price while generating order')
    list_price = fields.Float(
        related='product_id.list_price', string="List price", readonly=True)

    _sql_constraints = [
        ('line_qty_zero', 'CHECK (quantity > 0)',
         'All product quantities must be greater than 0.\n'),
        ('line_interval_zero', 'CHECK (ordering_interval > 0)',
         'All ordering intervals must be greater than 0.\n'),
    ]

    @api.multi
    def onchange_product_id(self, product_id=False):
        result = {}
        if product_id:
            product = self.env['product.product'].browse(product_id)
            if product:
                result['value'] = {'name': product['name']}
        return result


class AgreementRenewal(models.Model):
    _name = 'purchase.recurring_orders.agreement.renewal'

    agreement_id = fields.Many2one(
        comodel_name='purchase.recurring_orders.agreement',
        string='Agreement reference', ondelete='cascade', select=True)
    date = fields.Date(string='Date', help="Date of the renewal")
    comments = fields.Char(
        string='Comments', size=200, help='Renewal comments')

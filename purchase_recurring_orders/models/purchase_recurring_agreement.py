# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ayana KP (odoo@cybrosys.com)
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
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, exceptions, fields, models, _


class PurchaseRecurringAgreement(models.Model):
    """Model for generating purchase recurring agreement"""
    _name = 'purchase.recurring.agreement'
    _inherit = 'mail.thread'
    _description = "Purchase Recurring Agreement"

    @api.model
    def _get_next_term_date(self, date, unit, interval):
        """Returns the Next Term Date"""
        if unit == 'days':
            date = date + timedelta(days=interval)
        elif unit == 'weeks':
            date = date + timedelta(weeks=interval)
        elif unit == 'months':
            date = date + relativedelta(months=interval)
        elif unit == 'years':
            date = date + relativedelta(years=interval)
        return date

    def _compute_next_expiration_date(self):
        """Calculates the Next Expiration Date According to the Prolongation
        Unit Chosen"""
        for agreement in self:
            if agreement.prolong == 'fixed':
                agreement.next_expiration_date = agreement.end_date
            elif agreement.prolong == 'unlimited':
                now = fields.Date.from_string(fields.Datetime.today())
                date = self._get_next_term_date(
                    fields.Date.from_string(agreement.start_date),
                    agreement.prolong_unit, agreement.prolong_interval)
                while date < now:
                    date = self._get_next_term_date(
                        date, agreement.prolong_unit,
                        agreement.prolong_interval)
                agreement.next_expiration_date = date
            else:
                agreement.next_expiration_date = self._get_next_term_date(
                    fields.Datetime.from_string(
                        agreement.last_renovation_date or
                        agreement.start_date),
                    agreement.prolong_unit, agreement.prolong_interval)

    def _default_company_id(self):
        """Returns the Current Company Id"""
        company_model = self.env['res.company']
        company_id = company_model._company_default_get('purchase')
        return company_model.browse(company_id.id)

    name = fields.Char(
        string='Name', size=100, index=True, required=True,
        help='Name that Helps to Identify the Agreement')
    number = fields.Char(
        string='Agreement Number', index=True, size=32, copy=False,
        help="Number of Agreement. Keep Empty to Get the Number Assigned by a "
             "Sequence.")
    active = fields.Boolean(
        string='Active', default=True,
        help='Uncheck this Field, Quotas are not Generated')
    partner_id = fields.Many2one('res.partner', string='Supplier', index=True,
                                 change_default=True, required=True,
                                 help="Supplier You are Making the "
                                      "Agreement with")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 help="Company that Signs the Agreement",
                                 default=_default_company_id)
    start_date = fields.Date(
        string='Start Date', index=True, copy=False,
        help="Beginning of the Agreement. Keep Empty to Use the Current Date")
    prolong = fields.Selection(
        selection=[('recurrent', 'Renewable Fixed Term'),
                   ('unlimited', 'Unlimited Term'),
                   ('fixed', 'Fixed Term')],
        string='Prolongation', default='unlimited',
        help="Sets the term of the agreement. 'Renewable fixed term': It sets "
             "a fixed term, but with possibility of manual renew; 'Unlimited "
             "term': Renew is made automatically; 'Fixed term': The term is "
             "fixed and there is no possibility to renew.")
    end_date = fields.Date(
        string='End date', help="End Date of the Agreement")
    prolong_interval = fields.Integer(
        string='Interval', default=1,
        help="Interval in time units to prolong the agreement until new "
             "renewable (that is automatic for unlimited term, manual for "
             "renewable fixed term).")
    prolong_unit = fields.Selection(
        selection=[('days', 'Days'),
                   ('weeks', 'Weeks'),
                   ('months', 'Months'),
                   ('years', 'Years')],
        string='Interval Unit', default='years',
        help='Time unit for the prolongation interval')
    agreement_line_ids = fields.One2many('recurring.agreement.line',
                                         inverse_name='recurring_agreement_id',
                                         string='Agreement Lines')
    order_ids = fields.One2many('purchase.order', copy=False,
                                inverse_name='recurring_agreement_id',
                                string='Orders', readonly=True)
    renewal_ids = fields.One2many('purchase.agreement.renewal', copy=False,
                                  inverse_name='recurring_agreement_id',
                                  string='Renewal Lines',
                                  readonly=True)
    last_renovation_date = fields.Datetime(
        string='Last Renovation Date',
        help="Last date when agreement was renewed (same as start date if not "
             "renewed)")
    next_expiration_date = fields.Datetime(
        compute="_compute_next_expiration_date",
        help="Date when agreement will expired ",
        string='Next Expiration Date')
    state = fields.Selection(
        selection=[('empty', 'Without Orders'),
                   ('first', 'First Order Created'),
                   ('orders', 'With Orders')],
        string='State', help="Indicates the state of recurring agreement",
        readonly=True, default='empty')
    renewal_state = fields.Selection(
        selection=[('not_renewed', 'Agreement not Renewed'),
                   ('renewed', 'Agreement Renewed')],
        string='Renewal State',
        help="Renewal Status of the Recurring agreement", readonly=True,
        default='not_renewed')
    notes = fields.Text('Notes', help="Notes regarding Renewal agreement")
    order_count = fields.Integer(compute='_compute_order_count',
                                 help="Indicates the No. of Orders Generated "
                                      "with this Agreement")

    _sql_constraints = [
        ('number_uniq', 'unique(number)', 'Agreement Number Must be Unique !'),
    ]

    def get_orders(self):
        """Returns All Orders Generated from the Agreement"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Orders',
            'views': [[False, 'tree'], [False, 'form']],
            'res_model': 'purchase.order',
            'domain': [('recurring_agreement_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def _compute_order_count(self):
        """Finds the count of orders generated from the Agreement"""
        for record in self:
            record.order_count = self.env['purchase.order'].search_count(
                [('recurring_agreement_id', '=', self.id)])

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Method for ensuring start date will be always less than
         or equal to end date"""
        for record in self:
            if record.end_date and record.end_date < record.start_date:
                raise exceptions.Warning(
                    _('Agreement End Date must be Greater than Start Date'))

    @api.model
    def create(self, vals):
        """Function that supering create function"""
        if not vals.get('start_date'):
            vals['start_date'] = fields.Datetime.today()
        if not vals.get('number'):
            vals['number'] = self.env['ir.sequence'].get(
                'purchase.r_o.agreement.sequence')
        return super().create(vals)

    def write(self, vals):
        """Function that supering write function"""
        value = super().write(vals)
        if (any(vals.get(rec) is not None for rec in
                ['active', 'number', 'agreement_line_ids', 'prolong',
                 'end_date',
                 'prolong_interval', 'prolong_unit', 'partner_id'])):
            self.unlink_orders(fields.Datetime.today())
        return value

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        if 'name' not in default:
            default['name'] = _("%s (Copy)") % self.name
        return super().copy(default=default)

    def unlink(self):
        """Function that supering unlink function which will unlink Self and
        the Current record"""
        for agreement in self:
            if any(agreement.mapped('order_ids')):
                raise exceptions.Warning(
                    _('You Cannot Remove Agreements with Confirmed Orders!'))
        self.unlink_orders(fields.Datetime.from_string(fields.Datetime.today()))
        return models.Model.unlink(self)

    @api.onchange('start_date')
    def onchange_start_date(self, start_date=False):
        """Method for updating last renovation date"""
        if not start_date:
            return {}
        result = {'value': {'last_renovation_date': start_date}}
        return result

    @api.model
    def revise_agreements_expirations_planned(self):
        """Method for changing the prolong as unlimited"""
        for agreement in self.search([('prolong', '=', 'unlimited')]):
            if agreement.next_expiration_date <= fields.Datetime.today():
                agreement.write({'prolong': 'unlimited'})
        return True

    @api.model
    def _prepare_purchase_order_vals(self, agreement, date):
        """Creates purchase order values"""
        # Order Values
        order_vals = {'date_order': date, 'origin': agreement.number,
                      'partner_id': agreement.partner_id.id,
                      'state': 'draft', 'company_id': agreement.company_id.id,
                      'from_agreement': True,
                      'recurring_agreement_id': agreement.id,
                      'date_planned': date,
                      'fiscal_position_id': self.env[
                          'account.fiscal.position'].with_context(
                          company_id=agreement.company_id.id).
                      _get_fiscal_position(agreement.partner_id),
                      'payment_term_id': agreement.partner_id.
                      property_supplier_payment_term_id.id,
                      'currency_id': agreement.partner_id.
                                     property_purchase_currency_id.id or
                                     self.env.user.company_id.currency_id.id,
                      'user_id': agreement.partner_id.user_id.id}
        return order_vals

    @api.model
    def _prepare_purchase_order_line_vals(self, agreement_line_ids, order):
        """Returns the Purchase Order Line Values as a Dictionary Which can be
         Used While creating the Purchase Order"""
        product_lang = agreement_line_ids.product_id.with_context({
            'lang': order.partner_id.lang,
            'partner_id': order.partner_id.id,
        })
        fpos = order.fiscal_position_id
        # Order Line Values as a Dictionary
        order_line_vals = {
            'order_id': order.id,
            'product_id': agreement_line_ids.product_id.id,
            'product_qty': agreement_line_ids.quantity,
            'date_planned': order.date_planned,
            'price_unit': agreement_line_ids.product_id.
            _get_tax_included_unit_price(
                order.company_id,
                order.currency_id,
                order.date_order,
                'purchase',
                fiscal_position=order.fiscal_position_id,
                product_uom=agreement_line_ids.product_id.uom_po_id),
            'product_uom': agreement_line_ids.product_id.uom_po_id.id or
                           agreement_line_ids.product_id.uom_id.id,
            'name': product_lang.display_name,
            'taxes_id': fpos.map_tax(
                agreement_line_ids.product_id.supplier_taxes_id.filtered(
                    lambda r: r.company_id.id == self.company_id.id).ids)
        }
        # product price changed if specific price is added
        if agreement_line_ids.specific_price:
            order_line_vals['price_unit'] = agreement_line_ids.specific_price
        order_line_vals['taxes_id'] = [
            (6, 0, tuple(order_line_vals['taxes_id']))]
        # product price changed if specific price is added
        if agreement_line_ids.additional_description:
            order_line_vals['name'] += " %s" % (
                agreement_line_ids.additional_description)
        return order_line_vals

    def create_order(self, date, agreement_lines):
        """Create Purchase Order from Recurring Agreement """
        self.ensure_one()
        order_line_obj = self.env['purchase.order.line'].with_context(
            company_id=self.company_id.id)
        order_vals = self._prepare_purchase_order_vals(self, date)
        order = self.env['purchase.order'].create(order_vals)
        for agreement_line in agreement_lines:
            # Create Purchase Order Line Values
            order_line_vals = self._prepare_purchase_order_line_vals(
                agreement_line, order)
            order_line_obj.create(order_line_vals)
        agreement_lines.write({'last_order_date': fields.Datetime.today()})
        if self.state != 'orders':
            self.state = 'orders'
        return order

    def _get_next_order_date(self, line, start_date):
        """Return The date of Next Purchase order generated from the
         Agreement"""
        self.ensure_one()
        next_date = fields.Datetime.from_string(self.start_date)
        while next_date <= start_date:
            next_date = self._get_next_term_date(
                next_date, line.ordering_unit, line.ordering_interval)
        return next_date

    def generate_agreement_orders(self, start_date, end_date):
        """Method for generating agreement orders"""
        self.ensure_one()
        if not self.active:
            return
        lines_to_order = {}
        # Get next expiration date
        exp_date = fields.Datetime.from_string(self.next_expiration_date)
        if exp_date < end_date and self.prolong != 'unlimited':
            end_date = exp_date
        for line in self.agreement_line_ids:
            if not line.active_chk:
                continue
            # Get Date of Next Order
            next_order_date = self._get_next_order_date(line, start_date)
            while next_order_date <= end_date:
                if not lines_to_order.get(next_order_date):
                    lines_to_order[next_order_date] = self.env[
                        'recurring.agreement.line']
                lines_to_order[next_order_date] |= line
                next_order_date = self._get_next_order_date(
                    line, next_order_date)
        dates = lines_to_order.keys()
        sorted(dates)
        for date in dates:
            order = self.order_ids.filtered(
                lambda x: (
                        fields.Date.to_string(
                            fields.Datetime.from_string(x.date_order)) ==
                        fields.Date.to_string(date)))
            if not order:
                self.create_order(
                    fields.Datetime.to_string(date), lines_to_order[date])

    def generate_initial_order(self):
        """This will generate the Initial purchase Order from the Purchase
        Agreement"""
        self.ensure_one()
        agreement_lines = self.mapped('agreement_line_ids').filtered(
            'active_chk')
        order = self.create_order(self.start_date, agreement_lines)
        self.write({'state': 'first'})
        order.button_confirm()
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
        """Method for generating the planned orders"""
        if start_date:
            start_date = fields.Datetime.from_string(start_date)
        self.search([]).generate_next_orders(
            years=years, start_date=start_date)

    def generate_next_year_orders(self):
        """This will Generate Orders for Next year"""
        return self.generate_next_orders(years=1)

    def generate_next_orders(self, years=1, start_date=None):
        if not start_date:
            start_date = fields.Datetime.from_string(fields.Date.today())
        end_date = start_date + relativedelta(years=years)
        for agreement in self:
            agreement.generate_agreement_orders(start_date, end_date)
        return True

    @api.model
    def confirm_current_orders_planned(self):
        """This will Confirm All Orders satisfying the Domain"""
        tomorrow = fields.Date.to_string(
            fields.Datetime.from_string(fields.Datetime.today()) + timedelta(
                days=1))
        orders = self.env['purchase.order'].search([
            ('recurring_agreement_id', '!=', False),
            ('state', 'in', ('draft', 'sent')),
            ('date_order', '<', tomorrow)
        ])
        for order in orders:
            order.signal_workflow('order_confirm')

    def unlink_orders(self, start_date):
        """ Remove the relation between ``self`` and the related record."""
        orders = self.mapped('order_ids').filtered(
            lambda x: (x.state in ('draft', 'sent') and
                       x.date_order >= start_date))
        orders.unlink()

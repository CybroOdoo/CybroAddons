# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """Inherit Sale Orders to support offline sales synchronization."""
    _inherit = 'sale.order'

    offline_uid = fields.Char('Offline UID', readonly=True, copy=False)

    @api.model
    def _prepare_offline_partner_vals(self, data):
        """Prepare partner values from offline customer data."""
        vals = {
            'name': data.get('name') or data.get('partner_name') or 'Offline Customer',
            'street': data.get('street') or data.get('partner_street') or '',
            'city': data.get('city') or data.get('partner_city') or '',
            'zip': data.get('zip') or data.get('partner_zip') or '',
            'phone': data.get('phone') or data.get('partner_phone') or '',
            'email': data.get('email') or data.get('partner_email') or '',
            'website': data.get('website') or data.get('partner_website') or '',
            'vat': data.get('vat') or data.get('partner_vat') or '',
        }
        if 'mobile' in self.env['res.partner']._fields:
            vals['mobile'] = data.get('mobile') or data.get('partner_mobile') or ''
        return vals

    @api.model
    def _get_or_create_offline_partner(self, offline_partner_id, data=None):
        """Synchronize offline customers and sale orders with Odoo."""
        data = data or {'id': offline_partner_id}
        vals = self._prepare_offline_partner_vals(data)
        search_domain = []
        if vals.get('email'):
            search_domain = [('email', '=', vals['email'])]
        elif vals.get('phone'):
            search_domain = [('phone', '=', vals['phone'])]
        elif vals.get('mobile'):
            search_domain = [('mobile', '=', vals['mobile'])]
        elif vals.get('name') and vals.get('street'):
            search_domain = [
                ('name', '=', vals['name']),
                ('street', '=', vals['street']),
                ('city', '=', vals.get('city') or False),
                ('zip', '=', vals.get('zip') or False),
            ]
        if search_domain:
            partner = self.env['res.partner'].search(search_domain, limit=1)
            if partner:
                return partner

        return self.env['res.partner'].create(vals)

    @api.model
    def create_from_offline(self, orders_data, partners_data=None):
        """ Create sale orders and partners from offline data JSON """
        _logger.info("OFFLINE_SALE Sync: %s orders, %s partners", len(orders_data),
                     len(partners_data or []))
        results = {'orders': [], 'partners': []}
        partner_id_map = {}
        # 1. Create Partners First
        if partners_data:
            for p_info in partners_data:
                try:
                    offline_partner_id = p_info.get('id')
                    if not offline_partner_id:
                        continue
                    new_p = self._get_or_create_offline_partner(offline_partner_id,
                                                                p_info)
                    partner_id_map[offline_partner_id] = new_p.id
                    results['partners'].append(
                        {'offline_id': offline_partner_id, 'id': new_p.id})
                except Exception as e:
                    _logger.error("Failed to create offline partner: %s", str(e))
                    results['partners'].append(
                        {'offline_id': p_info.get('id'), 'error': str(e)})
        # 2. Process Orders
        for data in orders_data:
            try:
                uid = data.get('uid')
                if not uid:
                    continue
                # 2.a Loaded backend order: register payment against existing SO
                backend_id = data.get('backend_order_id')
                if backend_id:
                    order = self.browse(int(backend_id)).exists()
                    if not order:
                        results['orders'].append({'uid': uid, 'status': 'error',
                                                  'message': 'Backend order not found'})
                        continue
                    if data.get('state') == 'confirmed' and order.state in ('draft',
                                                                            'sent'):
                        order.action_confirm()
                    self._process_offline_invoice_payment(order, data)
                    self._post_offline_backend_note(order, data)
                    results['orders'].append({
                        'uid': uid,
                        'name': order.name,
                        'id': order.id,
                        'status': 'paid_existing',
                        'state': order.state,
                    })
                    continue
                target_state = data.get('state', 'draft')  # 'draft' or 'confirmed'
                existing = self.search([('offline_uid', '=', uid)], limit=1)
                # Get partner (either existing Odoo ID or Offline ID we just created)
                partner_id = data.get('partner_id')
                original_partner_id = partner_id
                if isinstance(partner_id, str) and partner_id.startswith('OFF-'):
                    partner_id = partner_id_map.get(partner_id)
                    if not partner_id:
                        partner_err = next(
                            (p.get('error') for p in results['partners'] if
                             p.get('offline_id') == original_partner_id),
                            None
                        )
                        if partner_err:
                            results['orders'].append({'uid': uid, 'status': 'error',
                                                      'message': f"Partner creation failed: {partner_err}"})
                            continue
                        else:
                            partner = self._get_or_create_offline_partner(
                                original_partner_id, data)
                            partner_id = partner.id
                if not partner_id:
                    results['orders'].append({'uid': uid, 'status': 'error',
                                              'message': 'Missing Partner Selection'})
                    continue
                order_vals = {
                    'partner_id': int(partner_id),
                    'offline_uid': uid,
                    'payment_term_id': int(data.get('payment_term_id')) if data.get(
                        'payment_term_id') else False,
                    'order_line': [],
                }
                lines_vals = []
                for line in data.get('lines', []):
                    line_vals = {
                        'product_id': int(line.get('product_id')),
                        'product_uom_qty': float(line.get('qty', 1)),
                        'price_unit': float(line.get('price_unit', 0)),
                        'discount': float(line.get('discount', 0)),
                    }
                    if line.get('tax_ids'):
                        line_vals['tax_id'] = [
                            (6, 0, [int(tid) for tid in line.get('tax_ids')])]
                    lines_vals.append((0, 0, line_vals))
                order_vals['order_line'] = lines_vals

                if existing:
                    if existing.state == 'draft':
                        existing.order_line.unlink()
                        existing.write(order_vals)
                        if target_state == 'confirmed':
                            existing.action_confirm()
                            self._process_offline_invoice_payment(existing, data)
                        self._post_offline_backend_note(existing, data)
                        results['orders'].append(
                            {'uid': uid, 'name': existing.name, 'id': existing.id,
                             'status': 'updated', 'state': existing.state})
                    else:
                        if target_state == 'confirmed':
                            self._process_offline_invoice_payment(existing, data)
                        self._post_offline_backend_note(existing, data)
                        results['orders'].append(
                            {'uid': uid, 'name': existing.name, 'id': existing.id,
                             'status': 'existing', 'state': existing.state})
                    continue
                new_order = self.create(order_vals)
                if target_state == 'confirmed':
                    new_order.action_confirm()
                    self._process_offline_invoice_payment(new_order, data)
                self._post_offline_backend_note(new_order, data)
                results['orders'].append({
                    'uid': uid,
                    'name': new_order.name,
                    'id': new_order.id,
                    'status': 'created',
                    'state': new_order.state
                })
            except Exception as e:
                _logger.error("OFFLINE_SALE sync error: %s", str(e))
                results['orders'].append(
                    {'uid': data.get('uid'), 'status': 'error', 'message': str(e)})
        return results

    def _post_offline_backend_note(self, order, data):
        """ Post the offline-captured backend note to the order's chatter. """
        note = (data.get('backend_note') or '').strip()
        if not note:
            return
        try:
            body = "<p><strong>Offline Backend Note</strong></p><p>%s</p>" % (
                note.replace('\n', '<br/>')
            )
            order.message_post(body=body, subject="Offline Backend Note")
        except Exception as e:
            _logger.error("Failed to post offline backend note for %s: %s",
                          order.display_name, str(e))

    def _create_offline_invoice_from_ordered_qty(self):
        """Create an invoice using Odoo 18's _create_invoices() mechanism.
        Products configured with Delivered Quantities invoicing policy are
        handled by temporarily marking lines as fully delivered so the standard
        invoicing flow picks them up — then reverting if needed.
        """
        self.ensure_one()

        # For "delivery" policy products: set qty_delivered = ordered qty so
        # the standard invoice engine sees them as invoiceable.
        lines_to_revert = []
        for line in self.order_line.filtered(
                lambda l: not l.display_type
                          and not l.is_downpayment
                          and l.product_id.invoice_policy == 'delivery'
                          and l.qty_delivered < l.product_uom_qty
        ):
            lines_to_revert.append((line, line.qty_delivered))
            line.qty_delivered = line.product_uom_qty

        try:
            # Odoo 18 standard invoicing — respects invoice_policy correctly now
            # that qty_delivered is set. Returns account.move recordset.
            invoices = self._create_invoices(final=False)
        except Exception:
            # Revert qty_delivered changes on failure before re-raising
            for line, original_qty in lines_to_revert:
                line.qty_delivered = original_qty
            raise

        # We do NOT revert qty_delivered — the offline terminal is a
        # pay-now/take-now flow so the delivered quantity should stay.
        if invoices:
            return invoices[0]
        return self.env['account.move']

    def _process_offline_invoice_payment(self, order, data):
        """Create invoice (or reuse the existing pending one) and register
        the offline payment against it.

        For partial payments, the registered account.payment is created only
        for the amount actually tendered. The account.move keeps the unpaid
        balance as amount_residual and its payment_state becomes 'partial'.
        """
        try:
            # 1. Locate or create the invoice
            invoice = order.invoice_ids.filtered(
                lambda m: m.move_type == 'out_invoice'
                          and m.state != 'cancel'
                          and m.payment_state not in ('paid', 'in_payment', 'reversed')
            )[:1]

            if not invoice:
                invoice = order._create_offline_invoice_from_ordered_qty()
                if not invoice:
                    raise Exception(
                        "No invoiceable lines found for offline payment on %s" % order.display_name
                    )

            if invoice.state == 'draft':
                invoice.action_post()

            # 2. Determine the amount to register
            raw_paid = float(data.get('amount_paid') or 0.0)
            amount_to_pay = max(0.0, min(raw_paid, invoice.amount_residual))

            if amount_to_pay <= 0:
                _logger.info(
                    "Offline invoice %s posted with no payment registered "
                    "(amount_due=%s remains as balance).",
                    invoice.name, invoice.amount_total,
                )
                return

            # 3. Register payment via account.payment.register (Odoo 18 standard)
            journal = self.env['account.journal'].search([
                ('type', 'in', ('bank', 'cash')),
                ('company_id', '=', order.company_id.id),
            ], limit=1)

            if not journal:
                raise Exception(
                    "No bank/cash journal found for company %s" % order.company_id.display_name
                )

            payment_register = self.env['account.payment.register'].with_context(
                active_model='account.move',
                active_ids=invoice.ids,
            ).create({
                'amount': amount_to_pay,
                'journal_id': journal.id,
                'payment_date': fields.Date.context_today(self),
            })
            payment_register._create_payments()

            if amount_to_pay < invoice.amount_total:
                _logger.info(
                    "Offline partial payment registered for %s: paid=%s, balance=%s",
                    invoice.name, amount_to_pay, invoice.amount_total - amount_to_pay,
                )
        except Exception as e:
            _logger.error("Failed to finalize offline invoice/payment: %s", str(e))
            raise

    @api.model
    def get_pending_sale_orders(self):
        """Return sale orders that still have an unpaid (or uninvoiced) balance."""
        # Fetch only orders that are not cancelled and not yet fully invoiced.
        # invoice_status values: 'upselling', 'invoiced', 'to invoice', 'nothing'
        domain = [
            ('state', 'not in', ('cancel',)),
            ('invoice_status', '!=', 'nothing'),
        ]
        orders = self.search(domain, order='date_order desc', limit=200)
        result = []
        for order in orders:
            try:
                invoices = order.invoice_ids.filtered(
                    lambda m: m.move_type == 'out_invoice' and m.state != 'cancel'
                )
                fully_paid = bool(invoices) and all(
                    inv.payment_state in ('paid', 'in_payment', 'reversed')
                    for inv in invoices
                )
                if fully_paid:
                    continue
                residual = sum(invoices.mapped(
                    'amount_residual')) if invoices else order.amount_total
                # Guard against False date_order on draft orders
                date_str = ''
                if order.date_order:
                    try:
                        date_str = order.date_order.strftime('%Y-%m-%d %H:%M')
                    except Exception:
                        date_str = str(order.date_order)
                lines = []
                for l in order.order_line:
                    try:
                        if not l.product_id:
                            continue
                        line_data = {
                            'product_id': l.product_id.id,
                            'name': l.product_id.display_name or l.name or '',
                            'qty': l.product_uom_qty or 0.0,
                            'price_unit': l.price_unit or 0.0,
                            'discount': getattr(l, 'discount', 0.0),
                            'tax_ids': l.tax_id.ids if hasattr(l,
                                                               'tax_id') else [],
                        }
                        lines.append(line_data)
                    except Exception:
                        import traceback
                        traceback.print_exc()
                result.append({
                    'id': order.id,
                    'name': order.name or '',
                    'date': date_str,
                    'state': order.state,
                    'invoice_status': order.invoice_status,
                    'partner_id': order.partner_id.id if order.partner_id else False,
                    'partner_name': order.partner_id.name or '',
                    'partner_email': order.partner_id.email or '',
                    'partner_city': order.partner_id.city or '',
                    'partner_zip': order.partner_id.zip or '',
                    'amount_untaxed': order.amount_untaxed,
                    'amount_tax': order.amount_tax,
                    'amount_total': order.amount_total,
                    'amount_residual': residual,
                    'payment_term_id': order.payment_term_id.id if order.payment_term_id else False,
                    'lines': lines,
                })
            except Exception as e:
                _logger.error(
                    "get_pending_sale_orders: skipping order id=%s due to error: %s",
                    order.id, str(e)
                )
        return result

    @api.model
    def get_offline_data(self):
        """ Get initial data for offline working """
        products = self.env['product.product'].search_read(
            [('sale_ok', '=', True)],
            ['id', 'display_name', 'lst_price', 'barcode', 'default_code', 'categ_id',
             'taxes_id']
        )
        partners = self.env['res.partner'].search_read(
            [],
            ['id', 'name', 'email', 'phone', 'barcode', 'street', 'city', 'zip',
             'country_id']
        )
        categories = self.env['product.category'].search_read([], ['id', 'name'])
        company = self.env.company
        company_info = {
            'name': company.name,
            'street': company.street,
            'city': company.city,
            'zip': company.zip,
            'country': company.country_id.name,
            'phone': company.phone,
            'vat': company.vat,
        }
        payment_terms = self.env['account.payment.term'].search_read([], ['id', 'name'])
        employees = []
        if 'hr.employee' in self.env:
            employees = self.env['hr.employee'].search_read([], ['id', 'name', 'job_id',
                                                                 'pin'])
        taxes = self.env['account.tax'].search_read(
            [('type_tax_use', '=', 'sale')],
            ['id', 'name', 'amount', 'price_include', 'include_base_amount',
             'amount_type']
        )
        return {
            'products': products,
            'partners': partners,
            'categories': categories,
            'company': company_info,
            'user_name': self.env.user.name,
            'employees': employees,
            'payment_terms': payment_terms,
            'taxes': taxes,
        }

    @api.model
    def send_offline_receipt_mail(self, uid, receipt_html, email, subject=None,
                                  body=None):
        """ Generate PDF from receipt HTML and attach to chatter/send via email """
        _logger.info(
            "Generating offline receipt PDF and sending email to %s for order %s", email,
            uid)
        pdf_content = self.env['ir.actions.report']._run_wkhtmltopdf([receipt_html])
        pdf_content = pdf_content[0] if isinstance(pdf_content, tuple) else pdf_content
        sale_order = self.search([('offline_uid', '=', uid)], limit=1)
        attachment_vals = {
            'name': 'Receipt_%s.pdf' % uid,
            'type': 'binary',
            'raw': pdf_content,
            'description': 'Offline Transaction Receipt',
        }
        if sale_order:
            attachment_vals['res_model'] = 'sale.order'
            attachment_vals['res_id'] = sale_order.id
        attachment = self.env['ir.attachment'].create(attachment_vals)
        if sale_order:
            sale_order.message_post(
                body="<p>Receipt sent to %s</p>" % email,
                attachment_ids=[attachment.id],
            )
        if email:
            safe_subject = subject if subject else 'Transaction Receipt - %s' % uid
            safe_body = (
                body.replace('\n', '<br/>') if body
                else '<p>Dear Customer,</p><p>Please find attached your transaction receipt for order <strong>%s</strong>.</p><p>Thank you for your business!</p>' % uid
            )
            mail_values = {
                'subject': safe_subject,
                'body_html': safe_body,
                'email_to': email,
                'attachment_ids': [(4, attachment.id)],
            }
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.send()
        return True

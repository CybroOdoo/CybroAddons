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

import collections
import hmac
import logging
import time

from lxml import html
from lxml.html.clean import Cleaner
from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.http import request
from odoo.tools import email_normalize, html_sanitize, plaintext2html

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
        """Return the matching partner or create one from offline customer data."""
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
        _logger.info("OFFLINE_SALE Sync: %s orders, %s partners", len(orders_data), len(partners_data or []))

        results = {'orders': [], 'partners': []}
        partner_id_map = {}

        # 1. Create Partners First
        if partners_data:
            for p_info in partners_data:
                try:
                    with self.env.cr.savepoint():
                        offline_partner_id = p_info.get('id')
                        if not offline_partner_id:
                            continue
                        new_p = self._get_or_create_offline_partner(offline_partner_id, p_info)
                    partner_id_map[offline_partner_id] = new_p.id
                    results['partners'].append({'offline_id': offline_partner_id, 'id': new_p.id})
                except Exception as e:
                    _logger.error("Failed to create offline partner: %s", str(e))
                    results['partners'].append({'offline_id': p_info.get('id'), 'error': str(e)})

        # 2. Process Orders
        for data in orders_data:
            try:
                with self.env.cr.savepoint():
                    result = self._process_offline_order(data, partner_id_map, results['partners'])
            except Exception as e:
                _logger.error("OFFLINE_SALE sync error: %s", str(e))
                result = {'uid': data.get('uid'), 'status': 'error', 'message': str(e)}
            if result:
                results['orders'].append(result)

        return results

    @api.model
    def _process_offline_order(self, data, partner_id_map, partner_results):
        """Create or update one offline order and return its sync result."""
        uid = data.get('uid')
        if not uid:
            return None

        backend_id = data.get('backend_order_id')
        if backend_id:
            order = self.browse(int(backend_id)).exists()
            if not order:
                return {'uid': uid, 'status': 'error', 'message': 'Backend order not found'}
            if data.get('state') == 'confirmed' and order.state in ('draft', 'sent'):
                order.action_confirm()
            self._process_offline_invoice_payment(order, data)
            self._post_offline_backend_note(order, data)
            return {
                'uid': uid,
                'name': order.name,
                'id': order.id,
                'status': 'paid_existing',
                'state': order.state,
            }

        target_state = data.get('state', 'draft')
        existing = self.search([('offline_uid', '=', uid)], limit=1)

        partner_id = data.get('partner_id')
        original_partner_id = partner_id
        if isinstance(partner_id, str) and partner_id.startswith('OFF-'):
            partner_id = partner_id_map.get(partner_id)
            if not partner_id:
                partner_err = next(
                    (p.get('error') for p in partner_results if p.get('offline_id') == original_partner_id),
                    None,
                )
                if partner_err:
                    return {
                        'uid': uid,
                        'status': 'error',
                        'message': f"Partner creation failed: {partner_err}",
                    }
                partner = self._get_or_create_offline_partner(original_partner_id, data)
                partner_id = partner.id

        if not partner_id:
            return {'uid': uid, 'status': 'error', 'message': 'Missing Partner Selection'}

        order_vals = {
            'partner_id': int(partner_id),
            'offline_uid': uid,
            'payment_term_id': int(data.get('payment_term_id')) if data.get('payment_term_id') else False,
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
                line_vals['tax_ids'] = [Command.set([int(tid) for tid in line.get('tax_ids')])]
            lines_vals.append(Command.create(line_vals))
        order_vals['order_line'] = lines_vals

        if existing:
            if existing.state == 'draft':
                existing.order_line.unlink()
                existing.write(order_vals)
                if target_state == 'confirmed':
                    existing.action_confirm()
                    self._process_offline_invoice_payment(existing, data)
                self._post_offline_backend_note(existing, data)
                return {
                    'uid': uid,
                    'name': existing.name,
                    'id': existing.id,
                    'status': 'updated',
                    'state': existing.state,
                }
            if target_state == 'confirmed':
                self._process_offline_invoice_payment(existing, data)
            self._post_offline_backend_note(existing, data)
            return {
                'uid': uid,
                'name': existing.name,
                'id': existing.id,
                'status': 'existing',
                'state': existing.state,
            }

        new_order = self.create(order_vals)
        if target_state == 'confirmed':
            new_order.action_confirm()
            self._process_offline_invoice_payment(new_order, data)
        self._post_offline_backend_note(new_order, data)
        return {
            'uid': uid,
            'name': new_order.name,
            'id': new_order.id,
            'status': 'created',
            'state': new_order.state,
        }

    def _post_offline_backend_note(self, order, data):
        """Post the backend note captured offline to the order's chatter."""
        note = (data.get('backend_note') or '').strip()
        if not note:
            return
        try:
            title = self.env._("Offline Backend Note")
            body = Markup("<p><strong>%s</strong></p><p>%s</p>") % (
                title,
                Markup("<br/>").join(note.splitlines()),
            )
            order.message_post(body=body, subject=title)
        except Exception as e:
            _logger.error("Failed to post offline backend note for %s: %s", order.display_name, str(e))

    def _create_offline_invoice_from_ordered_qty(self):
        """Create an invoice for the remaining ordered quantities.

        Backend pending orders may contain products configured with Delivered
        Quantities invoicing. The offline terminal is a pay-now flow, so it
        must invoice the remaining ordered quantity even when no delivery has
        been recorded yet.
        """
        self.ensure_one()
        invoice_vals = self._prepare_invoice()
        invoice_line_vals = []
        sequence = 0

        for line in self.order_line.filtered(lambda line: not line.display_type and not line.is_downpayment):
            qty_to_invoice = line.product_uom_qty - line.qty_invoiced
            if qty_to_invoice <= 0:
                continue
            for vals in line._prepare_invoice_lines_vals_list(
                sequence=sequence,
                quantity=qty_to_invoice,
            ):
                invoice_line_vals.append(Command.create(vals))
                sequence += 1

        if not invoice_line_vals:
            return self.env['account.move']

        invoice_vals['invoice_line_ids'] += invoice_line_vals
        return self.env['account.move'].with_context(
            default_move_type='out_invoice',
        ).create(invoice_vals)

    def _process_offline_invoice_payment(self, order, data):
        """ Create invoice (or reuse the existing pending one) and register
        the offline payment against it.

        For partial payments, the registered ``account.payment`` is created
        only for the amount actually tendered. The ``account.move`` keeps the
        unpaid balance as ``amount_residual`` and its ``payment_state`` becomes
        ``partial`` automatically.
        """
        try:
            # 0. For offline (pay-now) flow: mark delivery-policy lines as
            #    fully delivered so that Odoo's invoice_status dependency chain
            #    computes 'invoiced' correctly after payment. Offline sales are
            #    semantically equivalent to "take now / deliver now".
            for line in order.order_line.filtered(
                lambda line: not line.display_type
                and not line.is_downpayment
                and line.product_id.invoice_policy == 'delivery'
                and line.qty_delivered_method == 'manual'
                and line.qty_delivered < line.product_uom_qty
            ):
                line.qty_delivered = line.product_uom_qty

            # 1. Locate or create the invoice
            invoice = order.invoice_ids.filtered(
                lambda move: move.state != 'cancel' and move.payment_state not in ('paid', 'in_payment', 'reversed')
            )[:1]
            if not invoice:
                invoice = order._create_offline_invoice_from_ordered_qty()
                if not invoice:
                    raise UserError(self.env._("No invoiceable lines found for offline payment on %s", order.display_name))
            if invoice.state == 'draft':
                invoice.action_post()

            # 2. Determine the amount to register
            raw_paid = float(data.get('amount_paid') or 0.0)
            invoice_total = invoice.amount_total
            # For loaded backend orders, amount_paid is the cashier-entered
            # amount for this payment attempt, so cap only at the open residual.
            amount_to_pay = max(0.0, min(raw_paid, invoice.amount_residual))

            if amount_to_pay <= 0:
                _logger.info(
                    "Offline invoice %s posted with no payment registered "
                    "(amount_due=%s remains as balance).",
                    invoice.name, invoice_total,
                )
                return

            # 3. Register a payment for the (possibly partial) amount only
            journal = self.env['account.journal'].search([
                ('type', 'in', ('bank', 'cash')),
                ('company_id', '=', order.company_id.id)
            ], limit=1)

            if not journal:
                raise UserError(self.env._("No bank/cash journal found for company %s", order.company_id.display_name))

            payment_register = self.env['account.payment.register'].with_context(
                active_model='account.move',
                active_ids=invoice.ids,
            ).create({
                'amount': amount_to_pay,
                'journal_id': journal.id,
                'payment_date': fields.Date.context_today(self),
            })
            payment_register._create_payments()

            if amount_to_pay < invoice_total:
                _logger.info(
                    "Offline partial payment registered for %s: paid=%s, balance=%s",
                    invoice.name, amount_to_pay, invoice_total - amount_to_pay,
                )
        except Exception as e:
            _logger.error("Failed to finalize offline invoice/payment: %s", str(e))
            raise

    @api.model
    def get_pending_sale_orders(self):
        """Sale orders that still have an unpaid balance.

        This includes sale orders created from the offline terminal. Partial
        offline payments leave the invoice residual open, and those orders must
        remain visible so the cashier can collect the balance later.
        """
        domain = [
            ('state', 'not in', ('cancel',)),
        ]
        orders = self.search(domain, order='date_order desc', limit=200)
        result = []
        for order in orders:
            invoices = order.invoice_ids.filtered(lambda move: move.state != 'cancel')
            fully_paid = bool(invoices) and all(
                inv.payment_state in ('paid', 'in_payment', 'reversed') for inv in invoices
            )
            if fully_paid:
                continue
            residual = sum(invoices.mapped('amount_residual')) or order.amount_total
            result.append({
                'id': order.id,
                'name': order.name,
                'date': order.date_order and order.date_order.strftime('%Y-%m-%d %H:%M') or '',
                'state': order.state,
                'invoice_status': order.invoice_status,
                'partner_id': order.partner_id.id,
                'partner_name': order.partner_id.name or '',
                'partner_city': order.partner_id.city or '',
                'partner_zip': order.partner_id.zip or '',
                'amount_untaxed': order.amount_untaxed,
                'amount_tax': order.amount_tax,
                'amount_total': order.amount_total,
                'amount_residual': residual,
                'payment_term_id': order.payment_term_id.id or False,
                'lines': [{
                    'product_id': line.product_id.id,
                    'name': line.product_id.display_name or line.name,
                    'qty': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'tax_ids': line.tax_ids.ids,
                } for line in order.order_line if line.product_id],
            })
        return result

    @api.model
    def _get_offline_employees(self):
        """Return terminal employees with a flag indicating if a PIN is set.
        Never return the PIN itself or hashes to avoid offline brute-force attacks.
        """
        if 'hr.employee' not in self.env:
            return []
        employees = self.env['hr.employee'].search_read(
            [('company_id', 'in', [False, self.env.company.id])],
            ['id', 'name', 'job_id'],
        )
        emp_ids = [e['id'] for e in employees]
        emps_with_pin = set(self.env['hr.employee'].sudo().search([
            ('id', 'in', emp_ids),
            ('pin', '!=', False),
            ('pin', '!=', ''),
        ]).ids)
        for emp in employees:
            emp['pin'] = emp['id'] in emps_with_pin
            emp['has_pin'] = emp['pin']
        return employees

    @api.model
    def check_offline_employee_pin(self, employee_id, pin):
        """Securely verify employee PIN on the server without exposing PIN to the client."""
        if 'hr.employee' not in self.env or not employee_id or not pin:
            return False

        # Throttling to prevent brute-force attacks on employee PIN
        now = time.time()
        window = 60
        max_attempts = 5
        rate_limits = getattr(self.env.registry, '_offline_pin_rate_limits', None)
        if rate_limits is None:
            rate_limits = self.env.registry._offline_pin_rate_limits = collections.defaultdict(list)

        ip = request.httprequest.remote_addr if request and getattr(request, 'httprequest', None) else None
        rate_key = (employee_id, self.env.user.id, ip)

        # Remove attempts older than the window
        rate_limits[rate_key] = [t for t in rate_limits[rate_key] if now - t < window]
        if len(rate_limits[rate_key]) >= max_attempts:
            raise UserError(self.env._("Too many failed PIN attempts. Please try again later."))

        employee = self.env['hr.employee'].browse(employee_id)
        if not employee.exists():
            return False
        if employee.company_id and employee.company_id != self.env.company:
            return False

        stored_pin = str(employee.sudo().pin or '')
        input_pin = str(pin).strip()
        is_valid = bool(stored_pin and hmac.compare_digest(stored_pin, input_pin))
        if is_valid:
            rate_limits[rate_key] = []
            return True

        rate_limits[rate_key].append(now)
        return False

    @api.model
    def get_offline_data(self):
        """Return the initial data required to work offline."""
        products = self.env['product.product'].search_read(
            [('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', self.env.company.id)],
            ['id', 'display_name', 'lst_price', 'barcode', 'default_code', 'categ_id', 'taxes_id']
        )
        partners = self.env['res.partner'].search_read(  # pylint: disable=no-search-all
            [],
            ['id', 'name', 'email', 'phone', 'barcode', 'street', 'city', 'zip', 'country_id']
        )
        # Fetch all product categories for dynamic filtering. The full set is
        # required so the terminal keeps working offline; do not add a limit.
        categories = self.env['product.category'].search_read(  # pylint: disable=no-search-all
            [], ['id', 'name'])
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

        # Fetch payment terms from account.payment.term
        payment_terms = self.env['account.payment.term'].search_read(  # pylint: disable=no-search-all
            [], ['id', 'name'])

        # Fetch employees for the terminal login
        employees = self._get_offline_employees()
        # Fetch sales taxes
        taxes = self.env['account.tax'].search_read(
            [('type_tax_use', '=', 'sale'), '|',
             ('company_id', '=', False),
             ('company_id', '=', self.env.company.id)],
            ['id', 'name', 'amount', 'price_include', 'include_base_amount', 'amount_type']
        )
        # Keep only taxes that are valid for the current company.
        for product in products:
            tax_ids = product.get('taxes_id', [])
            if tax_ids:
                valid_taxes = self.env['account.tax'].search([
                    ('id', 'in', tax_ids),
                    '|',
                    ('company_id', '=', False),
                    ('company_id', '=', company.id),
                ])
                product['taxes_id'] = valid_taxes.ids
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
    def _sanitize_receipt_html(self, receipt_html):
        """Sanitize receipt HTML for wkhtmltopdf: keep style tags and inline styles,
        but strip script tags, iframes, embeds, forms, and all javascript event handlers."""
        if not receipt_html:
            return ''
        try:
            cleaner = Cleaner(
                scripts=True,
                javascript=True,
                comments=False,
                style=False,
                inline_style=False,
                links=False,
                meta=True,
                page_structure=False,
                processing_instructions=True,
                embedded=True,
                frames=True,
                forms=True,
                annoying_tags=False,
                remove_unknown_tags=False,
                safe_attrs_only=False,
            )
            doc = html.fromstring(receipt_html)
            cleaner(doc)
            # Remove all inline javascript attributes (onclick, onload, onerror, etc.)
            for el in doc.iter():
                attrs_to_remove = [
                    attr for attr in el.attrib
                    if attr.lower().startswith('on') or 'javascript:' in str(el.attrib[attr]).lower()
                ]
                for attr in attrs_to_remove:
                    del el.attrib[attr]
            return html.tostring(doc, encoding='unicode')
        except Exception:
            return html_sanitize(receipt_html, strip_style=False)

    @api.model
    def send_offline_receipt_mail(self, uid, receipt_html, email, subject=None, body=None):
        """ Generate PDF from receipt HTML and attach to chatter/send via email """
        _logger.info("Generating offline receipt PDF and sending email to %s for order %s", email, uid)
        if email and not email_normalize(email):
            raise UserError(self.env._("Invalid email address: %s", email))
        pdf_content = self.env['ir.actions.report']._run_pdf_engine_without_processing(
            'wkhtmltopdf',
            [self._sanitize_receipt_html(receipt_html)],
        )

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
                body=Markup("<p>%s</p>") % self.env._("Receipt sent to %s", email),
                attachment_ids=[attachment.id],
            )

        if email:
            safe_subject = self.env._('Transaction Receipt - %s', uid)
            if body:
                safe_body = plaintext2html(body)
            else:
                safe_body = Markup(
                    "<p>Dear Customer,</p><p>Please find attached your transaction receipt "
                    "for order <strong>%s</strong>.</p><p>Thank you for your business!</p>"
                ) % uid
            email_values = {
                'subject': safe_subject,
                'body_html': safe_body,
                'email_to': email,
                'attachment_ids': [Command.link(attachment.id)],
            }

            template = self.env.ref('offline_sale.mail_template_offline_receipt', raise_if_not_found=False)
            if not template:
                template = self.env['mail.template'].search([('model', '=', 'sale.order')], limit=1)
            if template:
                template.send_mail(
                    sale_order.id if sale_order else False,
                    force_send=True,
                    email_values=email_values,
                )

        return True

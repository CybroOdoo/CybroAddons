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
import json

from werkzeug.exceptions import NotFound

from odoo import fields
from odoo.http import Controller, request, route
from odoo.tools import BinaryBytes


class Tender(Controller):
    """Website pages of the tenders and bid submission."""

    @route('/edit_request', type="jsonrpc", auth="user", website=True)
    def edit_request(self, bid_id, **_kwargs):
        """Ask the tender responsible to allow editing a submitted bid."""
        vendor_bid = request.env['tender.bidding'].sudo().browse(int(bid_id)).exists()
        if (not vendor_bid or vendor_bid.vendor_id != request.env.user.partner_id
                or not vendor_bid._can_request_edit()):
            return {'success': False}
        vendor_bid.edit_request = True
        template = request.env.ref('advanced_tender_management.bid_edit_request_template').sudo()
        template.with_context(
            bid_link=f"{vendor_bid.get_base_url()}/odoo/tender.bidding/{vendor_bid.id}",
        ).send_mail(vendor_bid.id, force_send=True)
        return {'success': True}

    @staticmethod
    def _bid_prices(product_bid_list):
        """Prices typed on the tender page, by product id."""
        try:
            pairs = json.loads(product_bid_list or '[]')
            return {str(product_id): float(price or 0) for product_id, price in pairs}
        except (TypeError, ValueError):
            return {}

    @route('/bid/submit', type="http", auth="user", website=True, methods=['POST'])
    def submit_bit(self, **vals):
        """Create the bid of the current vendor, or update it after an
        approved edit request."""
        tender_record = request.env['tender.management'].sudo().browse(
            int(vals.get('tender_id') or 0)).exists()
        if not tender_record or tender_record.tender_state != 'bid_submission':
            raise NotFound()
        prices = self._bid_prices(vals.get('product_bid_list'))
        partner = request.env.user.partner_id
        existing_record = request.env['tender.bidding'].sudo().search(
            [('tender_id', '=', tender_record.id), ('vendor_id', '=', partner.id)], limit=1)
        if existing_record and existing_record.bidding_state != 'bid':
            return request.redirect(f'/show_tender/{tender_record.id}')
        attachment = request.env['ir.attachment']
        file = vals.get('att')
        if file and getattr(file, 'filename', False):
            attachment = attachment.sudo().create({
                'name': file.filename,
                'type': 'binary',
                'raw': BinaryBytes(file.read()),
                'res_model': partner._name,
                'res_id': partner.id,
            })
        if existing_record:
            existing_record.write({
                'qualification_stage': 'initial',
                'vendor_attachments_ids': [fields.Command.link(attachment.id)] if attachment else [],
                'tender_bid_products_ids': [fields.Command.update(line.id, {
                    'product_price': 0 if line.display_type else prices.get(
                        str(line.product_id.id), 0.0),
                }) for line in existing_record.tender_bid_products_ids],
            })
            bid = existing_record
        else:
            Bidding = request.env['tender.bidding'].sudo()
            bid = Bidding.create({
                'vendor_id': partner.id,
                'tender_id': tender_record.id,
                'bidding_date': fields.Date.context_today(tender_record),
                'vendor_attachments_ids': [fields.Command.link(attachment.id)] if attachment else [],
                'tender_bid_products_ids': Bidding._prepare_bid_line_commands(
                    tender_record, prices),
            })
        bid._mark_submitted()
        return request.render('advanced_tender_management.bid_submitted_thankyou_page')

    @route('/tender_management_snippet', type="jsonrpc", auth="public", website=True)
    def get_tenders(self):
        """Tenders open for bidding; portal vendors only see their categories."""
        user = request.env.user
        domain = [('tender_state', '=', 'bid_submission')]
        if user._is_portal():
            domain.append(('tender_category_id', 'in', user.partner_id.tender_category_ids.ids))
        Tender = request.env['tender.management'].sudo()
        tenders = Tender.search_read(
            domain,
            ['name', 'bid_start_date', 'bid_end_date', 'tender_type', 'tender_category_id',
             'create_date', 'tender_start_date', 'tender_end_date'],
            order='create_date desc')
        type_labels = dict(Tender._fields['tender_type']._description_selection(request.env))
        for tender in tenders:
            tender['tender_type'] = type_labels.get(tender['tender_type'])
        return tenders

    @route('/edit_request_success', type="http", auth="public", website=True)
    def render_edit_request_success_page(self):
        """Confirmation page of an edit request."""
        return request.render('advanced_tender_management.edit_request_submitted_page')

    @route('/show_tender/<int:tender_id>', type="http", auth="public", website=True)
    def render_tender_details(self, tender_id):
        """Details of a tender with the bid form or the vendor's bid."""
        tender_record = request.env['tender.management'].sudo().browse(tender_id).exists()
        if not tender_record:
            raise NotFound()
        partner = request.env.user.partner_id
        data = {
            'record': tender_record,
            'tender_products': request.env['tender.product.lines'].sudo().search_read(
                [('id', 'in', tender_record.tender_product_line_ids.ids)]),
            'vendor_id': partner.id,
            'has_registered': partner in tender_record.registered_vendors_ids,
        }
        if data['has_registered']:
            record = request.env['tender.bidding'].sudo().search(
                [('vendor_id', '=', partner.id), ('tender_id', '=', tender_record.id)], limit=1)
            data['bid_record'] = record
            data['bid_product_lines'] = record.tender_bid_products_ids
        return request.render('advanced_tender_management.tender_details', data)

    @route('/tender_management', type='http', auth='public', website=True)
    def render_tender_template(self):
        """Website page with the tenders snippet."""
        return request.render('advanced_tender_management.tender_snippet_template')

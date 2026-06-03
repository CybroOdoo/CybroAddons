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
import ast
import base64
from datetime import date
from odoo import fields
from odoo.http import Controller, request, route


class Tender(Controller):
    """Class for tender management"""

    @route('/edit_request', type="json", auth="public", website=True)
    def edit_request(self, **vals):
        """Function for dealing with edit requests"""
        vendor_bid = request.env['tender.bidding'].sudo().browse(
            int(vals['bid_id']))
        vendor_bid.edit_request = True
        base_url = request.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        menu_id = request.env.ref(
            'advanced_tender_management.tender_bidding_menu').id
        action_id = request.env.ref(
            'advanced_tender_management.tender_bidding_action').id
        company_id = request.env.user.company_id.id
        db_name = request.env.cr.dbname
        context = {
            'bid_link': f"""{base_url}/web?db={db_name}#id={vendor_bid.id}
            &cids={company_id}
            &menu_id={menu_id}&action={action_id}
            &model=tender.bidding&view_type=form""",
        }
        template = request.env.ref(
            'advanced_tender_management.bid_edit_request_template').sudo()
        template.with_context(**context).send_mail(
            vendor_bid.id, force_send=True)

    @route('/bid/submit', type="http", auth="public", website=True)
    def submit_bit(self, **vals):
        """Function to submit vendor's bid and creating corresponding
         bidding record"""
        tender_record = request.env['tender.management'].sudo().browse(
            int(vals['tender_id']))
        tender = tender_record.tender_product_line_ids
        product_bid_list = ast.literal_eval(vals['product_bid_list'])
        product_bid_dict = {str(x[0]): x[1] for x in product_bid_list}
        current_partner_id = request.env.user.partner_id
        file = vals.get('att')
        attachment_id = False
        if file:
            file_name = file.filename
            attachment_id = request.env['ir.attachment'].sudo().create({
                'name': file_name,
                'type': 'binary',
                'datas': base64.b64encode(file.read()),
                'res_model': current_partner_id._name,
                'res_id': current_partner_id.id
            })
        existing_record = request.env['tender.bidding'].sudo().search(
            [('tender_id', '=', tender_record.id), (
                'vendor_id', '=', current_partner_id.id)])
        if existing_record:
            existing_record.qualification_stage = 'initial'
            existing_record.update({
                'tender_bid_products_ids': [
                    (fields.Command.update(rec.id, {
                        'product_price': 0 if rec.display_type else int(
                            product_bid_dict.get(str(rec.product_id.id), 0))})) for rec in
                    existing_record.tender_bid_products_ids]
            })
            bid = existing_record
        else:
            bid = request.env['tender.bidding'].sudo().create({
                'vendor_id': current_partner_id.id,
                'tender_id': int(vals['tender_id']),
                'bidding_state': 'pre_qualification',
                'bidding_date': date.today(),
                'vendor_attachments_ids': [(4, attachment_id.id)] if attachment_id else [],
                'tender_bid_products_ids': [(fields.Command.create({
                    'name': rec.name,
                    'product_id': rec.product_id.id,
                    'product_qty': rec.product_qty,
                    'display_type': rec.display_type,
                    'product_price': 0 if rec.display_type else int(
                        product_bid_dict.get(str(rec.product_id.id), 0)), }
                )) for rec in tender]
            })
        bid.bidding_state = 'bid_close'
        template = request.env.ref(
            'advanced_tender_management.bid_submission_template'
                                   ).sudo()
        template.send_mail(bid.id, force_send=True)
        tender_record.write({
            'registered_vendors_ids': [
                (fields.Command.link(current_partner_id.id))]
        })
        return request.render(
            'advanced_tender_management.bid_submitted_thankyou_page')

    @route('/tender_management_snippet', type="json",
           auth="public", website=True)
    def get_tenders(self):
        """Function to retrieve all tenders in bid submission stage"""
        user = request.env.user
        if user.sudo().user_has_groups('base.group_portal'):
            tender_category_ids = user.partner_id.tender_category_ids.ids
            search_filter = [('tender_category_id', 'in', tender_category_ids),
                             ('tender_state', '=', 'bid_submission')]
        else:
            search_filter = [('tender_state', '=', 'bid_submission')]
        tenders = request.env['tender.management'].sudo().search_read(
            search_filter,
            ['name', 'bid_start_date', 'bid_end_date', 'tender_type',
             'tender_category_id',
             'create_date', 'tender_start_date', 'tender_end_date'],
            order='create_date desc')
        tender_type_selection = request.env['tender.management']._fields[
            'tender_type'].selection
        for tender in tenders:
            tender_type_string = dict(tender_type_selection).get(
                tender['tender_type'])
            tender['tender_type'] = tender_type_string
        return tenders

    @route('/edit_request_success', type="http",
           auth="public", website=True)
    def render_edit_request_success_page(self):
        """Function to render edit request submit page"""
        return request.render(
            'advanced_tender_management.edit_request_submitted_page')

    @route('/show_tender/<int:id>', type="http",
           auth="public", website=True)
    def render_tender_details(self, id):
        """Function to render the chosen tender details"""
        current_vendor_id = request.env.user.partner_id.id
        tender_record = request.env['tender.management'].sudo(
        ).browse(id)
        registered_vendors = tender_record.registered_vendors_ids.ids
        tender_product_line_records = request.env[
            'tender.product.lines'].sudo().search_read(
            [('id', 'in', tender_record.tender_product_line_ids.ids)])
        data = {'record': tender_record,
                'tender_products': tender_product_line_records,
                'vendor_id': current_vendor_id, 'has_registered': False
                }
        if current_vendor_id in registered_vendors:
            data['has_registered'] = True
            record = request.env['tender.bidding'].sudo().search(
                [('vendor_id', '=', current_vendor_id),
                 ('tender_id', '=', tender_record.id)])
            data['bid_record'] = record
            data['bid_product_lines'] = record.tender_bid_products_ids
        return request.render(
            'advanced_tender_management.tender_details', data)

    @route('/tender_management', type='http', auth='public', website=True)
    def render_tender_template(self):
        """Function to render website snippet page"""
        return request.render(
            'advanced_tender_management.tender_snippet_template')

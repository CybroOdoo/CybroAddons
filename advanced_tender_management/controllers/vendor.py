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

from odoo import fields
from odoo.exceptions import UserError
from odoo.http import Controller, request, route
from odoo.tools import BinaryBytes
from odoo.tools.image import binary_to_image


class Vendor(Controller):
    """Vendor registration from the website."""

    @route('/vendor_register', type='http', auth='public', website=True)
    def render_vendor_template(self):
        """Render the vendor registration form."""
        return request.render('advanced_tender_management.vendor_register_template', {
            'tender_category': request.env['tender.category'].sudo().search_read(
                [], fields=['id', 'name']),
            'countries': request.env['res.country'].sudo().search_read([], fields=['name']),
            'states': request.env['res.country.state'].sudo().search_read([], fields=['name']),
        })

    @staticmethod
    def _to_id(value):
        """Record id from a form value, or False when empty."""
        try:
            return int(value) if value else False
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _logo(upload):
        """Uploaded logo as a binary value, or False when it is not an image."""
        content = upload.read() if upload and hasattr(upload, 'read') else b''
        if not content:
            return False
        try:
            binary_to_image(content)
        except UserError:
            return False
        return BinaryBytes(content)

    @route('/vendor_register/submit', type='http', auth='public', website=True, methods=['POST'])
    def register_vendor(self, **post):
        """Create the vendor, then grant portal access or notify the
        approval users, depending on the settings."""
        category_ids = [self._to_id(cat_id)
                        for cat_id in request.httprequest.form.getlist('category')]
        vendor = request.env['res.partner'].sudo().create({
            'name': post['name'],
            'street': post.get('street'),
            'street2': post.get('street2'),
            'state_id': self._to_id(post.get('state')),
            'city': post.get('city'),
            'country_id': self._to_id(post.get('country')),
            'zip': post.get('zip'),
            'is_vendor': True,
            'phone': post.get('phone'),
            'email': post.get('email'),
            'website': post.get('website'),
            'comment': post.get('note'),
            'tender_category_ids': [fields.Command.set([cat for cat in category_ids if cat])],
            'image_1920': self._logo(post.get('company_logo')),
        })
        company = request.env.company
        params = request.env['ir.config_parameter'].sudo()
        request.env.ref('advanced_tender_management.vendor_registration_template').sudo().send_mail(
            vendor.id, force_send=True, email_values={'email_from': company.email})
        is_auto_approval = params.get_bool('advanced_tender_management.auto_approval')
        approval_user_ids = json.loads(
            params.get_str('advanced_tender_management.manual_approval_users_ids') or '[]')
        if is_auto_approval:
            Users = request.env['res.users'].sudo()
            if vendor.email and not Users.search_count([('login', '=', vendor.email)]):
                # Creating the user emails the vendor an invitation to set
                # their password (auth_signup), so they can log in to bid.
                Users.create({
                    'name': vendor.name,
                    'login': vendor.email,
                    'partner_id': vendor.id,
                    'group_ids': [fields.Command.set([request.env.ref('base.group_portal').id])],
                })
        elif approval_user_ids:
            emails = request.env['res.users'].sudo().browse(approval_user_ids).exists().mapped(
                'partner_id.email')
            template = request.env.ref(
                'advanced_tender_management.approval_user_notification_mail_template').sudo()
            template.with_context(
                contact_link=f"{vendor.get_base_url()}/odoo/res.partner/{vendor.id}",
            ).send_mail(vendor.id, force_send=True, email_values={
                'email_to': ','.join(email for email in emails if email),
                'email_from': company.email,
            })
        return request.render('advanced_tender_management.register_thankyou_page')

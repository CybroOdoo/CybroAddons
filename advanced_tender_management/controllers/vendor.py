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
from odoo import fields
from odoo.http import Controller, request, route


class Vendor(Controller):
    """Class for vendor registration"""

    @route('/vendor_register', type='http', auth='public', website=True)
    def render_vendor_template(self):
        """Function to render vendor registration form"""
        tender_categories = (request.env['tender.category'].sudo().search_read
                             ([],fields=['id', 'name']))
        all_countries = request.env['res.country'].search_read([], fields=['name'])
        all_states = request.env['res.country.state'].search_read([], fields=['name'])
        values = {
            'tender_category': tender_categories,
            'countries': all_countries,
            'states': all_states
        }
        return request.render('advanced_tender_management.vendor_register_template', values)

    @route('/vendor_register/submit', type='http', auth='public', website=True)
    def register_vendor(self, **post):
        """Function to register vendor"""
        filestorage = post['company_logo']
        image_data = filestorage.read()
        encoded_image = base64.b64encode(image_data)
        vendor = request.env['res.partner'].sudo().create({
            'name': post['name'],
            'street': post['street'],
            'street2': post['street2'],
            'state_id': post['state'],
            'city': post['city'],
            'country_id': post['country'],
            'zip': post['zip'],
            'is_company': True if post['vendor_type'] == 'company' else False,
            'is_vendor': True,
            'phone': post['phone'],
            'email': post['email'],
            'website': post['website'],
            'tender_category_ids': [(fields.Command.link(int(cat_id))) for cat_id in
                                    ast.literal_eval(post['many2many_field'])],
            'image_1920': encoded_image
        })
        company = request.env.user.company_id
        template = request.env.ref('advanced_tender_management.vendor_registration_template').sudo()
        template.send_mail(vendor.id, force_send=True, email_values={'email_from': company.email})
        is_auto_approval = request.env['ir.config_parameter'].sudo().get_param(
            'advanced_tender_management.auto_approval')
        approval_users_str = request.env['ir.config_parameter'].sudo().get_param(
            'advanced_tender_management.manual_approval_users_ids'
        )
        approval_users = ast.literal_eval(approval_users_str) if approval_users_str else False
        if not is_auto_approval and approval_users:
            approval_users_email = request.env['res.users'].sudo().browse(approval_users).mapped(
                'partner_id').mapped('email')
            emails = ",".join(approval_users_email)
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            menu_id = request.env.ref('advanced_tender_management.res_partner_menu').id
            action_id = request.env.ref('advanced_tender_management.res_partner_action').id
            db_name = request.env.cr.dbname
            context = {
                'contact_link': f"""{base_url}/web?db={db_name}#id={vendor.id}&cids={company.id}
                &menu_id={menu_id}&action={action_id}&model=res.partner&view_type=form""",
            }
            template = request.env.ref('advanced_tender_management.approval_user_notification_mail_template')
            template.sudo().with_context(**context).send_mail(vendor.id, force_send=True,
                                                       email_values={'email_to': emails, 'email_from': company.email})

        elif is_auto_approval:
            portal_user = request.env.ref('base.group_portal').sudo()
            request.env['res.users'].sudo().create({
                'name': post['name'],
                'login': post['email'],
                'partner_id': vendor.id,
                'groups_id': [(6, 0, [portal_user.id])]
            })

        return request.render('advanced_tender_management.register_thankyou_page')

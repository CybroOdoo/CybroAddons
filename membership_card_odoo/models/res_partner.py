# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rahna Rasheed (<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    """ Inherit the res. partner to make existing field required. """
    _inherit = 'res.partner'

    image_1920 = fields.Image(max_width=1920, max_height=1920,
                              required=True, string="Image",
                              help="The field hold the image of customer")
    phone = fields.Char(unaccent=False, required=True,
                        string="Phone",
                        help="The field hold the phone number of customer")
    function = fields.Char(string='Job Position',
                           help="The field hold the job position  of customer")

    def server_action_get_card(self):
        """ Used to fetch data from res. partner to pass in template"""
        partner_id = self.env['res.partner'] \
            .browse(self.env.context.get('active_ids'))
        company_id = self.env.company
        if self.free_member or partner_id.member_lines:
            data = {
                'name': partner_id.name,
                'image': partner_id.image_1920,
                'phone': partner_id.phone,
                'function': partner_id.function,
                'free_member': partner_id.free_member,
                'membership_product': partner_id.member_lines.
                mapped('membership_id.name'),
                'start_date': partner_id.membership_start,
                'end_date': partner_id.membership_stop,
                'company_name': company_id.name,
                'company_address': company_id.street,
                'city': company_id.city,
                'country': company_id.country_id.name,
                'state': company_id.state_id.name,
                'company_email': company_id.email,
                'company_phone': company_id.phone,
                'website': company_id.website,
            }
            return self.env.ref('membership_card_odoo.action_membership_card'). \
                report_action(None, data=data)
        else:
            raise ValidationError(
                'Need to buy membership inorder to print membership card')

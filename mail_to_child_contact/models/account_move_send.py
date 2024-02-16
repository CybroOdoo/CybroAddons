# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
###############################################################################
from odoo import models, tools
from odoo.addons.account.wizard.account_move_send import AccountMoveSend


class AccountMoveSend(models.TransientModel):
    """Inherited the account move send model to addd functionality"""
    _inherit = 'account.move.send'

    def _get_default_mail_partner_ids(self, move, mail_template, mail_lang):
        """To pass default partner_ids to mail """
        partners = self.env['res.partner'].with_company(move.company_id)
        if mail_template.email_to:
            for mail_data in tools.email_split(mail_template.email_to):
                partners |= partners.find_or_create(mail_data)
        if mail_template.email_cc:
            for mail_data in tools.email_split(mail_template.email_cc):
                partners |= partners.find_or_create(mail_data)
        if mail_template.partner_to:
            partner_to = self._get_mail_default_field_value_from_template(
                mail_template, mail_lang, move, 'partner_to')
            partner_ids = mail_template._parse_partner_to(partner_to)
            partner_to_ids = self.env['res.partner'].sudo().search(
                [('commercial_partner_id', '=', int(partner_ids[0]))])
            for rec in partner_to_ids:
                partner_ids.append(rec.id)
            partners |= self.env[
                'res.partner'].sudo().browse(partner_ids).exists()
        return partners

    AccountMoveSend._get_default_mail_partner_ids = \
        _get_default_mail_partner_ids

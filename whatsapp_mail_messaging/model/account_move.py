# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from itertools import groupby

from odoo import models, _
from odoo.exceptions import UserError


class Account(models.Model):
    _inherit = 'account.move'

    def action_send_whatsapp(self):
        compose_form_id = self.env.ref(
            'whatsapp_mail_messaging.whatsapp_message_wizard_form').id
        ctx = dict(self.env.context)
        message = "Hi" + " " + self.partner_id.name + ',' + '\n' + "Here is your invoice" + ' ' + self.name + ' ' + "amounting" + ' ' + str(
            self.amount_total) + self.currency_id.symbol + ' ' + "from " + self.company_id.name + ". Please remit payment at your earliest convenience. " + '\n' + \
                  "Please use the following communication for your payment" + ' ' + self.name
        ctx.update({
            'default_message': message,
            'default_partner_id': self.partner_id.id,
            'default_mobile': self.partner_id.mobile,
            'default_image_1920': self.partner_id.image_1920,
        })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'whatsapp.message.wizard',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def check_customers(self, partner_ids):
        partners = groupby(partner_ids)
        return next(partners, True) and not next(partners, False)

    def action_whatsapp_multi(self):
        account_move_ids = self.env['account.move'].browse(
            self.env.context.get('active_ids'))
        partner_ids = []
        for account_move in account_move_ids:
            partner_ids.append(account_move.partner_id.id)
        partner_check = self.check_customers(partner_ids)
        if partner_check:
            account_move_numbers = account_move_ids.mapped('name')
            account_move_numbers = "\n".join(account_move_numbers)
            compose_form_id = self.env.ref(
                'whatsapp_mail_messaging.whatsapp_message_wizard_form').id
            ctx = dict(self.env.context)
            message = "Hi" + " " + self.partner_id.name + ',' + '\n' + "Your Orders are" + '\n' + account_move_numbers + \
                      ' ' + "is ready for review.Do not hesitate to contact us if you have any questions."
            ctx.update({
                'default_message': message,
                'default_partner_id': account_move_ids[0].partner_id.id,
                'default_mobile': account_move_ids[0].partner_id.mobile,
                'default_image_1920': account_move_ids[0].partner_id.image_1920,
            })
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'whatsapp.message.wizard',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
                'context': ctx,
            }
        else:
            raise UserError(_(
                'It seems that you have selected Invoices of more than one customer.'
                'Try select Invoices of an unique customer'))

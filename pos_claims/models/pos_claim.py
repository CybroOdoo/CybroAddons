# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import SUPERUSER_ID
from openerp import models, fields, api, _


class PosClaims(models.Model):
    _name = 'pos.claims'
    _description = "Claim"
    _inherit = ['mail.thread']

    name = fields.Many2one('pos.order', string='Claim Order', required=True)
    ref_name = fields.Char(string="Claim Ticket", readonly=True, default=lambda self: _('New'))
    claim_product = fields.Many2one('pos.order.line', string="Product",
                                    domain="[('order_id', '=',name)]", required=True)
    claim_qty = fields.Integer(string="Quantity")
    claim_date = fields.Datetime(string='Claim Date', default=fields.Datetime.now, required=True)
    session_id = fields.Many2one('pos.session', string='Session', related='name.session_id')
    user_id = fields.Many2one('res.users', string="Assigned Person")
    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High')], 'Priority')
    partner_id = fields.Many2one('res.partner', string='Partner', required=1)
    partner_phone = fields.Char(string='Phone')
    partner_email = fields.Char(string='Email', related='partner_id.email')
    description = fields.Text(string='Description')
    user_fault = fields.Char(string='Trouble Responsible')
    cate_id = fields.Selection([('0', 'Factual Claims'), ('1', 'Value Claims'), ('2', 'Policy Claim')], 'Category Id',
                               )
    date_action_next = fields.Datetime(string='Next Action Date')
    action_next = fields.Char(string='Next Action')
    resolution = fields.Text(string='Resolution')
    cause = fields.Text(string='Root Cause')
    type_action = fields.Selection([('correction', 'Corrective Action'),
                                    ('prevention', 'Preventive Action')], 'Action Type')
    date_closed = fields.Datetime('Closed')
    state = fields.Selection([
        ('new', 'New'),
        ('assigned', 'Assigned'),
        ('feedback', 'Feedback'),
        ('paid', 'Paid'),
        ('settle', 'Settled'),
        ('reject', 'Rejected'),
    ], default='new')

    def create_from_ui(self, cr, uid, claim, context=None):
        """ create claims from the point of sale ui. """
        claim_id = self.create(cr, uid, claim, context=context)
        return claim_id

    @api.model
    def create(self, vals):
        if vals.get('ref_name', 'New') == 'New':
            vals['ref_name'] = self.env['ir.sequence'].next_by_code('pos.claims') or 'New'

        if vals.get('user_id'):
            vals['state'] = 'assigned'
        result = super(PosClaims, self).create(vals)
        result.claim_ticket()
        return result

    @api.multi
    def write(self, vals):
        if vals.get('user_id'):
            vals['state'] = 'assigned'
        result = super(PosClaims, self).write(vals)
        return result

    @api.multi
    def action_settle(self):
        self.state = 'settle'

    @api.multi
    def action_reject(self):
        self.state = 'reject'

    @api.one
    def claim_ticket(self):
        su_id = self.env['res.partner'].browse(SUPERUSER_ID)
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('pos_claims', 'email_template_edi_pos_ticket')[1]
        except ValueError:
            template_id = False
        email_template_obj = self.env['mail.template'].browse(template_id)
        if template_id:
            values = email_template_obj.generate_email(self.id, fields=None)
            values['email_from'] = su_id.email
            values['email_to'] = self.partner_id.email
            values['res_id'] = False
            mail_mail_obj = self.env['mail.mail']
            msg_id = mail_mail_obj.create(values)
            if msg_id:
                msg_id.send()

    @api.multi
    def action_sent(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('pos_claims', 'email_template_edi_pos_claims')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'pos.claims',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        if self._context.get('default_model') == 'pos.claims' and self._context.get('default_res_id'):
            order = self.env['pos.claims'].browse([self._context['default_res_id']])
            if order.state == 'assigned':
                order.state = 'feedback'
            order.sent = True
            self = self.with_context(mail_post_autofollow=True)
        return super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)








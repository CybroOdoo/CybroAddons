from odoo import api, fields, models


class sale_discount(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('waiting', 'Waiting Approval'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.multi
    def action_confirm(self):
        discnt = 0.0
        no_line = 0.0
        for order in self:
            if order.company_id.discount_approval:
                print order.company_id.discount_approval
                for line in order.order_line:
                    no_line += 1
                    discnt += line.discount
                discnt = (discnt / no_line)
                if order.company_id.limit_discount and discnt > order.company_id.limit_discount:
                    order.state = 'waiting'
                    return True
            order.state = 'sale'
            order.confirmation_date = fields.Datetime.now()
            if self.env.context.get('send_email'):
                self.force_quotation_send()
            order.order_line._action_procurement_create()
        if self.env['ir.values'].get_default('sale.config.settings', 'auto_done_setting'):
            self.action_done()
        return True

    @api.multi
    def action_approve(self):
        for order in self:
            order.state = 'sale'
            order.confirmation_date = fields.Datetime.now()
            if self.env.context.get('send_email'):
                self.force_quotation_send()
            order.order_line._action_procurement_create()
        if self.env['ir.values'].get_default('sale.config.settings', 'auto_done_setting'):
            self.action_done()
        return True




class Company(models.Model):
    _inherit = 'res.company'

    limit_discount = fields.Float(string="Discount limit requires approval %",
                                  help="Discount after which approval of sale is required.")
    discount_approval = fields.Boolean("Force two levels of approvals",
                                       help='Provide a double validation mechanism for sale exceeding minimum discount.')

    @api.multi
    def set_default_discount(self):
        if self.discount_approval and self.discount_approval != self.company_id.discount_approval:
            self.company_id.write({'discount_approval': self.discount_approval})
        if self.limit_discount and self.limit_discount != self.company_id.limit_discount:
            self.company_id.write({'limit_discount': self.limit_discount})


class AccountDiscountSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    limit_discount = fields.Float(string="Discount limit requires approval in %",
                                  related='company_id.limit_discount',
                                  help="Discount after which approval of sale is required.")
    discount_approval = fields.Boolean("Force two levels of approval on discount",
                                       related='company_id.discount_approval',
                                       help='Provide a double validation mechanism for sale exceeding maximum discount limit.')

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            company = self.company_id
            self.discount_approval = company.discount_approval
            self.limit_discount = company.limit_discount
            res = super(AccountDiscountSettings, self).onchange_company_id()
            return res
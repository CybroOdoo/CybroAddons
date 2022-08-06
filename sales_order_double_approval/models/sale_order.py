from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = ['sale.order']

    state = fields.Selection(selection_add=
                             [('to_approve', 'To Approve'),
                              ('sent',)], ondelete={'to_approve': 'cascade'})

    def button_approve(self):
        self.write({'state': 'sale'})

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.company_id.so_double_validation:
            if self.env['ir.config_parameter'].sudo().get_param('sales_order_double_approval.so_approval'):
                if self.amount_total > float(
                        self.env['ir.config_parameter'].sudo().get_param('sales_order_double_approval.so_min_amount')):
                    if self.user_has_groups('sales_team.group_sale_manager'):
                        self.state = 'sale'
                    else:
                        self.state = 'to_approve'
        return res

    def action_cancel(self):
        self.state = 'cancel'

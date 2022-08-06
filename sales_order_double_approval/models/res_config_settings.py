from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    so_approval = fields.Boolean(string="Sale Order Approval")
    so_min_amount = fields.Monetary(string="Minimum Amount")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['so_approval'] = self.env['ir.config_parameter'].sudo().get_param(
            "sales_order_double_approval.so_approval", default="")
        res['so_min_amount'] = self.env['ir.config_parameter'].sudo().get_param(
            "sales_order_double_approval.so_min_amount", default="")
        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].set_param("sales_order_double_approval.so_approval",
                                                  self.so_approval or '')
        self.env['ir.config_parameter'].set_param("sales_order_double_approval.so_min_amount",
                                                  self.so_min_amount or '')
        super(ResConfigSettings, self).set_values()

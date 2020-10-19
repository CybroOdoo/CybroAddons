from odoo import api, fields, models, _
import datetime
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    active_standard_price = fields.Boolean(string='Standard price as a code',
                                           help="check this box to show cost on the product labels as code")
    active_ref = fields.Boolean(string='Show product reference ',
                                help="check this box to show product reference as in product labels")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        active_standard_price = params.get_param('active_standard_price', default=False)
        active_ref = params.get_param('active_ref', default=False)
        res.update(
            active_standard_price=bool(active_standard_price),
            active_ref=bool(active_ref),
        )
        return res


    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("active_standard_price",
                                                         self.active_standard_price)
        self.env['ir.config_parameter'].sudo().set_param("active_ref",
                                                         self.active_ref)


class CustomizeBarcodeGenerator(models.Model):
    _name = 'barcode.code'
    name = fields.Char(default='Numeric Code')
    code_for_zero = fields.Char(string=' 0 ', required=True, limit=1, size=1,
                                default='a', help="insert substitute code ")
    code_for_one = fields.Char(string='1 ', required=True, limit=1, size=1,
                               default='b', help="insert substitute code ")
    code_for_two = fields.Char(string='2 ', required=True, limit=1, size=1,
                               default='c', help="insert substitute code ")
    code_for_three = fields.Char(string='3 ', required=True, limit=1, size=1,
                                 default='d', help="insert substitute code ")
    code_for_four = fields.Char(string='4 ', required=True, limit=1, size=1,
                                default='e', help="insert substitute code ")
    code_for_five = fields.Char(string='5 ', required=True, limit=1, size=1,
                                default='f', help="insert substitute code ")
    code_for_six = fields.Char(string='6 ', required=True, limit=1, size=1,
                               default='g', help="insert substitute code ")
    code_for_seven = fields.Char(string='7 ', required=True, limit=1, size=1,
                                 default='h', help="insert substitute code ")
    code_for_eight = fields.Char(string='8 ', required=True, limit=1, size=1,
                                 default='i', help="insert substitute code ")
    code_for_nine = fields.Char(string='9 ', required=True, limit=1, size=1,
                                default='j', help="insert substitute code ")
    active_check = fields.Boolean(string="Active", default=False)
    date_check = fields.Datetime(default=datetime.datetime.today(), string="Date")


    @api.onchange('active_check')
    def onchange_active_check(self):
        for i in self.search([]):
            if i.active_check == self.active_check and self.active_check:
                self.active_check = False
                raise UserError(_("Only one rule for code can be active at a time"))


class CostToCode(models.Model):
    _inherit = 'product.product'
    cost_in_code = fields.Char(string='Cost in code', compute='get_cost_in_code')


    def get_cost_in_code(self):
        code = self.env['barcode.code'].sudo().search([('active_check', '=', True)])
        active_check = self.env['ir.config_parameter'].sudo().search([('key','=','active_standard_price'),('value','=',True)])
        if active_check:
            if code:
                real = str(self.standard_price).split('.')[0]
                for i in real:
                    if i == '0':
                        real = real.replace('0', code.code_for_zero)
                    elif i == '1':
                        real = real.replace('1', code.code_for_one)
                    elif i == '2':
                        real = real.replace('2', code.code_for_two)
                    elif i == '3':
                        real = real.replace('3', code.code_for_three)
                    elif i == '4':
                        real = real.replace('4', code.code_for_four)
                    elif i == '5':
                        real = real.replace('5', code.code_for_five)
                    elif i == '6':
                        real = real.replace('6', code.code_for_six)
                    elif i == '7':
                        real = real.replace('7', code.code_for_seven)
                    elif i == '8':
                        real = real.replace('8', code.code_for_eight)
                    else:
                        real = real.replace('9', code.code_for_nine)
                return real
            else:
                return " "
        else:
            return " "

    def get_product_ref(self):
        active_check = self.env['ir.config_parameter'].sudo().search([('key','=','active_ref'),('value','=',True)])
        if active_check:
            return self.default_code
        else:
            return " "

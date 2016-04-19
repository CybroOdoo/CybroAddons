from openerp import models, fields,api


class RepEmployee(models.Model):
    _inherit = 'hr.employee'

    rep = fields.Boolean('Medical Representative')
    commission = fields.Float('Commission')
    target = fields.Integer('Target')

    @api.one
    def _get_total_sale(self):
        total = 0.0
        for EACH_Doctor in self.env['res.partner'].search([('doctor', '=', True)]):
            if EACH_Doctor.related_rep.id == self.id:
                total += EACH_Doctor.total_sale
        self.total_sale = total
    total_sale = fields.Integer('Total sale', compute='_get_total_sale')

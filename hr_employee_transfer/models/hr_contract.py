from odoo import models, fields, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    from_transfer = fields.Boolean(string='Transferred', default=False)
    emp_transfer = fields.Many2one('employee.transfer', string='Transferred Employee')

    @api.model
    def create(self, vals):
        res = super(HrContract, self).create(vals)
        if res.emp_transfer:
            self.env['employee.transfer'].browse(res.emp_transfer.id).write({'state': 'done'})
        return res

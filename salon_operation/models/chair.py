from openerp import models, fields,api,http,SUPERUSER_ID


class Chairs(models.Model):
    _name = 'salon.chair'

    name = fields.Char()
    related_employee = fields.Many2one('hr.employee', string='Related Employee')

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'This chair is already exist !'),
        ('related_employee_unique', 'unique(related_employee)', 'This person was reserved for another chair !')]



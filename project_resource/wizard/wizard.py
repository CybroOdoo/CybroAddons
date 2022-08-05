""" Creating Wizard to add the period to get the free resource"""
from odoo import models, fields


class FreeResource(models.TransientModel):
    """Wizard to add the period to get the free resource"""
    _name = 'free.resource'

    date_from = fields.Date(string="Start Date")
    date_to = fields.Date(string="End Date")

    def get_free_resource(self):
        """get the list of free resource at the given period
        """
        date_from = self.date_from
        date_to = self.date_to
        if date_from and date_to:
            resource_ids = self.env['project.task'].\
                get_free_resource_ids(date_from, date_to)
        else:
            resource_ids = []

        return {
            'name': 'Free Resource',
            'view_mode': 'tree,form',
            'target': 'main',
            'res_model': 'res.users',
            'views': [
                (self.env.ref('project_resource.free_user_tree').id, 'tree'),
                (self.env.ref('project_resource.free_user_form').id, 'form')],
            'type': 'ir.actions.act_window',
            'domain': [('id', 'not in', resource_ids), ('share', '=', False)],
             }

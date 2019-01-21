from odoo import models, api, fields


class WhatsappSendMessage(models.TransientModel):

    _name = 'whatsapp.message.wizard'

    user_id = fields.Many2one('res.partner', string="Recipient")
    mobile = fields.Char(related='user_id.mobile', required=True)
    message = fields.Text(string="message", required=True)

    def send_message(self):
        if self.message and self.mobile:
            message_string = ''
            message = self.message.split(' ')
            for msg in message:
                message_string = message_string + msg + '%20'
            message_string = message_string[:(len(message_string) - 3)]
            return {
                'type': 'ir.actions.act_url',
                'url': "https://api.whatsapp.com/send?phone="+self.user_id.mobile+"&text=" + message_string,
                'target': 'self',
                'res_id': self.id,
            }
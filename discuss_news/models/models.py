# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import logging
import json

_logger = logging.getLogger(__name__)

class NewsChannel(models.Model):
    _inherit = 'mail.channel'

    is_news_channel = fields.Boolean(default=False, invisible=True)
    language_id = fields.Many2one('res.lang', 'Language')
    url = fields.Char('URL')
    category = fields.Char('Category')
    channel_ref = fields.Char('Channel Reference', invisible=True)
    last_updated = fields.Datetime("Last Updated")

    def update_news_content(self, channel, contents):
        """
            {
            'body': HTML content of the message
            'model': u'res.partner',
            'record_name': u'Agrolait',
            'attachment_ids': [
                {
                    'file_type_icon': u'webimage',
                    'id': 45,
                    'name': u'sample.png',
                    'filename': u'sample.png'
                }
            ],
            'needaction_partner_ids': [], # list of partner ids
            'res_id': 7,
            'tracking_value_ids': [
                {
                    'old_value': "",
                    'changed_field': "Customer",
                    'id': 2965,
                    'new_value': "Axelor"
                }
            ],
            'author_id': (3, u'Administrator'),
            'email_from': 'sacha@pokemon.com' # email address or False
            'subtype_id': (1, u'Discussions'),
            'channel_ids': [], # list of channel ids
            'date': '2015-06-30 08:22:33',
            'partner_ids': [[7, "Sacha Du Bourg-Palette"]], # list of partner name_get
            'message_type': u'comment',
            'id': 59,
            'subject': False
            'is_note': True # only if the subtype is internal
            }
        """
        body = contents.get('articles', False)
        body_contents = ""
        for data in body:
            body_contents += """
                <p> 
                <p style="margin-bottom: 10px;"><img src="%s" width="300px" height="300px"/></p>
                <p style="margin-bottom: 0px;"><b>Title:</b>%s</p>
                <p style="margin-bottom: 0px;"><b>Description:</b>%s</p>
                <p style="margin-bottom: 0px;"><b>Author:</b>%s      <b>publishedAt:</b>%s</p>
                <p style="margin-bottom: 0px;"><b><a href="%s">Read more.. </a></b></p>
                <p style="padding-bottom:10px">
                <hr/>
            """%(data.get('urlToImage', False), data.get('title', False), data.get('description', False),
                 data.get('author', False), data.get('publishedAt', False), data.get('url', False),)

        data = {
                'body': body_contents,
                'model': u'mail.channel',
                'record_name': channel.name,
                'res_id': channel.id,
                'author_id': 3,
                'email_from': u'Administrator <admin@yourcompany.example.com>', # email address or False
                'subtype_id': 1,
                'channel_ids': [channel.id], # list of channel ids
                'message_type': u'notification',
                'subject': False,
                'parent_id': False,
                'reply_to': u'YourCompany <catchall@gmail.com>',
        }

        data.update({'message_id': self.env['mail.message'].sudo()._get_message_id(data)})
        self.env['mail.message'].sudo().create(data)


    @api.model
    def news_sync(self):
        """
        Sync the news according to the each channels, where the news api not providing a single sync for  all channels,
        so we are iterating here on each channels to sync.
        Lets hope for a good Updated api from them in future
        :return:
        """
        default_key = self.env['news.channel.config.settings'].get_default_news_api_key([])
        api_key = default_key.get('news_api_key', False)
        if api_key:
            query = """delete from mail_message m where m.res_id in
             (select distinct id from mail_channel c where c.is_news_channel = True)"""
            self._cr.execute(query)
            channels_pool = self.search([('is_news_channel', '=', True)])
            url = "https://newsapi.org/v1/articles"
            querystring = {
                           "apiKey": api_key,
                           }
            headers = {
                'cache-control': "no-cache",
            }
            for channels in channels_pool:
                querystring.update({"source": channels.channel_ref, })
                response = requests.request("GET", url, headers=headers, params=querystring)
                try:
                    if response.status_code == 200:
                        contents = json.loads(response.text)
                        if contents and contents.get('status') == 'ok':
                            self.update_news_content(channels, contents)
                except Exception as e:
                    _logger.info(e)
                    continue



class NewsChannelConfigSettings(models.Model):
    _name = 'news.channel.config.settings'
    _inherit = 'res.config.settings'

    news_api_key = fields.Char('Api Key')

    @api.model
    def get_default_news_api_key(self, fields):
        ir_values = self.env['ir.values']
        news_api_key = ir_values.get_default('news.channel.config.settings', 'news_api_key')
        return {'news_api_key': news_api_key}

    @api.multi
    def set_default_news_api_key(self):
        ir_values = self.env['ir.values']
        for record in self:
            ir_values.sudo().set_default('news.channel.config.settings', 'news_api_key', record.news_api_key)

    @api.multi
    def execute(self):
        """
        Which invokes when you click on apply button on config page
        Here we update all channels from news api, list under menu 'News'
        Url https://newsapi.org/v1/sources lists the sources
        :return: {'tag': 'reload', 'type': 'ir.actions.client'}
        """
        print self.news_api_key, "self.news_api_keyself.news_api_key"
        if self.news_api_key:
            try:
                url = "https://newsapi.org/v1/sources"
                querystring = {"language": "en"}
                headers = {
                    'cache-control': "no-cache"
                }
                response = requests.request("GET", url, headers=headers, params=querystring)
                data = eval(response.text)
                language_model = self.env['res.lang']
                Channel = self.env['mail.channel']
                channel_data = {}
                if data.get('status') == 'ok':
                    for values in data['sources']:
                        channel_id = Channel.search([('channel_ref', '=', values['id'])])
                        if not len(channel_id):
                            language = language_model.search([('iso_code', '=', values.get('language', False))])
                            channel_data.update({
                                'name': values['name'],
                                'channel_ref': values['id'],
                                'language_id': language and language.id,
                                'category': values['category'],
                                'url': values['url'],
                                'is_news_channel': True,
                                'description': values['description'],
                            })
                            Channel.create(channel_data)
                    return super(NewsChannelConfigSettings, self).execute()
                else:
                    raise Exception
            except Exception as e:
                _logger.info(e)
        else:
            return Warning("Give Proper Api Key")

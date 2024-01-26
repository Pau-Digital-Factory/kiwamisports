# coding: utf-8
"""
@author: Emipro Technologies
@create_date: 22.07.2021
"""
import logging
from odoo import models, fields, api

_logger = logging.getLogger("InAppNotification")


class CustomerAppNotificationSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    app_update_notify_ept = fields.Boolean(string="Enable Emipro's app update notification?",
                                           help="If True, Get the notification of latest app "
                                                "update of Emipro.", default=False,
                                           config_parameter='common_connector_library.app_update_notification')
    last_update_time_by_emipro = fields.Char(string="Last app update time by Emipro",
                                             help="Last app update get by Emipro.",
                                             default=False,
                                             config_parameter='common_connector_library.last_update_time_by_emipro')

    customer_so_number = fields.Char(string="App Order Number",
                                     help="Your App Purchase Registered Numer",
                                     default=False,
                                     config_parameter='common_connector_library.customer_so_number')

    @api.model
    def create(self, vals):
        ipc = self.env['ir.config_parameter'].sudo()
        is_notify = ipc.get_param('common_connector_library.app_update_notification')
        if 'app_update_notify_ept' in list(vals.keys()) and is_notify != vals.get('app_update_notify_ept'):
            self.enable_emipro_notification(vals.get('app_update_notify_ept'))
        return super(CustomerAppNotificationSettings, self).create(vals)

    # def execute(self):
    #     self.enable_emipro_notification(self.app_update_notify_ept)
    #     return super(CustomerAppNotificationSettings, self).execute()

    def update_system_param(self, value, so_number):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('common_connector_library.customer_so_number', so_number)
        return params.set_param('common_connector_library.app_update_notification', value)

    def enable_emipro_notification(self, notify):
        send_cron = self.env['ir.cron']
        try:
            send_cron = self.env.ref("common_connector_library.send_in_app_notification_ept")
        except Exception as error:
            _logger.error(error)
        if send_cron:
            send_cron.write({'active': notify})
            if not notify:
                app = self.env['emipro.app.version.details'].with_context({'is_notify': False})
                app.auto_send_installed_app_details_ept()
        return True

    def get_in_app_system_parameter(self):
        config_parameter_obj = self.env['ir.config_parameter'].sudo()
        is_notify = config_parameter_obj.get_param('common_connector_library.app_update_notification')
        customer_so_number = config_parameter_obj.get_param('common_connector_library.customer_so_number')
        return is_notify, customer_so_number

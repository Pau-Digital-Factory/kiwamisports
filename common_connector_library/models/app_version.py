# coding: utf-8
"""
@author: Emipro Technologies
@create_date: 22.07.2021
"""
import requests
import odoo
import json
import logging
from distutils.version import LooseVersion
from cryptography.fernet import Fernet
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger("InAppNotification")
from datetime import datetime


class EmiproAppVersionDetails(models.Model):
    _name = 'emipro.app.version.details'
    _rec_name = 'module_id'
    _description = 'Emipro App Version Details'

    module_id = fields.Many2one(comodel_name='ir.module.module', string="Module")
    version = fields.Char(string="App Version", help="Emipro's installed app version.")
    update_detail = fields.Html(string="Version Details", help="App version update details.")
    is_latest = fields.Boolean(string="Is Latest Version?",
                               help="True, if the installed app version is latest.")
    upgrade_require = fields.Boolean(string="Is Update Required?",
                                     help="True, if required to update app to latest version.")
    is_notify = fields.Boolean(string="Is Notify?",
                               help="False, It will not notify any updates related to this app.\n"
                                    "If customer click on the close button it will mark that \n"
                                    "update as True and never show the update again.",
                               default=True)
    update_url = fields.Char(string="Odoo Store URL")
    module_name = fields.Char(string="Module Name", related="module_id.name")

    def auto_send_installed_app_details_ept(self):
        """
        This method are used in cronjob.
        :created_by: Meera Sidapara
        :create_date: 16.11.2022
        -----------------
        :return: True
        """
        details = self._prepare_odoo_details()
        request_data = self._get_installed_modules(details)
        request_data = self._encrypt_details(request_data)
        if request_data:
            url = 'https://internalerp.emiprotechnologies.com/app_notification/send'
            headers = {
                'Accept': '*/*',
                'Content-Type': 'text/plain',
            }
            try:
                response = requests.post(url, headers=headers, data=request_data, verify=False, timeout=10)
                _logger.info("Request send with installed app information...")
            except requests.exceptions.Timeout:
                _logger.info("Server is Busy, Request Timeout...")
                raise UserError('Server is not available, Please check after sometime.')
            except Exception as error:
                _logger.error('Server is not available, Please check after sometime. %s' % error)
                raise UserError('Server is not available, Please check after sometime.')
            if response.status_code in [200, 201] and isinstance(response.content, bytes):
                response = json.loads(response.content)
                status = response.get('status', [])
                if status == 'success':
                    self.receive_app_updates(request_data)
                    ipc = self.env['ir.config_parameter'].sudo()
                    ipc.set_param('common_connector_library.last_update_time_by_emipro', str(datetime.now()))
                elif status == 'failed':
                    pass
                else:
                    raise UserError('Request limit reached for today.')
        return True

    def receive_app_updates(self, details):
        # details = self._encrypt_details(details)
        url = 'https://internalerp.emiprotechnologies.com/app_notification/receive'
        headers = {
            'Accept': '*/*',
            'Content-Type': 'text/plain',
        }
        try:
            response = requests.post(url, headers=headers, data=details, verify=False, timeout=10)
            _logger.info("Request send to get app updates...")
        except requests.exceptions.Timeout:
            _logger.info("Server is Busy, Request Timeout...")
            raise UserError('Server is not available, Please check after sometime.')
        except Exception as error:
            _logger.error(error)
            raise UserError('Server is not available, Please check after sometime.')
        if isinstance(response.content, bytes):
            response = json.loads(response.content)
            if isinstance(response, dict):
                self.create_update_details(response)
        return True

    def _prepare_odoo_details(self):
        """
        This method are used to prepare dictionary for odoo basic details like
        version, platform, odoo_url, email, user etc..
        :created_by: Meera Sidapara
        :create_date: 16.11.2022
        -----------------
        :return: dict()
        """
        info = self._get_version_info()
        details = self._get_company_info()
        details.update({
            'odoo_version': info.get('server_version'),
            'platform': info.get('platform'),
            'send_notification': self.env.context.get('is_notify', True)
        })
        return details

    @staticmethod
    def _encrypt_details(details):
        key = '9_Y1xoxbj0E9pRcyqy6BLvg9_uf1Kua1F7T5trFo7yU='
        fernet = Fernet(key)
        try:
            _logger.info("Encoding application details...")
            j_dump = json.dumps(details).encode()
            _logger.info("Details encoded successfully...")
            _logger.info("Encrypting details...")
            encrypt = fernet.encrypt(j_dump)
            _logger.info("Encryption successful...")
            return encrypt
        except Exception as error:
            _logger.info("Error !!! While encoding & encrypting application details...")
            _logger.error(error)
        return details

    def _get_installed_modules(self, info):
        """
        This method are used to gather the information of installed/uninstalled modules
        in the customer's database and updated it into the param: info.
        :created_by: Meera Sidapara
        :create_date: 16.11.2022
        -----------------
        :param info: dict()
        :return: info
        """
        module = self.env['ir.module.module'].sudo()
        module_list = dict()
        icp = self.env['ir.config_parameter'].sudo()
        last_update = icp.get_param('common_connector_library.last_update_time_by_emipro', False)
        for state in ['installed', 'uninstalled']:
            if last_update:
                modules = module.search_read([('author', 'in', self.get_author()),
                                              ('state', '=', state), ('write_date', '>', last_update)],
                                             fields=['name', 'latest_version', 'author'])
            else:
                modules = module.search_read([('author', 'in', self.get_author()), ('state', '=', state)],
                                             fields=['name', 'latest_version', 'author'])

            if state == 'uninstalled':
                for module in modules:
                    manifest = odoo.modules.load_information_from_description_file(module.get('name'))
                    module.update({'latest_version': manifest.get('version')})
            module_list.update({state: modules})
        if module_list:
            info.update({
                'app_details': module_list
            })
        return info

    @staticmethod
    def get_author():
        return [
            'Emipro Technologies Pvt. Ltd.',
            'Emipro',
            'Emipro Technologies',
            'Emipro Technologies (P) Ltd.'
        ]

    @staticmethod
    def _get_version_info():
        """
        This method are used to get the odoo version information, If we get the "e" param in
        the list then the version is "enterprise" otherwise it will "community".
        :created_by: Meera Sidapara
        :create_date: 16.11.2022
        -----------------
        :return: dict()
        """
        info = odoo.service.common.exp_version()
        platform = 'community'
        info.update({'platform': 'community'})
        if '+e' in info.get('server_version'):
            platform = 'enterprise'
        info.update({
            'platform': platform
        })
        return info

    def _get_company_info(self):
        """
        This method are used to get the basic company information like name, email, odoo_url,
        db_uuid.
        :created_by: Meera Sidapara
        :create_date: 16.11.2022
        -----------------
        :return: dict()
        """
        params = self._get_ipc_param_info()
        return {
            'company_name': self.env.company.name,
            'company_email': self.env.company.email or self.env.user.email,
            'odoo_url': params.get('url'),
            'send_notification': params.get('is_notify'),
            'db_uuid': params.get('db_uuid'),
            'customer_so_numer': params.get('customer_so_numer'),
        }

    def _get_ipc_param_info(self):
        """
        This method are used to get the required system parameter information.
        :created_by: Meera Sidapara
        :create_date: 16.11.2022
        -----------------
        :return: dict()
        """
        ipc = self.env['ir.config_parameter'].sudo()
        params = {
            'url': 'web.base.url',
            'is_notify': 'common_connector_library.app_update_notification',
            'db_uuid': 'database.uuid',
            'customer_so_numer': 'common_connector_library.customer_so_number',
        }
        for param in params:
            params.update({
                param: ipc.get_param(params.get(param))
            })
        return params

    def create_update_details(self, data):
        """
        This method are used to create app update details in the system. It search the update
        based on the module_id and module version, If the app update is available then
        default system will update that update details record otherwise its create new one.
        :created_by: Meera Sidapara
        :create_date: 16.11.2022
        -----------------
        :param data: dict()
        :return: True
        """
        module = self.env['ir.module.module'].sudo()
        app_details = data.get('app_details', [])
        for app in app_details:
            app_keys = list(app.keys())
            for key in app_keys:
                app_data = app.get(key)
                module = module.search([('name', '=', key)], limit=1)
                if module:
                    for data in app_data:
                        emipro_app = self.search([('module_id', '=', module.id),
                                                  ('version', '=', data.get('version'))], limit=1)
                        self.sudo().search([('module_id', '=', module.id)]).write({'is_latest': False})
                        if emipro_app:
                            emipro_app.sudo().write(data)
                        else:
                            data.update({'module_id': module.id})
                            self.sudo().create(data)
            self._cr.commit()
        return True

    def find_update_details(self, module):
        """
        This method are used to find an update details based on the module_id from
        customer's database and return it.
        :created_by: Meera Sidapara
        :create_date: 16.11.2022
        -----------------
        :param module: ir.module.module object
        :return: list(update details)
        """
        details = list()
        updates = self.search([('module_id', '=', module.id), ('is_notify', '=', True)])
        if updates:
            details = self._prepare_update_details(updates, details)
        module_obj = self.env['ir.module.module'].sudo()
        common_connector = module_obj.search([('name', '=', 'common_connector_library')], limit=1)
        if common_connector:
            common_updates = self.search([('module_id', '=', common_connector.id),
                                          ('is_notify', '=', True)])
            if common_updates:
                details = self._prepare_update_details(common_updates, details)
        return details

    @staticmethod
    def _prepare_update_details(updates, details):
        counter = 1
        versions = updates.mapped('version')
        versions = sorted(versions, key=LooseVersion, reverse=True)
        for version in versions:
            if counter == 6:
                break
            update = updates.filtered(lambda u: u.version == version)
            if update.module_id.installed_version == update.version:
                return details
            else:
                details.append({
                    'version': update.version,
                    'module_name': update.module_id.shortdesc,
                    'detail': update.update_detail,
                    'is_latest': update.is_latest,
                    'update_required': update.upgrade_require,
                    'update_url': update.update_url
                })
            counter += 1
        return details

    def disable_notification(self, module_name):
        """
        This method are used to find the update details of specific module, and disable the
        notification for that specific module for the customer.
        :created_by: Meera Sidapara
        :create_date: 16.11.2022
        -----------------
        :param module_name: string
        :return: True
        """
        module = self.env['ir.module.module'].sudo()
        module = module.search([('name', '=', module_name)], limit=1)
        if module:
            details = self.search([('module_id', '=', module.id)])
            if details:
                details.write({'is_notify': False})
        return True

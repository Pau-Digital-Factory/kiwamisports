# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import json
import base64
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ImageUrl(http.Controller):

    @http.route('/lf/i/<string:encodedimage>', type='http', auth='public')
    def create_image_url(self, encodedimage=''):
        """This method is used to get images based on URL which URL set common product images.URL will be generated
            automatically in ERP.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 18 September 2021 .
            Task_id: 178058
        """
        if encodedimage:
            try:
                decode_data = base64.urlsafe_b64decode(encodedimage)
                res_id = str(decode_data, "utf-8")
                status, headers, content = request.env['ir.http'].sudo().binary_content(
                    model='common.product.image.ept', id=res_id,
                    field='image')
                content_base64 = base64.b64decode(content) if content else ''
                _logger.info("Image found with status %s", str(status))
                headers.append(('Content-Length', len(content_base64)))
                return request.make_response(content_base64, headers)
            except Exception:
                return request.not_found()
        return request.not_found()

    @http.route('/app_notification/get_module', type='json', methods=['POST'], auth='public')
    def receive_in_app_update_notification(self, **kwargs):
        """
        This controller are used to send the installed/uninstalled module information
        to webserver.
        :created_by: Meera Sidapara
        :create_date: 16.11.2022
        -----------------
        :return: dict()
        """
        details, data = dict(), dict()
        try:
            data = json.loads(request.httprequest.data.decode('UTF-8'))
        except Exception as error:
            _logger.error("Error In Decode the data using (UTF-8) format!!")
            _logger.error(error)
        ipc = request.env['ir.config_parameter'].sudo()
        is_notify = ipc.get_param('common_connector_library.app_update_notification', False)
        if is_notify:
            params = data.get('params')
            if params:
                if params.get('menu_id'):
                    module_name = self._get_module_name(params.get('menu_id'))
                else:
                    module_name = params.get('module_name')
                module = request.env['ir.module.module'].sudo()
                app_version = request.env['emipro.app.version.details'].sudo()
                author = app_version.get_author()
                module = module.search([('name', '=', module_name), ('author', 'in', author)],
                                       limit=1)
                if module:
                    updates = app_version.find_update_details(module)
                    update_url = [update.get('update_url') for update in updates if
                                  update.get('update_url')]
                    details.update({
                        'updates': updates,
                        'module_name': module.shortdesc,
                        'module_id': module.id,
                        'update_url': update_url and update_url[0] or '',
                        'technical_name': module.name
                    })
        return details

    @staticmethod
    def _get_module_name(menu_id):
        """
        This method are use to find the module name from menu id.
        :created_by: Meera Sidapara
        :create_date: 16.11.2022
        -----------------
        :param menu_id: menu_id
        :return: module_name
        """
        menu = request.env['ir.ui.menu'].sudo().browse(menu_id).get_xml_id()
        menu_id = menu.get(list(menu.keys())[0])
        module_name = menu_id.split('.')[0]
        return module_name

    @http.route('/app_notification/deny_update', type='json', methods=['POST'], auth='public')
    def deny_update(self):
        """
        This controller are used to disable the app update when user close the popup.
        Its only disable those notifications which was disabled in the popup.
        :task_id : 176082
        :created_by: Meera Sidapara
        :create_date: 16.11.2022
        -----------------
        :params: list
        :return: dict()
        """
        data = dict()
        try:
            data = json.loads(request.httprequest.data.decode('UTF-8'))
        except Exception as error:
            _logger.error("Error In Decode the data using (UTF-8) format!!")
            _logger.error(error)
        params = data.get('params')
        if params:
            if params.get('menu_id'):
                module_name = self._get_module_name(params.get('menu_id'))
            else:
                module_name = params.get('module_name')
            app_version = request.env['emipro.app.version.details'].sudo()
            module_obj = request.env['ir.module.module'].sudo()
            module = module_obj.search(['|', ('shortdesc', '=ilike', module_name), ('name', '=ilike', module_name)],
                                       limit=1)
            app_version_details = app_version.search([('module_id.shortdesc', '=', 'Common Connector Library')])
            if request.env.user.sudo().has_group('base.group_system') and app_version_details:
                app_version_details.write({'is_notify': False})
            method_name = "disable_notification_{}".format(module.name)
            if hasattr(app_version, method_name):
                getattr(app_version, method_name)(module_name)
        return True

import logging
from odoo import models, fields, api

_logger = logging.getLogger("InAppNotification")


class EmiproAppVersionDetails(models.Model):
    _inherit = 'emipro.app.version.details'

    def disable_notification_shopify_ept(self, module_name):
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
        modules = module.search([('shortdesc', 'in', [module_name, 'Common Connector Library'])])
        if modules:
            details = self.sudo().search([('module_id', 'in', modules.ids)])
            if self.sudo().user_has_groups('shopify_ept.group_shopify_manager_ept') and details:
                details.write({'is_notify': False})
        return True

# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class OnbordingStep(models.Model):
    """
    This model is inherited for adding onboarding process.
    @author: Dhaval Bhut on Date 01-Nov-2023
    """
    _inherit = 'onboarding.onboarding.step'

    def shopify_res_config_view_action(self, view_id):
        """ Usage: return the action for open the configurations wizard """
        action = self.env["ir.actions.actions"]._for_xml_id(
            "shopify_ept.action_shopify_instance_config")
        action_data = {'view_id': view_id.id, 'views': [(view_id.id, 'form')], 'target': 'new',
                       'name': 'Configurations'}
        instance = self.env['shopify.instance.ept'].search_shopify_instance()
        if instance:
            action['context'] = {'default_shopify_instance_id': instance.id}
        else:
            action['context'] = {}
        action.update(action_data)
        return action

    @api.model
    def action_shopify_open_shopify_instance_wizard(self):
        """ Called by onboarding panel above the Instance."""
        action = self.env["ir.actions.actions"]._for_xml_id(
            "shopify_ept.shopify_on_board_instance_configuration_action")
        action['context'] = {'is_calling_from_onboarding_panel': True}
        instance = self.env['shopify.instance.ept'].search_shopify_instance()
        if instance:
            action.get('context').update({
                'default_name': instance.name,
                'default_shopify_host': instance.shopify_host,
                'default_shopify_api_key': instance.shopify_api_key,
                'default_shopify_password': instance.shopify_password,
                'default_shopify_shared_secret': instance.shopify_shared_secret,
                'default_shopify_company_id': instance.shopify_company_id.id,
                'is_already_instance_created': True,
            })
        return action

    @api.model
    def action_shopify_open_basic_configuration_wizard(self):
        """ Usage: return the action for open the basic configurations wizard for shopify """
        try:
            view_id = self.env.ref('shopify_ept.shopify_basic_configurations_onboarding_wizard_view')
        except:
            return True
        return self.shopify_res_config_view_action(view_id)

    @api.model
    def action_shopify_open_financial_status_configuration_wizard(self):
        """ Usage: return the action for open the basic configurations wizard for financial status"""
        try:
            view_id = self.env.ref('shopify_ept.shopify_financial_status_onboarding_wizard_view')
        except:
            return True
        return self.shopify_res_config_view_action(view_id)

    @api.model
    def action_shopify_open_cron_configuration_wizard(self):
        """ Usage: Return the action for open the cron configuration wizard """
        action = self.env["ir.actions.actions"]._for_xml_id("shopify_ept.action_wizard_shopify_cron_configuration_ept")
        instance = self.env['shopify.instance.ept'].search_shopify_instance()
        action['context'] = {'is_calling_from_onboarding_panel': True}
        if instance:
            action.get('context').update({'default_shopify_instance_id': instance.id,
                                          'is_instance_exists': True})
        return action

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class Onboarding(models.Model):
    _inherit = 'onboarding.onboarding'

    # Shopify Dashboard Onboarding
    @api.model
    def action_close_panel_shopify_dashboard(self):
        self.action_close_panel('shopify_ept.onboarding_onboarding_shopify_dashboard')

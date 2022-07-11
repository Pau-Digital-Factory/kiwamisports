from dataclasses import field
from odoo import models, fields

class account_move(models.Model):
    _inherit = 'account.move'

    # The country_name is stored to allow it as a filter in the 'group by' section
    partner_country_name = fields.Char(compute='_compute_partner_country_name', store=True)
    partner_country_code = fields.Char(compute='_compute_partner_country_code')

    # Get the full name of the country (ex: France) for each invoice
    def _compute_partner_country_name(self):
        for record in self:
            record.partner_country_name = record.partner_id.country_id.name

    # Get the country code (ex: FR) for each invoice
    def _compute_partner_country_code(self):
        for record in self:
            record.partner_country_code = record.partner_id.country_id.code
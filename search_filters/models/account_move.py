from dataclasses import field
from odoo import models, fields

class account_move(models.Model):
    _inherit = 'account.move'

    partner_country_name = fields.Char(compute='_compute_partner_country_name')
    partner_country_code = fields.Char(compute='_compute_partner_country_code')

    def _compute_partner_country_code(self):
        for record in self:
            record.partner_country_code = record.partner_id.country_id.code

    def _compute_partner_country_name(self):
        for record in self:
            record.partner_country_name = record.partner_id.country_id.name
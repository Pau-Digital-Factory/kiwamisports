from dataclasses import field
from odoo import models, fields

class account_move(models.Model):
    _inherit = 'account.move'

    
    def _default_category(self):
        return self.env['res.partner.category'].browse(self._context.get('category_id'))

    # The country_name is stored to allow it as a filter in the 'group by' section
    partner_country_name = fields.Char(compute='_compute_partner_country_name', store=True)
    partner_country_code = fields.Char(compute='_compute_partner_country_code', store=False)
    #partner_tags = fields.Many2many(compute='_compute_partner_tags', store=False)
    category_id = fields.Many2many('res.partner.category', string='Tags', compute='_compute_category_id')

    # Get the full name of the country (ex: France) for each invoice
    def _compute_partner_country_name(self):
        for record in self:
            record.partner_country_name = record.partner_id.country_id.name

    # Get the country code (ex: FR) for each invoice
    def _compute_partner_country_code(self):
        for record in self:
            record.partner_country_code = record.partner_id.country_id.code

    
    def _compute_category_id(self):
        for record in self:
            record.category_id = record.partner_id.category_id



#     def _compute_partner_tags(self):
#         for record in self:
#             partner_tags = context['partner_categories'].ids



# from contextlib import contextmanager
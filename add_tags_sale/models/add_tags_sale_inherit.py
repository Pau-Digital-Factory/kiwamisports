from odoo import tools
from odoo import api, fields, models


class Saleorder(models.Model):
    _inherit = "sale.order"
    tagg = fields.Char('champ', compute='_compute_tagg', store=True)
    category_id = fields.Many2many('res.partner.category', string='Etiquette', compute='_compute_category_id')
    
    def _compute_category_id(self):
        for record in self:
            record.category_id = record.partner_id.category_id
    
    @api.depends('partner_id.category_id')
    def _compute_tagg(self):
        for record in self:
            if record.partner_id.category_id:
                record.tagg = record.partner_id.category_id[0].name
            else:
                record.tagg = False
    
class SaleReportv(models.Model):
    _inherit = "sale.report"
    tagg = fields.Char('Etiquette', readonly=True)
    

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
              fields['tagg'] = ", s.tagg as tagg" 
              groupby += ', s.tagg '
              return super(SaleReportv, self)._query(with_clause, fields, groupby, from_clause)


class AccountMove(models.Model):
    _inherit = "account.move"
    tagg = fields.Char('champ', compute='_compute_tagg', store=True)
    
    @api.depends('partner_id.category_id')
    def _compute_tagg(self):
        for record in self:
            if record.partner_id.category_id:
                record.tagg = record.partner_id.category_id[0].name
            else:
                record.tagg = False
    

class AccountInvoiceReportv(models.Model):
    _inherit = "account.invoice.report"
    tagg = fields.Char('Etiquette', readonly=True)
    

    def _select(self):
        return super(AccountInvoiceReportv, self)._select() + ", move.tagg as tagg"


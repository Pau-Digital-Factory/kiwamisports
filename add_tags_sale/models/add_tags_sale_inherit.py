from odoo import tools
from odoo import api, fields, models


class Saleorder(models.Model):
    _name = "sale.order"
    tagg = fields.Char('Tags', compute='_compute_tagg')
    
    @api.depends('partner_id')
    def _compute_tagg(self):
        for record in self:
            if reocrd.partner_id.category_id[0]:
                record.tagg = reocrd.partner_id.category_id[0].name
            else:
                record.tagg = False
    
class SaleReport(models.Model):
    _name = "sale.report"
    tagg = fields.Char('Tags', readonly=True)
    

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
              fields['tagg'] = ", s.tagg as tagg" 
              groupby += ', s.tagg '
              return super(ClassName, self)._query(with_clause, fields, groupby, from_clause)



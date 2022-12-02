from odoo import tools
from odoo import api, fields, models


class SaleReport(models.Model):
    _name = "sale.report"

    category_id = fields.Many2many('res.partner.category', column1='partner_id',
                                    column2='category_id', string='Tags', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
              fields['category_id'] = ", s.category_id as category_id" 
              groupby += ', s.category_id '
              return super(ClassName, self)._query(with_clause, fields, groupby, from_clause)



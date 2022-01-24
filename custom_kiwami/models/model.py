from odoo import api, fields, models, tools, _
from odoo.osv import expression
from odoo.exceptions import AccessError
from odoo.addons.shopify_ept import shopify



class Shopifysale_order_line(models.Model):
     _inherit = "sale.order.line"
     def get_sale_order_line_multiline_description_sale(self, product):
        """ Compute a default multiline description for this sales order line.

        In most cases the product description is enough but sometimes we need to append information that only
        exists on the sale order line itself.
        e.g:
        - custom attributes and attributes that don't create variants, both introduced by the "product configurator"
        - in event_sale we need to know specifically the sales order line as well as the product to generate the name:
          the product is not sufficient because we also need to know the event_id and the event_ticket_id (both which belong to the sale order line).
        """
        
        
        if not self.product_id:
            return ''

        color = ""
        taille = ""
        if self.product_id.product_template_variant_value_ids:
          for m in self.product_id.product_template_variant_value_ids:
            phrase = m.attribute_id.name
            if m.attribute_id.id in [2,3,4]:
                color = ", Color: "+ m.name
            else:
                taille = m.name

        values = []
        if self.product_id.type_product:
            type_perso = str(self.product_id.type_product)
        else:
            type_perso = " "
        if self.product_id.product_template_variant_value_ids:
           lieu = self.product_id.name +" \n \n Taille :"+taille+" QTY: "+str(self.product_uom_qty)+" \n \n"+type_perso +", Type : "+self.product_id.name + color +", made in France by Kiwami 9 rue ampere 64121 Montardon"
        else: 
          lieu = " "
          if product.partner_ref:
             values.append(product.partner_ref)
        values.append(lieu)    
        if product.description_sale: 
                values.append(product.description_sale)
        return '\n'.join(values)

#      @api.onchange('product_uom_qty')
#      def _onchange_quantity_desc(self):
#         if not self.product_id:
#             return ''
#         product = self.product_id
#         color = ""
#         taille = ""
#         if self.product_id.product_template_variant_value_ids:
#           for m in self.product_id.product_template_variant_value_ids:
#             phrase = m.attribute_id.name
#             if m.attribute_id.id in [2,3,4]:
#                 color = "Color: "+ m.name
#             else:
#                 taille = m.name

#         values = []
#         if self.product_id.type_product:
#             type_perso = str(self.product_id.type_product)
#         else:
#             type_perso = " "
#         if self.product_id.product_template_variant_value_ids:
#            lieu = self.product_id.name +" \n \n Taille :"+taille+" QTY: "+str(self.product_uom_qty)+" \n \n"+type_perso +", Type : "+self.product_id.name + color +", made in France by Kiwami 9 rue ampere 64121 Montardon"
#         else: 
#           lieu = " "
#           if self.product_id.partner_ref:
#              values.append(self.product_id.partner_ref)
#         values.append(lieu)    
#         if self.product_id.description_sale: 
#                 values.append(self.product_id.description_sale)
#         return '\n'.join(values)


class ShopifyProductProducttemplate(models.Model):
     _inherit = "product.template"
     type_product = fields.Char()
# class ShopifyProductProductliee(models.Model):
#      _inherit = "product.product"
     
#      hs_code = fields.Char("Nomenclature douanière",help="Code normalisé pour l'expédition internationale et la déclaration de marchandises. Pour le moment, utilisé uniquement pour le fournisseur d’expédition FedEx.",compute="_get_code_sh")
#      type_product = fields.Char()
#      def _get_code_sh(self):
#         for r in self: 
#           r.hs_code= False
#           code = self.env["shopify.product.product.ept"].search([("default_code","=", r.default_code)]) 
#           if code :
#                r.hs_code= code.hs_code
               

class Shopifysaleorderline(models.Model):
     _inherit = "account.move.line"               
     
     
     
     
     def _get_computed_name(self):
        self.ensure_one()

        if not self.product_id:
            return ''

        if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
        else:
            product = self.product_id
        color = ""
        taille = ""
        if self.product_id.product_template_variant_value_ids:
          for m in self.product_id.product_template_variant_value_ids:
            phrase = m.attribute_id.name
            if m.attribute_id.id in [2,3,4]:
                color = ", Color: "+ m.name
            else:
                taille = m.name

        values = []
        if self.product_id.type_product:
            type_perso = str(self.product_id.type_product)
        else:
            type_perso = " "
        if self.product_id.product_template_variant_value_ids:
           lieu = self.product_id.name +" \n \n Taille :"+taille+" QTY: "+str(self.quantity)+" \n \n"+type_perso +", Type : "+self.product_id.name + color +", made in France by Kiwami 9 rue ampere 64121 Montardon"
        else: 
          lieu = " "
          if product.partner_ref:
             values.append(product.partner_ref)
        values.append(lieu)    
        if self.journal_id.type == 'sale':
            if product.description_sale:
                
                values.append(product.description_sale)
                
        elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values.append(product.description_purchase)
        return '\n'.join(values)


     @api.onchange('quantity')
     def _onchange_quantity_desc(self):
        self.ensure_one()

        if not self.product_id:
            return ''

        if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
        else:
            product = self.product_id
        color = ""
        taille = ""
        if self.product_id.product_template_variant_value_ids:
         for m in self.product_id.product_template_variant_value_ids:
            phrase = m.attribute_id.name
            if m.attribute_id.id in [2,3,4]:
                color = m.name
            else:
                taille = m.name

        values = []
        if self.product_id.product_template_variant_value_ids:
           lieu = self.product_id.name +" \n \n Taille :"+taille+" QTY: "+str(self.quantity)+" \n \n"+str(self.product_id.type_product) +", Type : "+self.product_id.name+", Color : "+ color +", made in France by Kiwami 9 rue ampere 64121 Montardon"
        else: 
          lieu = " "
          if product.partner_ref:
             values.append(product.partner_ref)
        values.append(lieu)    
        if self.journal_id.type == 'sale':
            if product.description_sale:
                
                values.append(product.description_sale)
                
        elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values.append(product.description_purchase)
        self.name =  '\n'.join(values)
               
               
               
               
               

class ShopifyProductProductEptt(models.Model):
     _inherit = "shopify.product.product.ept"
    
     hs_code = fields.Char()
     type_product = fields.Char()

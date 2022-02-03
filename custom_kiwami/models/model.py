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
        if self.order_id.partner_id.country_id.code == "FR":
               return product.get_product_multiline_description_sale() + self._get_sale_order_line_multiline_description_variants()

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
           lieu = self.product_id.name +" \n \n Taille :"+taille+" QTY: "+str(self.product_uom_qty)+" \n \n Type : "+type_perso + color +", made in France by Kiwami 9 rue ampere 64121 Montardon"
        else: 
          lieu = " "
          if product.partner_ref:
             values.append(product.partner_ref)
        values.append(lieu)    
        if product.description_sale: 
                values.append(product.description_sale)
        return '\n'.join(values)

     @api.onchange('product_uom_qty')
     def _onchange_quantity_desc_for_export(self):
       if not self.product_id:
             self.name = ''
       if self.order_id.partner_id.country_id.code == "FR":
               self.name =  str(self.product_id.get_product_multiline_description_sale()) + str(self._get_sale_order_line_multiline_description_variants())
       else:

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
           lieu = self.product_id.name +" \n \n Taille :"+taille+" QTY: "+str(self.product_uom_qty)+" \n \n Type : "+type_perso + color +", made in France by Kiwami 9 rue ampere 64121 Montardon"
        else: 
          lieu = " "
          if self.product_id.partner_ref:
             values.append(self.product_id.partner_ref)
        values.append(lieu)    
        if self.product_id.description_sale: 
                values.append(self.product_id.description_sale)
        self.name =  '\n'.join(values)



class ShopifyProductProducttemplate(models.Model):
     _inherit = "product.template"
     type_product = fields.Char()

class salelineremovereference2(models.Model):
    _inherit = "product.product"
    @api.depends_context('partner_id')
    def _compute_partner_ref(self):
        for product in self:
            for supplier_info in product.seller_ids:
                if supplier_info.name.id == product._context.get('partner_id'):
                    product_name = supplier_info.product_name or product.name
                    product.partner_ref = '%s%s' % (product.code and '[%s] ' % product.code or '', product_name)
                    break
            else:
                product.partner_ref = product.display_name
    def get_product_multiline_description_sale(self):
        """ Compute a multiline description of this product, in the context of sales
                (do not use for purchases or other display reasons that don't intend to use "description_sale").
            It will often be used as the default description of a sale order line referencing this product.
        """
        name = ""
        if self.description_sale:
            name += self.description_sale
        if not self.description_sale:
            name += self.name

        return name
               

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
               
        
     
     
        if self.partner_id.country_id.code == "FR":
          
          values2 = []
          if product.name:
            values2.append(product.name)
          if self.journal_id.type == 'sale':
            if product.description_sale:
                values2.append(product.description_sale)
          elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values2.append(product.description_purchase)
          return '\n'.join(values2)
          
          
          
          
          
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
           lieu = self.product_id.name +" \n \n Taille :"+taille+" QTY: "+str(self.quantity)+" \n \n Type : "+type_perso + color +", made in France by Kiwami 9 rue ampere 64121 Montardon"
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

     @api.onchange('partner_id')
     def _onchange_partner_fr(self):
        self.ensure_one()

        if not self.product_id:
            return ''

        if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
        else:
            product = self.product_id
               
        if self.partner_id.country_id.code == "FR":
          
          values2 = []
          if product.partner_ref:
            values2.append(product.partner_ref)
          if self.journal_id.type == 'sale':
            if product.description_sale:
                values2.append(product.description_sale)
          elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values2.append(product.description_purchase)
          return '\n'.join(values2)
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
           lieu = self.product_id.name +" \n \n Taille :"+taille+" QTY: "+str(self.quantity)+" \n \n  Type : "+str(self.product_id.type_product)+", Color : "+ color +", made in France by Kiwami 9 rue ampere 64121 Montardon"
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
     @api.onchange('quantity')
     def _onchange_quantity_desc(self):
        self.ensure_one()

        if not self.product_id:
            return ''

        if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
        else:
            product = self.product_id
               
        if self.partner_id.country_id.code == "FR":
          
          values2 = []
          if product.partner_ref:
            values2.append(product.partner_ref)
          if self.journal_id.type == 'sale':
            if product.description_sale:
                values2.append(product.description_sale)
          elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values2.append(product.description_purchase)
          return '\n'.join(values2)
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
           lieu = self.product_id.name +" \n \n Taille :"+taille+" QTY: "+str(self.quantity)+" \n \n Type : "+str(self.product_id.type_product)+", Color : "+ color +", made in France by Kiwami 9 rue ampere 64121 Montardon"
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

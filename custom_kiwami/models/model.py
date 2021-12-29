from odoo import api, fields, models, tools, _
from odoo.osv import expression
from odoo.exceptions import AccessError
from odoo.addons.shopify_ept import shopify






class ShopifyProductProductEptt(models.Model):
     _inherit = "shopify.product.product.ept"
    
     hs_code = fields.Char()
     def search_odoo_product_and_set_sku_barcode(self, template_attribute_value_ids, variation, product_template):
        """ This method is used to search odoo product base on a prepared domain and set SKU and barcode on that
            product.
            :param template_attribute_value_ids: Record of product template attribute value ids.
            :param variation: Response of product variant which received from shopify store.
            :param product_template: Record of Odoo product template.
            @return: odoo_product
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 21 October 2020 .
            Task_id: 167537
        """
        odoo_product_obj = self.env["product.product"]
        sku = variation.get("sku")
        sh_code = variation.get("harmonizedSystemCode")
        barcode = variation.get("barcode") or False
        if barcode and barcode.__eq__("false"):
            barcode = False
        odoo_product = False

        domain = []
        for template_attribute_value in template_attribute_value_ids:
            tpl = ("product_template_attribute_value_ids", "=", template_attribute_value)
            domain.append(tpl)

        domain and domain.append(("product_tmpl_id", "=", product_template.id))
        if domain:
            odoo_product = odoo_product_obj.search(domain)
        if odoo_product and sku:
            odoo_product.write({"default_code": sku})
        if odoo_product and sh_code:
            odoo_product.write({"hs_code": "hghghg"})
        if barcode and odoo_product:
            odoo_product.write({"barcode": barcode})

        return odoo_product

class ShopifyProductTemplateEptt(models.Model):
    _inherit = "shopify.product.template.ept"
    
    def prepare_variant_vals(self, instance, variant_data):
        """
        This method used to prepare a shopify variant dictionary.
        @param instance:
        @param variant_data: Data of Shopify variant.
        @author: Maulik Barad on Date 01-Sep-2020.
        """
        instance.connect_in_shopify()
        result = shopify.InventoryItem().find(int(variant_data.get("inventory_item_id"))) 
#         mm = result.get("inventory_item_id")
        test = result.get("harmonized_system_code")
        variant_vals = {"shopify_instance_id": instance.id,
                        "variant_id": variant_data.get("id"),
                        "sequence": variant_data.get("position"),
                        "default_code": variant_data.get("sku", ""),
                        "hs_code": test,
                        "inventory_item_id": variant_data.get("inventory_item_id"),
                        "inventory_management": "shopify" if variant_data.get(
                            "inventory_management") == "shopify" else "Dont track Inventory",
                        "check_product_stock": variant_data.get("inventory_policy"),
                        "taxable": variant_data.get("taxable"),
                        "created_at": self.convert_shopify_date_into_odoo_format(variant_data.get("created_at")),
                        "updated_at": self.convert_shopify_date_into_odoo_format(variant_data.get("updated_at")),
                        "exported_in_shopify": True,
                        "active": True}

        return variant_vals

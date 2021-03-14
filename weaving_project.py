#!/usr/bin/env python
import yaml
import json
import re
from copy import deepcopy
from collections import defaultdict, abc
from util.conversions import cm_to_m, kg_to_g, g_to_kg
from forex_python.converter import CurrencyRates



RATES = {
    "SEK": 1.,
}


DEFAULT_WARP = {
    "shrinkage": {
        "width": 15., # percentage
        "length": 10., # percentage
    },
    "extra_ends": 0, # Adds to total number of ends, but not to the width
    "sampling": 0.,
    "evening_weaving": 20.,
    "tying": 15.,
    "efsingar": 50.,
    "density": 10., # Number of threads per cm in one direction
    "name": "",
    "warp_length": 0.,
    "width": 0.,
    "pattern_ends": 0, # Number of ends in one pattern repeat
    "yarn": {},
    "products": {},
    "n_ends": 0,
    "n_pattern_repeats": 0,
    "adjusted_weaving_width": 0.,
    "adjusted_final_width": 0.,
    "weight": 0.,
    "price": {
        "setup": 2000.,
        "base_per_wrap": 1000.,
        "additional_per_meter": 500., # All "per meter" are per finished meter of cloth
        "dyeing_warp_per_meter": 500.,
        "dyeing_weft_per_meter": 500.,
        "warp_cost_per_wrap_meter": 0.,
    }
}


DEFAULT_YARN = {
    "material": "unknown",
    "thickness": "unknown",
    "colour": "unknown",
    "m_per_kg": 0.,
    "m_per_kg_error": 5., # percentage
    "price_per_kg": 0.,
    "currency": "SEK",
    "currency_conversion": 1.,
    "url": "",
    "fraction": 1.,
    "length": 0.,
    "weight": 0.,
    "n_ends": 0,
    "finished_cloth_length": 0.,
    "cost": 0.,
    "this_for_extra_ends": False,
}


DEFAULT_PRODUCT = {
    "ordinal": 0,
    "name": "Unnamed",
    "length": 0.,
    "hems": 0.,
    "fringes": 0.,
    "density": 10.,
    "yarn": {},
    "fringe_shortening": 20., # percentage, due to twisting, braiding
    "weaving_length": 0.,
    "weight": 0.,
    "gsm_loom_state": 0.,
    "gsm": 0.,
    "price": { # in SEK
        "base_costs": 0.,
        "additional_total": 0.,
        "additional_costs": [],
        "running_per_m": 0.,
        "running_total": 0.,
        "weft_cost_per_wrap_meter": 0.,
        "warp_cost": 0.,
        "weft_cost": 0.,
        "total": 0.,
    },
}


class WeavingProject:
    def __init__(self):
        self.in_data = {}
        self.out_data = deepcopy(DEFAULT_WARP)
    
    def clear(self):
        self.in_data = {}
        self.out_data = deepcopy(DEFAULT_WARP)
    
    def _update_nested_dict(self, d, input_data):
        for k, v in input_data.items():
            if isinstance(v, abc.Mapping):
                d[k] = self._update_nested_dict(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def load_input_file(self, filepath):
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        self.in_data = deepcopy(data)
        warp_yarn = data.pop("yarn")
        products = data.pop("products")
        self.out_data = self._update_nested_dict(self.out_data, data)
        for y in warp_yarn:
            yarn_data = deepcopy(DEFAULT_YARN)
            yarn_data = self._update_nested_dict(yarn_data, y)
            yarn_id = " ".join([yarn_data["material"], yarn_data["thickness"], yarn_data["colour"]])
            yarn_id = re.sub(r'[^\w\s]', '-', yarn_id)
            yarn_id = re.sub(r'\s+', '_', yarn_id)
            self.out_data["yarn"][yarn_id] = yarn_data
        for p in products:
            weft_yarn = p.pop("yarn")
            product_data = deepcopy(DEFAULT_PRODUCT)
            product_data = self._update_nested_dict(product_data, p)
            product_id = " ". join([product_data["name"], str(product_data["ordinal"])])
            product_id = re.sub(r'[^\w\s]', '-', product_id)
            product_id = re.sub(r'\s+', '_', product_id)
            for y in weft_yarn:
                yarn_data = deepcopy(DEFAULT_YARN)
                yarn_data = self._update_nested_dict(yarn_data, y)
                yarn_id = " ".join([yarn_data["material"], yarn_data["thickness"], yarn_data["colour"]])
                yarn_id = re.sub(r'[^\w\s]', '-', yarn_id)
                yarn_id = re.sub(r'\s+', '_', yarn_id)
                product_data["yarn"][yarn_id] = yarn_data
            self.out_data["products"][product_id] = product_data
        return self.out_data
    
    def load_dump_file(self, filepath):
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        self.in_data = data["input"]
        self.out_data = data["output"]
    
    def dump_to_file(self, filepath):
        with open(filepath, 'w') as f:
            yaml.dump({"input": self.in_data, "ouput": self.out_data}, f)

    def store(self, key, value, overwrite=True):
        if not overwrite and key in self.out_data:
            return
        self.out_data[key] = value
    
    def weaving_length(self, product, refresh=False):
        if product["weaving_length"] and not refresh:
            return product["weaving_length"]

        shrinkage = 1. + self.out_data["shrinkage"]["length"] / 100.
        product["weaving_length"] = (product["length"] + product["hems"]) * shrinkage
        return product["weaving_length"]
    
    def warp_length(self, refresh=False):
        if self.out_data["warp_length"] and not refresh:
            return self.out_data["warp_length"]

        total_length = 0.
        total_length += self.out_data["sampling"]
        total_length += self.out_data["evening_weaving"]
        total_length += self.out_data["tying"]
        total_length += self.out_data["efsingar"]
        for p in self.out_data["products"].values():
            total_length += self.weaving_length(p, refresh=refresh) + p["fringes"]
        self.out_data["warp_length"] = total_length
        self.out_data["warp_yarn_length"] = total_length * self.n_ends()
        return total_length

    def n_ends(self, with_extras=True, refresh=False):
        if self.out_data["n_ends"] and not refresh:
            return self.out_data["n_ends"]

        shrinkage = 1. + self.out_data["shrinkage"]["width"] / 100.
        desired_width = self.out_data["width"]
        density = self.out_data["density"]
        pattern_ends = self.out_data["pattern_ends"]
        weaving_width = desired_width * shrinkage
        n_ends = weaving_width * density
        n_pattern_repeats = round(n_ends/pattern_ends)
        n_ends_whole_patterns = n_pattern_repeats * pattern_ends
        n_ends_total = n_ends_whole_patterns + self.out_data["extra_ends"]
        self.out_data["n_ends"] = n_ends_total
        self.out_data["n_ends_whole_patterns"] = n_ends_whole_patterns
        self.out_data["n_pattern_repeats"] = n_pattern_repeats
        if with_extras:
            return n_ends_total
        else:
            return n_ends_whole_patterns
    
    def weaving_width(self, final=False, refresh=False):
        if self.out_data["adjusted_weaving_width"] and not refresh:
            return self.out_data["adjusted_weaving_width"]

        shrinkage = 1. + self.out_data["shrinkage"]["width"] / 100.
        self.out_data["adjusted_weaving_width"] = self.n_ends(with_extras=False) / self.out_data["density"]
        self.out_data["adjusted_final_width"] = self.out_data["adjusted_weaving_width"] / shrinkage
        if final:
            return self.out_data["adjusted_final_width"]
        else:
            return self.out_data["adjusted_weaving_width"]
    
    def warp_length_all_ends(self, n_ends=None, refresh=False):
        if n_ends is None:
            if self.out_data["warp_yarn_length"] and not refresh:
                return self.out_data["warp_yarn_length"]
            else:
                self.out_data["warp_yarn_length"] = self.warp_length(refresh=refresh) * self.n_ends(refresh=refresh)
                return self.out_data["warp_yarn_length"]

        total_length = self.warp_length(refresh=refresh) * n_ends
        return total_length
    
    def _yarn_weight_warp(self, yarn, cloth_length=None, finished=True, n_ends=None, refresh=False):
        shrinkage = 1.
        if finished:
            shrinkage = 1. + self.out_data["shrinkage"]["length"] / 100.
        if yarn["weight"] and not refresh:
            if cloth_length is None:
                return yarn["weight"]
            else:
                return (cloth_length*shrinkage/self.warp_length(refresh=refresh)) * yarn["weight"]
        
        if n_ends is None:
            n_ends = round(self.n_ends(refresh=refresh) * yarn["fraction"])
            if yarn["this_for_extra_ends"]:
                n_ends += self.out_data["extra_ends"]
        
        yarn["n_ends"] = n_ends
        warp_length = self.warp_length_all_ends(n_ends=yarn["n_ends"], refresh=refresh)
        yarn["length"] = warp_length
        yarn["weight"] = kg_to_g((cm_to_m(yarn["length"]) / yarn["m_per_kg"]))
        yarn["weight"] /= (1 - yarn["m_per_kg_error"] / 100.) # Increase weight by error factor so as not to underestimate how much to buy
        if cloth_length is None:
            return yarn["weight"]
        
        return (cloth_length*shrinkage/self.warp_length(refresh=refresh)) * yarn["weight"]
    
    def _yarn_weight_weft(self, product, yarn, cloth_length=None, finished=True, refresh=False):
        shrinkage = 1.
        if finished:
            shrinkage = 1. + self.out_data["shrinkage"]["length"] / 100.
        if yarn["weight"] and not refresh:
            if cloth_length is None:
                return yarn["weight"]
            else:
                return (cloth_length*shrinkage/self.warp_length(refresh=refresh)) * yarn["weight"]
        
        if cloth_length is None:
            cloth_length = product["length"] * shrinkage
        
        yarn["length"] = product["density"] * self.weaving_length(product, refresh=refresh) * self.weaving_width(refresh=refresh)
        yarn["weight"] = kg_to_g((cm_to_m(yarn["length"]) / yarn["m_per_kg"]))
        yarn["weight"] /= (1 - yarn["m_per_kg_error"] / 100.) # Increase weight by error factor so as not to underestimate how much to buy
        if cloth_length is None:
            return yarn["weight"]
        else:
            return (cloth_length*shrinkage/self.warp_length(refresh=refresh)) * yarn["weight"]

    def product_weight(self, product, refresh=False):
        if product["weight"] and not refresh:
            return product["weight"]
        
        warp_weight = 0.
        n_ends_used = 0
        yarns = [y for y in self.out_data["yarn"].values() if not y["this_for_extra_ends"]]
        for yarn in yarns:
            warp_weight += self._yarn_weight_warp(yarn, cloth_length=self.weaving_length(product, refresh=refresh), refresh=refresh)
            n_ends_used += yarn["n_ends"]
        yarn = [y for y in self.out_data["yarn"].values() if y["this_for_extra_ends"]][0]
        n_ends = self.out_data["n_ends"] + self.out_data["extra_ends"] - n_ends_used
        warp_weight += self._yarn_weight_warp(yarn, cloth_length=self.weaving_length(product, refresh=refresh), n_ends=n_ends, refresh=refresh)

        weft_weight = 0.
        for yarn in product["yarn"].values():
            weft_weight += self._yarn_weight_weft(product, yarn, refresh=refresh)
        
        product["weight"] = warp_weight + weft_weight
        return product["weight"]
        
    def gsm(self, product, loom_state=False, refresh=False):
        if loom_state:
            if product["gsm_loom_state"] and not refresh:
                return product["gsm_loom_state"]
            
            weight = self.product_weight(product, refresh=refresh)
            width = self.weaving_width(refresh=refresh)
            length = self.weaving_length(product, refresh=refresh)
            product["gsm_loom_state"] = weight / (cm_to_m(width) * cm_to_m(length))
            return product["gsm_loom_state"]

        if product["gsm"] and not refresh:
            return product["gsm"]
        
        weight = self.product_weight(product, refresh=refresh)
        width = self.weaving_width(final=True, refresh=refresh)
        length = product["length"] + product["hems"]
        product["gsm"] = weight / (cm_to_m(width) * cm_to_m(length))
        return product["gsm"]
    
    def conversion_rate(self, yarn, refresh=False):
        if yarn["currency"] == "SEK":
            yarn["currency_conversion"] = RATES["SEK"]
            return yarn["currency_conversion"]

        if yarn["currency_conversion"] != 1. and not refresh:
            return yarn["currency_conversion"]
        
        if yarn["currency"] in RATES and not refresh:
            yarn["currency_conversion"] = RATES[yarn["currency"]]
        
        RATES[yarn["currency"]] = CurrencyRates().get_rate(yarn["currency"], "SEK")
        yarn["currency_conversion"] = RATES[yarn["currency"]]
        return yarn["currency_conversion"]

    def warp_cost_per_m(self, finished=True, refresh=False):
        if self.out_data["price"]["warp_cost_per_wrap_meter"] and not refresh:
            return self.out_data["price"]["warp_cost_per_wrap_meter"]

        cost = 0.
        n_ends_used = 0
        yarns = [y for y in self.out_data["yarn"].values() if not y["this_for_extra_ends"]]
        for yarn in yarns:
            cost_per_kg = yarn["price_per_kg"] * self.conversion_rate(yarn, refresh=refresh)
            weight = g_to_kg(self._yarn_weight_warp(yarn, cloth_length=100., finished=finished, refresh=refresh))
            cost += weight * cost_per_kg
            n_ends_used += yarn["n_ends"]
        yarn = [y for y in self.out_data["yarn"].values() if y["this_for_extra_ends"]][0]
        n_ends = self.out_data["n_ends"] + self.out_data["extra_ends"] - n_ends_used
        weight = g_to_kg(self._yarn_weight_warp(yarn, cloth_length=100., n_ends=n_ends, finished=finished, refresh=refresh))
        cost += weight * cost_per_kg

        self.out_data["price"]["warp_cost_per_wrap_meter"] = cost
        return cost
    
    def weft_cost_per_m(self, product, finished=True, refresh=False):
        if product["price"]["weft_cost_per_wrap_meter"] and not refresh:
            return product["price"]["weft_cost_per_wrap_meter"]

        cost = 0.
        for yarn in product["yarn"].values():
            cost_per_kg = yarn["price_per_kg"] * self.conversion_rate(yarn, refresh=refresh)
            weight = g_to_kg(self._yarn_weight_weft(product, yarn, cloth_length=100., finished=finished, refresh=refresh))
            cost += weight * cost_per_kg

        product["price"]["weft_cost_per_wrap_meter"] = cost
        return cost
    
    def price(self, product, refresh=False):
        if product["price"]["total"] and not refresh:
            return product["price"]["total"]
        
        price_dict = {}

        # Base price for setting up the warp
        base = 0.
        n_products = len([p for p in self.out_data["products"].keys()])
        base += self.out_data["price"]["setup"] / n_products
        base += self.out_data["price"]["base_per_wrap"]
        base += self.out_data["price"]["dyeing_warp_per_meter"] * cm_to_m(self.warp_length(refresh=refresh)) / n_products
        price_dict["base_costs"] = base

        # Running meter cost
        per_m = 0.
        per_m += self.out_data["price"]["additional_per_meter"]
        per_m += self.out_data["price"]["dyeing_weft_per_meter"]
        warp_cost_per_m = self.warp_cost_per_m(finished=True, refresh=refresh)
        per_m += warp_cost_per_m
        weft_cost_per_m = self.weft_cost_per_m(product, finished=True, refresh=refresh)
        per_m += weft_cost_per_m
        price_dict["running_per_m"] = per_m
        finished_length = cm_to_m(product["length"] + product["fringes"])
        price_dict["running_total"] = per_m * finished_length
        price_dict["warp_cost"] = warp_cost_per_m * finished_length
        price_dict["weft_cost"] = weft_cost_per_m * finished_length

        # Additional costs
        additional = 0.
        additional += sum(product["price"]["additional_costs"])
        price_dict["additional_total"] = additional

        price_dict["total"] = price_dict["base_costs"] + price_dict["running_total"] + price_dict["additional_total"]
        product["price"].update(price_dict)
        return product["price"]["total"]
    
    def product_prices(self, refresh=False):
        return_data = {}
        for product in self.out_data["products"].values():
            return_data[product["name"]] = self.price(product, refresh=refresh)
        return return_data


if __name__ == "__main__":
    project = WeavingProject()
    project.load_input_file("/Users/malin/src/github.com/mbmvelander/weaving/pebbles.yml")
    #print(cm_to_m(project.warp_length()))
    #print(project.n_ends())
    #print(json.dumps(project.yarn_weights(), indent=4))
    print(project.product_prices())
    print()
    print(yaml.safe_dump(project.out_data))
    print()
    print("Product:")
    for product in project.out_data["products"].values():
        print("    - {}: {:.2f} --> {:.2f}; SEK{:.2f}".format(product["name"], project.gsm(product, loom_state=True), project.gsm(product), project.price(product)))
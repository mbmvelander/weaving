#!/usr/bin/env python
import yaml
import json
import re
from copy import deepcopy
from collections import defaultdict
from util.conversions import cm_to_m, kg_to_g


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
    "length": 0.,
    "width": 0.,
    "pattern_ends": 0, # Number of ends in one pattern repeat
    "yarn": {},
    "products": {},
    "n_ends": 0,
    "n_pattern_repeats": 0,
    "adjusted_weaving_width": 0.,
    "adjusted_final_width": 0.,
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
}


class WeavingProject:
    def __init__(self):
        self.in_data = {}
        self.out_data = deepcopy(DEFAULT_WARP)
    
    def clear(self):
        self.in_data = {}
        self.out_data = deepcopy(DEFAULT_WARP)
    
    def load_input_file(self, filepath):
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        self.in_data = deepcopy(data)
        shrinkage = data.pop("shrinkage")
        self.out_data["shrinkage"].update(shrinkage)
        warp_yarn = data.pop("yarn")
        products = data.pop("products")
        self.out_data.update(data)
        for y in warp_yarn:
            yarn_data = deepcopy(DEFAULT_YARN)
            yarn_data.update(y)
            yarn_id = " ".join([yarn_data["material"], yarn_data["thickness"], yarn_data["colour"]])
            yarn_id = re.sub(r'[^\w\s]', '-', yarn_id)
            yarn_id = re.sub(r'\s+', '_', yarn_id)
            self.out_data["yarn"][yarn_id] = yarn_data
        for p in products:
            weft_yarn = p.pop("yarn")
            product_data = deepcopy(DEFAULT_PRODUCT)
            product_data.update(p)
            product_id = " ". join([product_data["name"], str(product_data["ordinal"])])
            product_id = re.sub(r'[^\w\s]', '-', product_id)
            product_id = re.sub(r'\s+', '_', product_id)
            for y in weft_yarn:
                yarn_data = deepcopy(DEFAULT_YARN)
                yarn_data.update(y)
                yarn_id = " ".join([yarn_data["material"], yarn_data["thickness"], yarn_data["colour"]])
                yarn_id = re.sub(r'[^\w\s]', '-', yarn_id)
                yarn_id = re.sub(r'\s+', '_', yarn_id)
                product_data["yarn"][yarn_id] = yarn_data
            self.out_data["products"][product_id] = product_data
    
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
        if self.out_data["length"] and not refresh:
            return self.out_data["length"]

        total_length = 0.
        total_length += self.out_data["sampling"]
        total_length += self.out_data["evening_weaving"]
        total_length += self.out_data["tying"]
        total_length += self.out_data["efsingar"]
        for p in self.out_data["products"].values():
            total_length += self.weaving_length(p, refresh=refresh) + p["fringes"]
        self.out_data["length"] = total_length
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
            n_ends = self.n_ends(refresh=refresh)

        total_length = self.warp_length(refresh=refresh) * n_ends
        return total_length
    
    def _yarn_weight_warp(self, yarn, n_ends=None, refresh=False):
        if yarn["weight"] and not refresh:
            return yarn["weight"]
        
        if n_ends is None:
            n_ends = round(self.n_ends(refresh=refresh)*yarn["fraction"])
        
        yarn["n_ends"] = n_ends
        yarn["length"] = self.warp_length_all_ends(n_ends=yarn["n_ends"], refresh=refresh)
        yarn["weight"] = kg_to_g((cm_to_m(yarn["length"]) / yarn["m_per_kg"]))
        yarn["weight"] /= (1 - yarn["m_per_kg_error"] / 100.) # Increase weight by error factor so as not to underestimate how much to buy
        return yarn["weight"]
    
    def _yarn_weight_weft(self, product, yarn, finished_cloth_length=None, refresh=False):
        if yarn["weight"] and not refresh:
            return yarn["weight"]
        
        if finished_cloth_length is None:
            finished_cloth_length = self.weaving_length(product, refresh=refresh) * yarn["fraction"]
        
        yarn["finished_cloth_length"] = finished_cloth_length
        yarn["length"] = product["density"] * finished_cloth_length * self.weaving_width(refresh=refresh)
        yarn["weight"] = kg_to_g((cm_to_m(yarn["length"]) / yarn["m_per_kg"]))
        yarn["weight"] /= (1 - yarn["m_per_kg_error"] / 100.) # Increase weight by error factor so as not to underestimate how much to buy
        return yarn["weight"]
    
    def yarn_weights(self, refresh=False):
        return_data = {"warp": {}, "weft": {}}

        # Warp yarns
        ends_used = 0
        weight_total = 0.
        yarns = [i for i in self.out_data["yarn"].items()]
        for yarn_id, yarn in yarns[:-1]:
            w = self._yarn_weight_warp(yarn, refresh=refresh)
            return_data["warp"][yarn_id] = w
            weight_total += w
            ends_used += yarn["n_ends"]
        yarn_id, yarn = yarns[-1]
        w = self._yarn_weight_warp(yarn, n_ends=self.n_ends(refresh=refresh) - ends_used, refresh=refresh)
        return_data["warp"][yarn_id] = w
        weight_total += w
        return_data["warp"]["total"] = weight_total

        # Weft yarns
        for product_id, product in self.out_data["products"].items():
            weight_total = 0.
            return_data["weft"][product_id] = {}
            for yarn_id, yarn in product["yarn"].items():
                w = self._yarn_weight_weft(product, yarn, refresh=refresh)
                return_data["weft"][product_id][yarn_id] = w
                weight_total += w
                ends_used += yarn["n_ends"]
        return return_data

    def warp_total_weight(self, n_ends=None):
        return


if __name__ == "__main__":
    project = WeavingProject()
    project.load_input_file("/Users/malin/src/github.com/mbmvelander/weaving/pebbles.yml")
    print(cm_to_m(project.warp_length()))
    print(project.n_ends())
    print(json.dumps(project.yarn_weights(), indent=4))
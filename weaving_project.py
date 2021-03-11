#!/usr/bin/env python
import yaml
from copy import deepcopy
from collections import defaultdict
from util.conversions import cm_to_m


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
    "yarn": [],
    "products": [],
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
}


DEFAULT_PRODUCT = {
    "ordinal": 0,
    "name": "Unnamed",
    "length": 0.,
    "hems": 0.,
    "fringes": 0.,
    "density": 10.,
    "yarn": [],
    "fringe_shortening": 20., # percentage, due to twisting, braiding
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
            self.out_data["yarn"].append(yarn_data)
        for p in products:
            weft_yarn = p.pop("yarn")
            product_data = deepcopy(DEFAULT_PRODUCT)
            product_data.update(p)
            for y in weft_yarn:
                yarn_data = deepcopy(DEFAULT_YARN)
                yarn_data.update(y)
                product_data["yarn"].append(yarn_data)
            self.out_data["products"].append(product_data)
    
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
    
    def warp_length(self):
        if self.out_data["length"]:
            return self.out_data["length"]

        total_length = 0.
        total_length += self.out_data["sampling"]
        total_length += self.out_data["evening_weaving"]
        total_length += self.out_data["tying"]
        total_length += self.out_data["efsingar"]
        shrinkage = 1. + self.out_data["shrinkage"]["length"] / 100.
        for p in self.out_data["products"]:
            weaving_length = (p["length"] + p["hems"]) * shrinkage
            total_length += weaving_length + p["fringes"]
        self.out_data["length"] = total_length
        return total_length

    def n_ends(self):
        if self.out_data["n_ends"]:
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
        self.out_data["n_pattern_repeats"] = n_pattern_repeats
        self.out_data["adjusted_weaving_width"] = n_ends_whole_patterns / density
        self.out_data["adjusted_final_width"] = self.out_data["adjusted_weaving_width"] / shrinkage
        return n_ends_total



if __name__ == "__main__":
    project = WeavingProject()
    project.load_input_file("/Users/malin/src/github.com/mbmvelander/weaving/pebbles.yml")
    print(cm_to_m(project.warp_length()))
    print(project.n_ends())
#!/usr/bin/env python3

import yaml
import sys
import json
from lxml import etree

PADDING = 0.25

def validate_pinout(pinout):
    if "name" not in pinout:
        raise RuntimeError("Missing board name in pinout")
    if "pins" not in pinout:
        raise RuntimeError("Missing pin definition in pinout")
    if "mapping" not in pinout:
        raise RuntimeError("Missing mapping definition in pinout")
    # ToDo: More checks

def add_checkboxes(template, parent_id, items):
    parent = template.find(".//*[@id='" + parent_id + "']")
    for p in items:
        li = etree.SubElement(parent, "li")
        input = etree.SubElement(li, "input")
        input.attrib["type"] = "checkbox"
        input.attrib["name"] = p
        label = etree.SubElement(li, "label")
        label.attrib["for"] = p
        label.text = p

if __name__ == "__main__":
    template = etree.HTML(open("template.html", "r").read())
    pinout = yaml.load(open("pinout.yaml", "r"))
    try:
        validate_pinout(pinout)
    except RuntimeError as e:
        print(e.message)
        sys.exit(1)

    for i in template.getiterator():
        print(i.tag)
    print(pinout)

    # Pins descriptions
    id_to_pin = {"pin_" + str(i): p for i, p in enumerate(pinout["pins"].keys())}
    pin_to_id = {p: "pin_" + str(i) for i, p in enumerate(pinout["pins"].keys())}
    script = etree.SubElement(template.find("head"), "script")
    script.text = "id_to_pin = {};\npin_to_id = {}; pins = {};\n" \
        .format(json.dumps(id_to_pin), json.dumps(pin_to_id), json.dumps(pinout["pins"]))

    # Set page titles
    name = pinout["name"]
    template.find(".//*title").text = name
    template.find(".//*[@id='name']").text = name

    # Properties
    general = list(set([x for p in pinout["pins"].values() for x in p["general features"]]))
    general.sort()
    add_checkboxes(template, "general-features", general)

    peripherals = list(set([x for p in pinout["pins"].values() for x in p["peripherals"]]))
    peripherals.sort()
    add_checkboxes(template, "peripherals", peripherals)

    # Generate image map
    board = template.find(".//*[@id='board']")
    for mapping in pinout["mapping"]:
        x, y, w, h = mapping["position"]
        c_x, c_y = mapping["size"]
        w /= c_x
        h /= c_y
        for i in range(c_y):
            for j in range(c_x):
                idx = c_x * i + j
                if idx >= len(mapping["pins"]):
                    break
                l_x = x + j * w
                l_y = y + i * h
                item = etree.SubElement(board, "a")
                item.attrib["style"] = "top: {}%; left: {}%; width: {}%; height:{}%" \
                    .format(l_y + PADDING / 2, l_x + PADDING / 2, w - PADDING, h - PADDING)
                # item.attrib["data-toggle"] = "tooltip"
                item.attrib["data-placement"] = "auto"
                pin = mapping["pins"][idx]
                item.attrib["title"] = pin
                item.attrib["onmousedown"] = "pinMouseClick(event, \"{}\");".format(pin_to_id[pin])
                item.attrib["onmouseenter"] = "pinMouseEnter(\"{}\");".format(pin_to_id[pin])
                item.attrib["onmouseleave"] = "pinMouseLeave(\"{}\");".format(pin_to_id[pin])
                item.attrib["class"] = "pin " + pin_to_id[pin]

    et = etree.ElementTree(template)
    et.write("output.html", pretty_print=True, method="html");
    print(etree.tostring(template, pretty_print=True, method="html").decode("utf-8"))

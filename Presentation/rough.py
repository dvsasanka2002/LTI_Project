# -*- coding: utf-8 -*-
from xml.etree import ElementTree as ET

def build_xpath(node, path):
    components = path.split("/")
    if components[0] == node.tag:
        components.pop(0)
    while components:
        # take in account positional  indexes in the form /path/para[3] or /path/para[location()=3]
        if "[" in components[0]:
            component, trail = components[0].split("[",1)
            target_index = int(trail.split("=")[-1].strip("]"))
        else:
            component = components[0]
            target_index = 0
        components.pop(0)
        found_index = -1
        for child in node.getchildren():
            if child.tag == component:
                found_index += 1
                if found_index == target_index:
                    node = child
                    break
        else:
            for i in range(target_index - found_index):
                new_node = ET.Element(component)
                node.append(new_node)
            node = new_node


if __name__  == "__main__":
    #Example
    root = ET.Element("root")
    build_xpath(root, "root/foo/bar[position()=4]/snafu")
    print(ET.tostring(root))
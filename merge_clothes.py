from lxml import etree

for filename in ["boyClothes", "girlClothes"]:
    doc = etree.parse(f"config_all_ru/inventory/{filename}.xml")
    new_doc = etree.parse(f"files/config/inventory/{filename}.xml")
    root = doc.getroot()
    new_root = new_doc.getroot()
    for category in new_root.xpath("//category[@logCategory2]"):
        tmp = category.attrib["logCategory2"]
        orig_category = root.xpath(f"//category[@logCategory2='{tmp}']")[0]
        for item in category:
            if item.tag != "item":
                continue
            if orig_category.xpath(f"//item[@id='{item.attrib['id']}']"):
                continue
            orig_category.append(item)
    string = etree.tostring(root, pretty_print=True,
                            xml_declaration=True).decode()
    with open(f"config_all_ru/inventory/{filename}.xml", "w") as f:
        f.write(string)

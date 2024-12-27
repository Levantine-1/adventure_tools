import time

from escpos.printer import Network
import textwrap
import yaml
import sys
import math
from PIL import Image
from prettytable import PrettyTable
import validators
import os
import urllib.request
import json

printer_ip = "10.69.69.10"

printerprint = Network(printer_ip, profile="TM-T88V")

# "screen" or "paper"
mode = "paper"


config_sheet = sys.argv[1]


banners = {
    "stats":    "================= Stats ==================",
    "score":    "        ==== Scores & Modifiers ====      ",
    "skills":   "================ Skills ==================",
    "cr":       "============ Challenge Rating ============",
    "descr":    "============== Description ===============",
    "dm_rules": "=========== Special DM Rules =============",
    "sp_mats":  "============ Spell Materials ============="
}

def tabs_to_spaces(path):
    with open (path, "r") as file:
        data = file.read()
        content = data.replace('\t', ' ' * 4)

    with open(path, 'w') as file:
        file.write(content)
    file.close()

def print_text(text, **no_newline):
    pp_newline = '''
'''
    newline = "\n"

    try:
        no_newline = no_newline["no_newline"]
        if no_newline is True:
            pp_newline = ''''''
            newline = ""
    except KeyError:
        pass

    if mode == "screen":
        printer = print
    else:
        printer = printerprint.text

    wrapper = textwrap.TextWrapper(width=42)
    try:
        for line in text.splitlines():
            char_count = len(line)
            if char_count == 0:
                printer(pp_newline)
            elif char_count > 42:
                line_list = wrapper.wrap(text=line)
                for line_list_element in line_list:
                    printer(line_list_element + newline)
            elif char_count < 43:
                printer(line)
    except AttributeError:
        printer(text)
    printer(pp_newline)


def print_image(img_location):
    if validators.url(img_location):  # Checks to see if valid URL
        print("Using image from URL")
        cache_path = "images/cached_images/" + os.path.basename(img_location)
        if not os.path.isfile(cache_path):  # If cached image doesn't exist, download it
            print("Downloading image to cache")
            download_path = "images/cached_images/" + os.path.basename(img_location)
            try:
                urllib.request.urlretrieve(img_location, download_path)
            except Exception as err:
                print(err)
        else:
            print("Serving cached image")
        img_location = cache_path

    if os.path.isfile(img_location):
        print("Serving image from file")
        picture = Image.open(img_location)
    else:
        print("Unable to serve a picture")
        # picture = Image.open("images/default.jpg")
        return None

    try:
        max_height = int(conf["max_height"])
    except KeyError:
        max_height = 650
    max_width = 500
    new_width = max_width  # Initializing

    picture_width = picture.size[0]
    picture_height = picture.size[1]

    new_height = int(max_width * picture_height / float(picture_width))  # Resize and maintain aspect ratio
    if new_height > max_height:
        new_width = int(max_height * max_width / float(new_height))
        new_height = int(new_width * new_height / float(max_width))
    resized = picture.resize((new_width, new_height))
    rotated = resized.rotate(conf["image_rotation"])
    black_white = rotated.convert("1")
    printerprint.image(black_white, center=True)


def calculate_modifier(ability_score):
    try:
        int_ability_score = int(ability_score)
        modifier = math.floor((int_ability_score - 10)/2)  # Round down
        if modifier < 0:
            prefix = ""
        else:
            prefix = "+"
        mod_string = prefix + str(modifier)
        return mod_string
    except ValueError:
        return ability_score


def print_stats_chart():
    stat_table = PrettyTable()
    stat_table.max_table_width = 42
    stat_table.field_names = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

    AC = str(conf["stats"]["ArmorClass"])
    HP = str(conf["stats"]["HP"])

    printerprint.text("          AC: " + AC + "           HP: " + HP + "\n")
    # printerprint.text(banners["score"])

    STR = str(conf["stats"]["STR"])
    DEX = str(conf["stats"]["DEX"])
    CON = str(conf["stats"]["CON"])
    INT = str(conf["stats"]["INT"])
    WIS = str(conf["stats"]["WIS"])
    CHA = str(conf["stats"]["CHA"])
    stat_table.add_row([STR, DEX, CON, INT, WIS, CHA])

    STR_MOD = calculate_modifier(ability_score=STR)
    DEX_MOD = calculate_modifier(ability_score=DEX)
    CON_MOD = calculate_modifier(ability_score=CON)
    INT_MOD = calculate_modifier(ability_score=INT)
    WIS_MOD = calculate_modifier(ability_score=WIS)
    CHA_MOD = calculate_modifier(ability_score=CHA)
    stat_table.add_row([STR_MOD, DEX_MOD, CON_MOD, INT_MOD, WIS_MOD, CHA_MOD])
    printerprint.text(stat_table)
    printerprint.text("\n")
    return True


def print_skills():
    for skill in conf["skills"]:
        print_text(text=skill)
        for description in conf["skills"][skill]["Descriptions"]:
            description = " - " + description
            print_text(text=description)


def generate_character_card():
    print_text(text=conf["name"])
    print_image(img_location=conf["image_location"])
    print_text(text=conf["physical_description"])
    print_text(text=conf["alignment"])
    print_text(text=banners["stats"])
    print_stats_chart()
    print_text(text=banners["skills"])
    print_skills()
    print_text(text=banners["cr"])
    print_text(text=conf["challenge_rating"])
    print_text(text=banners["descr"])
    print_text(text=conf["description"])
    printerprint.cut()


def print_5e_item_card():
    ignore_keys = ["name", "source", "page", "tier", "rarity", "hasFluffImages", "srd", "additionalSources", "excludes",
                   "inherits", "otherSources"]

    data = json.loads(conf["json_data"])

    title = data["name"]
    source = data["source"] + "." + str(data["page"])
    try:
        tier = data["tier"]
    except KeyError:
        tier = "N/A"
    try:
        rarity = data["rarity"]
    except KeyError:
        rarity = "N/A"

    print_text(text=title)
    print_image(img_location=conf["image_location"])

    stat_table = PrettyTable()
    stat_table.max_width = 42
    stat_table.field_names = ["tier", "rarity", "source"]
    stat_table.add_row([tier, rarity, source])
    printerprint.text(stat_table)
    printerprint.text("\n")

    for key in data:
        if key not in ignore_keys:
            if type(data[key]) is list:
                print_text(text="")
                string = "## " + key + " ####"
                print_text(text=string)
                for entry in data[key]:
                    if type(entry) is dict:
                        if key == "variants":
                            for variant in data["variants"]:
                                item_variant = variant["base"]["name"]
                                string = "- " + item_variant
                                print_text(text=string, no_newline=False)
                        else:
                            for dict_key in entry:
                                string = str(dict_key) + ": " + str(entry[dict_key])
                                print_text(text=string)
                    if key == "variants":
                        break
                    print_text(text=str(entry))
                print_text(text="")
            elif type(data[key]) is not (list, dict):
                string = str(key) + ": " + str(data[key])
                print_text(text=string)

    printerprint.text(banners["dm_rules"])
    printerprint.text(conf["dm_rules"])
    printerprint.cut()


def print_spell_constants(data):
    spell_school_key = {
        "A": "Abjuration",
        "C": "Conjuration",
        "D": "Divination",
        "E": "Enchantment",
        "V": "Evocation",
        "I": "Illusion",
        "N": "Necromancy",
        "T": "Transmutation"
    }

    source = data["source"] + "." + str(data["page"])

    range_type = data["range"]["type"]
    range_dist_in_hex = "N/A"
    if data["range"]["distance"]["type"] == "self":
        range_dist_in_hex = "Self"
    else:
        try:
            range_dist_in_hex = math.floor(data["range"]["distance"]["amount"]/5)
        except KeyError:
            range_dist_in_hex = data["range"]["distance"]["type"]

    verbal = str(data["components"]["v"]).capitalize()
    somatic = str(data["components"]["s"]).capitalize()
    material_components = ""
    try:
        material_components = data["components"]["m"]
        if material_components:
            uses_materials = "True"
        else:
            uses_materials = "False"
    except KeyError:
        uses_materials = "False"

    school = "Level " + str(data["level"]) + " " + spell_school_key[data["school"]]

    components_table = PrettyTable()
    components_table.max_table_width = 42
    components_table.field_names = ["Verbal", "Somatic", "Material"]
    components_table.add_row([verbal, somatic, uses_materials])

    cast_time = str(data["time"][0]["number"]) + " " + str(data["time"][0]["unit"])
    duration_type = data["duration"][0]["type"]
    spell_duration = "N/A"
    if duration_type == "instant":
        spell_duration = "Instant"
    elif duration_type == "timed":
        amount = str(data["duration"][0]["duration"]["amount"])
        unit = str(data["duration"][0]["duration"]["type"])
        spell_duration = amount + " " + unit
    try:
        concentration = data["duration"][0]["concentration"]
    except KeyError:
        concentration = "False"
    unit_duration_table = PrettyTable()
    unit_duration_table.max_table_width = 42
    unit_duration_table.field_names = ["Cast Time", "Duration", "Concentrate"]
    unit_duration_table.add_row([cast_time, spell_duration, concentration])

    range_table = PrettyTable()
    range_table.max_table_width = 42
    range_table.field_names = ["Range Type", "Range Dist(Hex)"]
    range_table.add_row([range_type, range_dist_in_hex])



    print_text(text=school)
    printerprint.text(components_table)
    printerprint.text("\n")
    printerprint.text(unit_duration_table)
    printerprint.text("\n")
    printerprint.text(range_table)
    printerprint.text("\n")
    printerprint.text(banners["sp_mats"])
    print_text(text=material_components)
    printerprint.text("\n")


def print_5e_spell_card():
    ignore_keys = ["otherSources", "time", "range", "components", "duration", "classes", "areaTags", "level", "school",
                   "source", "page", "name", "feats", "miscTags", "entriesHigherLevel"]
    data = json.loads(conf["json_data"])

    title = data["name"]

    print_text(text=title)
    print_image(img_location=conf["image_location"])
    print_spell_constants(data)

    for key in data:
        if key == "classes":
            class_list = data[key].get("fromClassList", [])
            subclass_list = data[key].get("fromSubclass", [])

            print_text(text="Classes:")
            for class_entry in class_list:
                class_name = class_entry.get("name", "Unknown")
                print_text(text=f"- {class_name}")

            print_text(text="Subclasses:")
            for subclass_entry in subclass_list:
                class_name = subclass_entry.get("class", {}).get("name", "Unknown")
                subclass_name = subclass_entry.get("subclass", {}).get("name", "Unknown")
                print_text(text=f"- {class_name}: {subclass_name}")
        if key == "feats":
            feat_list = data[key]
            print_text(text="Feats:")
            for feat_entry in feat_list:
                feat_name = feat_entry.get("name", "Unknown")
                print_text(text=f"- {feat_name}")
        if key == "entriesHigherLevel":
            entries_higher_level = data[key]

            print_text(text="Entries Higher Level:")
            for entry in entries_higher_level:
                entry_name = entry.get("name", "Unknown")
                print_text(text=f"- {entry_name}")
                for sub_entry in entry.get("entries", []):
                    print_text(text=f"  - {sub_entry}")
        if key not in ignore_keys:
            if type(data[key]) is list:
                print_text(text="")
                string = "## " + key + " ####"
                print_text(text=string)
                for entry in data[key]:
                    if type(entry) is dict:
                        for dict_key in entry:
                            string = str(dict_key) + ": " + str(entry[dict_key])
                            print_text(text=string)
                    string = "- " + str(entry)
                    print_text(text=string)
                print_text(text="")
            elif type(data[key]) is not (list, dict):
                string = str(key) + ": " + str(data[key])
                print_text(text=string)

    printerprint.text(banners["dm_rules"])
    printerprint.text(conf["dm_rules"])
    printerprint.cut()


def generate_item_card():
    if conf["data_source"] == "5etools":
        print_5e_item_card()
    else:
        print_text(text=conf["name"])
        print_image(img_location=conf["image_location"])
        print_text(text=banners["descr"])
        print_text(text=conf["description"])
        printerprint.cut()


def generate_spell_card():
    if conf["data_source"] == "5etools":
        print_5e_spell_card()
    else:
        print_text(text=conf["name"])
        print_image(img_location=conf["image_location"])
        print_text(text=banners["descr"])
        print_text(text=conf["description"])
        printerprint.cut()


def generate_custom_card():
    print_image(img_location=conf["image_location"])
    print_text(text=conf["description"])
    printerprint.cut()


try:
    with open(config_sheet) as f:
        conf = yaml.safe_load(f)
except FileNotFoundError:
    print("Error config sheet not found!")
    exit(1)
except yaml.YAMLError:
    try:
        print("Warning, Unable to parse config, trying to convert tabs to spaces")
        tabs_to_spaces(config_sheet)
        with open(config_sheet) as f:
            conf = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error parsing config sheet: {e}")
        exit(1)

if conf["card_type"] == "character":
    generate_character_card()
elif conf["card_type"] == "item":
    generate_item_card()
elif conf["card_type"] == "spell":
    generate_spell_card()
elif conf["card_type"] == "quest":
    pass
elif conf["card_type"] == "plaintext":
    generate_custom_card()



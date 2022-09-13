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

printer_ip = "10.69.69.10"

printerprint = Network(printer_ip)

config_sheet = sys.argv[1]
try:
    with open(config_sheet) as f:
        conf = yaml.safe_load(f)
except FileNotFoundError:
    print("Error config sheet not found!")
    exit(1)

banners = {
    "stats":  "================= Stats ==================",
    "score":  "        ==== Scores & Modifiers ====      ",
    "skills": "================ Skills ==================",
    "cr":     "============ Challenge Rating ============",
    "descr":  "============== Description ==============="
}


def print_text(text):
    pp_newline = '''
'''
    wrapper = textwrap.TextWrapper(width=42)
    for line in text.splitlines():
        char_count = len(line)
        if char_count == 0:
            printerprint.text(pp_newline)
        elif char_count > 42:
            line_list = wrapper.wrap(text=line)
            for line_list_element in line_list:
                printerprint.text(line_list_element + "\n")
        elif char_count < 43:
            printerprint.text(line)
    printerprint.text(pp_newline)


def print_image(img_location):
    if validators.url(img_location):  # Checks to see if valid URL
        cache_path = "images/cached_images/" + os.path.basename(img_location)
        if not os.path.isfile(cache_path):  # If cached image doesn't exist, download it
            download_path = "images/cached_images/" + os.path.basename(img_location)
            try:
                urllib.request.urlretrieve(img_location, download_path)
            except:
                pass
        img_location = cache_path

    if os.path.isfile(img_location):
        picture = Image.open(img_location)
    else:
        picture = Image.open("images/default.jpg")
    resized = picture.resize((500, 650))
    black_white = resized.convert("1")
    # black_white.show() # Display on screen
    printerprint.image(black_white, center=True)


def calculate_modifier(ability_score):
    int_ability_score = int(ability_score)
    modifier = math.floor((int_ability_score - 10)/2)  # Round down
    if modifier < 0:
        prefix = ""
    else:
        prefix = "+"
    mod_string = prefix + str(modifier)
    return mod_string


def print_stats_chart():
    stat_table = PrettyTable()
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


def generate_npc_card():
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


generate_npc_card()


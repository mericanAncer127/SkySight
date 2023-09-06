import argparse
from datetime import date
from glob import glob
import matplotlib.pyplot as plt
import numpy as np
import os
from PIL import Image, ImageFont, ImageDraw
from create_diagrams import *
from sketch_to_sheet import *


ADDRESS = "153 Polly Anna Drive, West Monroe, LA, USA"
COMPANY = "Frontier Roofing & Construction LLC"
CONTACT = "daniel@frontierhomex.com"

ADDRESS_FONT = ImageFont.truetype("fonts/Lucida Grande.ttf", 42)
DATE_FONT = ImageFont.truetype("fonts/Lucida Grande.ttf", 32)
CONTACT_1_FONT = ImageFont.truetype("fonts/Lucida Grande.ttf", 32)
CONTACT_2_FONT = ImageFont.truetype("fonts/Lucida Grande.ttf", 20)
MEASUREMENTS_FONT = ImageFont.truetype("fonts/Lucida Grande.ttf", 20)
AREA_FONT = ImageFont.truetype("fonts/Lucida Grande Bold.ttf", 24)
LENGTHS_FONT = ImageFont.truetype("fonts/Lucida Grande.ttf", 24)
SUMMARY_FONT = ImageFont.truetype("fonts/Lucida Grande Bold.ttf", 24)

WASTE_PERCENTAGES = [
    1,
    1.1,
    1.12,
    1.15,
    1.17,
    1.2,
    1.22
]

def process_datasheet(roof, fontsize=8, datasheet="data_sheet.csv"):
    return create_diagrams(roof, fontsize, datasheet=datasheet)

def draw_underlined_text(draw, pos, text, font, color, **options):
    twidth, _ = draw.textsize(text, font=font)
    _, theight = draw.textsize("o", font=font)
    lx, ly = pos[0], pos[1] + theight + 3
    draw.text(pos, text, color, font=font, **options)
    draw.line((lx, ly, lx + twidth, ly), color, **options)
    return

def get_fit_image(img, bbox):
    bbox_w = bbox[1] - bbox[0]
    bbox_h = bbox[3] - bbox[2]

    bbox_aspect_ratio = bbox_w / bbox_h
    img_aspect_ratio = img.size[0] / img.size[1]

    if img_aspect_ratio > bbox_aspect_ratio:

        img_w = bbox_w
        img_h = int(bbox_w / img_aspect_ratio)

        pos = (bbox[0], bbox[2] + int(bbox_h / 2 - img_h / 2))

    else:
        img_h = bbox_h
        img_w = int(bbox_h * img_aspect_ratio)

        pos = (bbox[0] + int(bbox_w / 2 - img_w / 2), bbox[2])

    return img.resize((img_w, img_h)), pos

class ReportWriter:

    def __init__(
        self,
        folder,
        address,
        company,
        contact,
        measurements
    ):
        self.folder = folder
        self.address = address
        self.company = company
        self.contact = contact
        self.measurements = measurements
        return

    def add_header_to_img(self, img):
        draw = ImageDraw.Draw(img)

        draw.text((125, 170), self.address, (255,255,255),
                  font=ADDRESS_FONT)

        _date = date.today().strftime("%B %d, %Y")

        w, h = DATE_FONT.getsize(_date)
        draw.text((1150 - w, 95), _date, (100,100,100),
                  font=DATE_FONT)

        return img

    def make_page_0(self):
        page = Image.open("report_page_templates/page_0.jpg")

        page = self.add_header_to_img(page)

        draw = ImageDraw.Draw(page)

        def fill_contact_box():
            draw_underlined_text(draw, (180, 1180), "Company:",
                                CONTACT_1_FONT, (0,0,0))

            draw_underlined_text(draw, (180, 1230), "Contact:",
                                CONTACT_1_FONT, (0,0,0))

            draw.text((350, 1188), self.company, (0,0,0), font=CONTACT_2_FONT)

            draw.text((320, 1237), self.contact, (0,0,0), font=CONTACT_2_FONT)

        def fill_key_measurements():
            i = 0
            y_pos = 810
            for i in range(8):
                if i == 0:
                    text = '{0:,.0f}'.format(self.measurements[i]) + " sq. ft."
                    draw.text((940, y_pos), text, (0,0,0),
                            font=MEASUREMENTS_FONT)

                elif i > 2:
                    text = '{0:,}'.format(self.measurements[i]) + " ft."
                    draw.text((940, y_pos), text, (0,0,0),
                            font=MEASUREMENTS_FONT)

                else:
                    text = str(self.measurements[i])
                    draw.text((940, y_pos), text, (0,0,0),
                            font=MEASUREMENTS_FONT)


                if i % 2 == 0:
                    y_pos += 31
                else:
                    y_pos += 32

        def add_image():
            box_left = 200
            box_right = 650
            box_top = 375
            box_bottom = 1080

            img = Image.open(os.path.join(self.folder, "top.png"))

            img, pos = get_fit_image(img, (box_left, box_right, box_top, box_bottom))

            page.paste(img, pos)

            return

        fill_contact_box()
        fill_key_measurements()
        add_image()

        return page

    def make_page_1(self):
        page = Image.open("report_page_templates/page_1.jpg")

        page = self.add_header_to_img(page)

        def add_image():
            box_left = 160
            box_right = 1110
            box_top = 385
            box_bottom = 1350

            img = Image.open(os.path.join(self.folder, "top.png"))

            img, pos = get_fit_image(img, (box_left, box_right, box_top, box_bottom))

            page.paste(img, pos)

            return

        add_image()

        return page

    def make_page_2(self):
        page = Image.open("report_page_templates/page_2.jpg")

        page = self.add_header_to_img(page)

        draw = ImageDraw.Draw(page)

        draw.text((995, 370),
                  '{0:,.0f}'.format(self.measurements[0]) + " sq. ft.",
                  (0,0,0), font=AREA_FONT)

        def add_image():
            box_left = 160
            box_right = 1110
            box_top = 385
            box_bottom = 1350

            img = Image.open(os.path.join(self.folder, "Area.png"))

            img, pos = get_fit_image(img, (box_left, box_right, box_top, box_bottom))

            page.paste(img, pos)

            return

        add_image()

        return page

    def make_page_3(self):
        page = Image.open("report_page_templates/page_3.jpg")

        page = self.add_header_to_img(page)

        draw = ImageDraw.Draw(page)

        def fill_length_table():
            y_pos = 393

            COLORS = [
                (255,34,0),
                (255,136,0),
                (0,118,197),
                (69,163,38),
                (72,72,72)
            ]

            for i in range(3,8):
                text = '{0:,}'.format(self.measurements[i])
                w, h = LENGTHS_FONT.getsize(text)

                draw.text((1070 - w / 2, y_pos), text,
                    COLORS[i-3], font=LENGTHS_FONT)

                if i % 2 == 0:
                    y_pos += 39
                else:
                    y_pos += 40

        def add_image():
            box_left = 160
            box_right = 1110
            box_top = 600
            box_bottom = 1350

            img = Image.open(os.path.join(self.folder, "Length.png"))

            img, pos = get_fit_image(img, (box_left, box_right, box_top, box_bottom))

            page.paste(img, pos)

            return

        fill_length_table()
        add_image()

        return page

    def make_page_4(self):
        page = Image.open("report_page_templates/page_4.jpg")

        page = self.add_header_to_img(page)

        def add_image():
            box_left = 160
            box_right = 1110
            box_top = 385
            box_bottom = 1350

            img = Image.open(os.path.join(self.folder, "Pitch.png"))

            img, pos = get_fit_image(img, (box_left, box_right, box_top, box_bottom))

            page.paste(img, pos)

            return

        add_image()

        return page

    def make_page_5(self):
        page = Image.open("report_page_templates/page_5.jpg")

        page = self.add_header_to_img(page)

        draw = ImageDraw.Draw(page)

        def fill_pitch_and_area_table():
            table_left = 375
            table_right = 1120
            table_top = 462
            table_bottom = 553

            cols = len(self.measurements[8])

            col_lines_x = np.linspace(table_left, table_right, cols, endpoint=False)

            if cols > 1:
                half_col_w = int((col_lines_x[1] - table_left) / 2)
            else:
                half_col_w = int((table_right - table_left) / 2)

            for pitch, col_line_x in zip(self.measurements[8].keys(), col_lines_x):

                draw.line((col_line_x, table_top, col_line_x, table_bottom), fill=0, width=2)

                x_pos = col_line_x + half_col_w

                pitch_text = '{0:,.0f}'.format(pitch)
                area_text = '{0:,.0f}'.format(self.measurements[8][pitch])
                percent_text = str(int(100 * self.measurements[8][pitch] / self.measurements[0])) + "%"

                draw.text((x_pos - SUMMARY_FONT.getsize(pitch_text)[0] / 2, 469), pitch_text, (0,0,0), font=SUMMARY_FONT)
                draw.text((x_pos - SUMMARY_FONT.getsize(area_text)[0] / 2, 500), area_text, (0,0,0), font=SUMMARY_FONT)
                draw.text((x_pos - SUMMARY_FONT.getsize(percent_text)[0] / 2, 531), percent_text, (0,0,0), font=SUMMARY_FONT)

            return

        def fill_waste_table():
            table_left = 283
            table_right = 1125
            table_top = 818
            table_bottom = 755

            area = self.measurements[0]

            x_pos = 344
            spacing = 120

            for waste_percentage in WASTE_PERCENTAGES:
                curr_area = area * waste_percentage
                area_text = '{0:,.0f}'.format(curr_area)
                square_text = '{0:.1f}'.format(curr_area / 100)

                draw.text((x_pos - SUMMARY_FONT.getsize(area_text)[0] / 2, 763), area_text, (0,0,0), font=SUMMARY_FONT)
                draw.text((x_pos - SUMMARY_FONT.getsize(square_text)[0] / 2, 794), square_text, (0,0,0), font=SUMMARY_FONT)

                x_pos += spacing

            return

        def fill_length_table():
            x_pos = 408
            y_pos = 1040
            x_spacing = 159

            for i in range(3,8):
                length_text = '{0:,}'.format(self.measurements[i])

                draw.text((x_pos - SUMMARY_FONT.getsize(length_text)[0] / 2, y_pos), length_text, (0,0,0), font=SUMMARY_FONT)

                x_pos += x_spacing

            return


        fill_pitch_and_area_table()
        fill_waste_table()
        fill_length_table()

        return page

    def create_report(self):
        filename = os.path.join(self.folder+"/report.pdf")

        cover_img = self.make_page_0()

        page_imgs = [
            self.make_page_1(),
            self.make_page_2(),
            self.make_page_3(),
            self.make_page_4(),
            self.make_page_5(),
        ]

        cover_img.save(filename, "PDF", resolution=100.0,
                       save_all=True, append_images=page_imgs)

        return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--f", dest="folder")
    parser.add_argument("--s", dest="size", default=8)

    args = parser.parse_args()

    roof = Roof(args.folder, args.size)

    roof_line_map, pitch_area_map, face_count = process_datasheet(roof, args.size)

    measurements = [
        sum(pitch_area_map.values()),
        face_count,
        '{0:,.0f}'.format(max(pitch_area_map, key=pitch_area_map.get)) + "/12",
        roof_line_map["R"],
        roof_line_map["H"],
        roof_line_map["V"],
        roof_line_map["K"],
        roof_line_map["E"],
        pitch_area_map
    ]

    writer = ReportWriter(
        args.folder,
        ADDRESS,
        COMPANY,
        CONTACT,
        measurements
    )

    writer.create_report()





import os
from datetime import datetime
import fpdf

FONTS_DIR = 'font'

class PDF(fpdf.FPDF):
    def header(self):
        self.set_font('Roboto', '', 10)
        # Move to the right
        # self.cell(80)
        # Title
        self.cell(0, 10, self.title, 0, 2, 'C')
        self.cell(0, 0, border=1)
        # Line break
        self.ln(5)

    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Roboto', 'I', 6)
        # Page number
        self.cell(0, 0, border=1)
        self.ln(1)
        self.cell(0, 10, 'Page ' + str(self.page_no()) + ' ' * 20 +'confidential. Printed date: {:%Y/%m/%d}'.format(datetime.today()) , 0, 0, 'C')
        # self.cell(150, 10, 'confidential. {:%Y/%m/%d}'.format(datetime.today()) + '/{nb}', 0, 0, 'R')

    def __init__(self, orientation='P', unit='mm', format='A4', title='', top_margin = 5):
        super().__init__(orientation=orientation, unit=unit, format=format)
        # fonts = [
        #     f for f in os.listdir(freestyle_directory) 
        #     if os.path.isfile(os.path.join(freestyle_directory, f)) 
        #     and f.endswith('ttf')
        # ]
        # for font in fonts
        fpdf.set_global("SYSTEM_TTFONTS", os.path.join(os.path.dirname(''),FONTS_DIR))
        self.add_font("Roboto", style="", fname=os.path.abspath("fonts/" + "Roboto-Regular.ttf"), uni=True)
        self.add_font("Roboto", style="B", fname=os.path.abspath("fonts/" + "Roboto-Bold.ttf"), uni=True)
        self.add_font("Roboto", style="I", fname=os.path.abspath("fonts/" + "Roboto-Italic.ttf"), uni=True)
        self.add_font("Roboto", style="BI", fname=os.path.abspath("fonts/" + "Roboto-BoldItalic.ttf"), uni=True)
        self.add_font("Lato", style="", fname=os.path.abspath("fonts/" + "Lato-Regular.ttf"), uni=True)
        self.add_font("Lato", style="B", fname=os.path.abspath("fonts/" + "Lato-Bold.ttf"), uni=True)
        self.add_font("Lato", style="I", fname=os.path.abspath("fonts/" + "Lato-Italic.ttf"), uni=True)
        self.add_font("Lato", style="BI", fname=os.path.abspath("fonts/" + "Lato-BoldItalic.ttf"), uni=True)
        self.add_font("Ephesis", style="", fname=os.path.abspath("fonts/" + "Ephesis-Regular.ttf"), uni=True)
        self.alias_nb_pages()
        self.title=title
        self.set_top_margin(top_margin)


#!/usr/bin/env python3

# Python built-in modules
import argparse, io, os, pickle, sys, shutil, subprocess, tempfile, time
from typing import List, Tuple, Optional
from pathlib import Path

# modules need to install
from paddleocr import PaddleOCR
from PIL import Image
from PyPDF2 import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import Color

from pdf_util import RootLogger, PdfUtil

class PdfOCRer:
    def __init__(self, debug: bool = False, temp_dir: Optional[str] = '.'):
        self.debug = debug

        self.logger = RootLogger.getLogger(self.__class__.__name__, debug)

        self.DPI = 300
        self.IMAGE_FORMAT = 'png256'  # e.g., 'png256', 'png16m', 'pngalpha', 'jpeg', etc.
        self.POINTS_PER_INCH = 72
        self.pixel_to_point_scale = 1.0 * self.POINTS_PER_INCH / self.DPI

        self.temp_base = self.setup_temp_directories(temp_dir)

        if self.debug:
            self.logger.debug(f"pixel_to_point_scale = {self.pixel_to_point_scale}")

        self.font_name = 'STSong-Light'
        pdfmetrics.registerFont(UnicodeCIDFont(self.font_name))

        # suppress paddle ocr's log, which defaults to debug
        self.set_paddleocr_log_level()

    def set_paddleocr_log_level(self):
        from paddleocr.ppocr.utils.logging import get_logger
        get_logger().setLevel(40)  # logging.ERROR


    def setup_temp_directories(self, temp_dir: str) -> str:
        """Create directories for intermediate files"""
        if temp_dir:
            base_dir = Path(temp_dir)
        else:
            base_dir = Path(tempfile.mkdtemp())
            
        # Create subdirectories for different stages
        self.img_dir = base_dir / "images"
        self.ocr_dir = base_dir / "ocr_pdfs"
        self.img_dir.mkdir(parents=True, exist_ok=True)
        self.ocr_dir.mkdir(parents=True, exist_ok=True)
        
        if self.debug:
            self.logger.debug(f"Temp Dir for Images: {self.img_dir}")
            self.logger.debug(f"Temp Dir for OCR PDFs: {self.ocr_dir}")
        
        return base_dir
    
    def convert_coordinates(self, bbox: List[Tuple], page_height_pts: Tuple) -> List[Tuple]:
        """
           Convert coordinates from OCR pixel space to PDF point space.
           bbox example: [[413.0, 380.0], [871.0, 380.0], [871.0, 442.0], [413.0, 442.0]]
        """
        converted_bbox = []
        for coord in bbox:
            x, y = coord
            x_pts = x * self.pixel_to_point_scale
            y_pts = y * self.pixel_to_point_scale
            y_pts = page_height_pts - y_pts
            converted_bbox.append([round(x_pts, 1), round(y_pts, 1)])
        return converted_bbox

    def create_text_layer(self, ocr_results: List[List[Tuple]], page_dims: Tuple[float, float]) -> PdfReader:
        """ Create a single-page PDF with OCR text layer. """

        width_pts, height_pts = page_dims
        
        packet = io.BytesIO()  # create canvas in memory to avoid saving to file.
        c = canvas.Canvas(packet, pagesize=(width_pts, height_pts))

        c.setPageSize((width_pts, height_pts))
        c.setFillColor(Color(0, 0, 0, alpha=0))
        
        for result in ocr_results:
            # ocr_results is list of pages, each page is a list of lines. 
            # Each line is list [bbox, (text, confidence)], e.g.,
            # [[[413.0, 380.0], [871.0, 380.0], [871.0, 442.0], [413.0, 442.0]], ('(19)国家知识产权局', 0.9951820373535156)]
            if not result:
                break

            if self.debug:
                self.logger.debug(f"ocr_result = {result}")

            bbox = result[0]
            text, confidence = result[1]

            if self.debug:
                self.logger.debug(f"Text: '{text}'")
                self.logger.debug(f"Confidence: {confidence}")
                self.logger.debug(f"Original bbox: {bbox}")

            pdf_bbox = self.convert_coordinates(bbox, height_pts)
            
            if self.debug:
                self.logger.debug(f"Converted bbox: {pdf_bbox}")
            
            # Calculate text position and dimensions
            x1, y1 = pdf_bbox[0]
            x2, y2 = pdf_bbox[1]
            x3, y3 = pdf_bbox[2]
            x4, y4 = pdf_bbox[3]
            
            text_width = round(max(abs(x2 - x1), abs(x3 - x4)), 1)
            text_height = round(max(abs(y3 - y1), abs(y4 - y2)), 1)

            center_x = (x1 + x2 + x3 + x4) / 4
            center_y = (y1 + y2 + y3 + y4) / 4

            lower_left_x = center_x - (text_width / 2)
            lower_left_y = center_y - (text_height / 2)

            if self.debug:
                c.rect(lower_left_x, lower_left_y, text_width, text_height, stroke=1, fill=0)
            
            # in PDF, font size is measured by points.
            # Here to get average points of the text covered on x and y axis.
            font_size = round((text_height + (text_width/len(text)))  * 0.45, 1)

            if self.debug:
                self.logger.debug(f"font: {font_size}, w: {text_width}, h: {text_height}, words: {len(text)}")

            c.setFont(self.font_name, font_size)
            c.drawString(
                lower_left_x,  # center_x - (text_width / 2),
                lower_left_y+3,  # center_y - (text_height / 2),
                text
            )
        
        c.save()

        packet.seek(0)
        return PdfReader(packet)
    
    def overlay_text_layer(self, input_pdf: str, text_layer: PdfReader, page_num: int) -> str:
        """ put the text layer onto the original page. """
        # Create a PdfReader object for the original PDF
        pdf_writer = PdfWriter()
        raw_reader = PdfReader(input_pdf)
            
        # Create a new page with the overlay
        page = raw_reader.pages[page_num-1]
        page.merge_page(text_layer.pages[0])
        pdf_writer.add_page(page)

        page_pdf_path = f"{self.ocr_dir}/page_{page_num}.pdf"

        # Write out the modified PDF
        with open(page_pdf_path, 'wb') as output_file:
            pdf_writer.write(output_file)

        self.logger.info(f"Searchable PDF saved as '{page_pdf_path}'")

        return page_pdf_path

    def process_single_page(self, 
                            pdf_path: str,
                            page_num: int, 
                            ocr_engine: PaddleOCR) -> str:
        """ Process a single page and return path to the OCR PDF. """
        
        image_path = f"{self.img_dir}/page_{page_num}.png"

        PdfUtil.convert_page_to_image(pdf_path, page_num, image_path, self.IMAGE_FORMAT, self.DPI)

        self.logger.info(f"page image: {image_path}")

        if self.debug:
            with Image.open(image_path) as img:
                self.logger.debug(f"page dims: {img.size[0]} x {img.size[1]} pixels")
        
        # Run OCR
        ocr_results = ocr_engine.ocr(image_path)
  
        # Create OCR PDF
        page_dims = PdfUtil.get_page_dimension(pdf_path, page_num)

        self.logger.info(f"page dims: {page_dims[0]} x {page_dims[1]} points")
        
        text_layer_reader = self.create_text_layer(ocr_results[0], page_dims)

        page_pdf_path = self.overlay_text_layer(pdf_path, text_layer_reader, page_num)

        self.logger.info(f"page pdf: {page_pdf_path}")
        
        return page_pdf_path

    def process_pdf(self, input_pdf: str, output_pdf: str, language: str = 'ch'):
        """ Process PDF and create searchable version. """

        try:
            ocr_engine = PaddleOCR(lang=language)
            
            total_pages = PdfUtil.get_total_pages(input_pdf)
            
            ocr_pdf_paths = []
            for page_num in range(1, total_pages+1):
                self.logger.info(f"Processing page {page_num} ...")

                ocr_pdf_path = self.process_single_page(input_pdf, page_num, ocr_engine)
                
                ocr_pdf_paths.append(ocr_pdf_path)
            
            self.logger.info("Merging PDFs ...")

            PdfUtil.merge_pdfs(ocr_pdf_paths, output_pdf)

            self.logger.info(f"Saved merged PDF to: {output_pdf}")
            
            if not self.debug:
                shutil.rmtree(self.temp_base)
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            raise


def main():
    parser = argparse.ArgumentParser(description='Convert PDF to searchable PDF using Paddle OCR')
    parser.add_argument('-i', '--input_pdf', type=str, help='path to input PDF file')
    parser.add_argument('-o', '--output_pdf', type=str, help='path to output PDF file')
    parser.add_argument('-l', '--language', default='ch', help='OCR language (default: Chinese)')
    parser.add_argument('-t', '--temp_dir', type=str, help='Directory to store intermediate files (optional)')

    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    RootLogger.printInfo(f"input: {args.input_pdf}")
    RootLogger.printInfo(f"output: {args.output_pdf}")
    RootLogger.printInfo(f"language: {args.language}")
    RootLogger.printInfo(f"temp_dir: {args.temp_dir}")
    RootLogger.printInfo(f"debug: {args.debug}")

    t1 = time.time()
    
    processor = PdfOCRer(debug=args.debug, temp_dir=args.temp_dir)

    processor.process_pdf(args.input_pdf, args.output_pdf, args.language)

    t2 = time.time()

    RootLogger.printInfo(f"time: {(t2-t1):.1f} seconds.")

if __name__ == "__main__":
    main()

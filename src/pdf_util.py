import logging, subprocess

import PIL, PyPDF2

from typing import List, Tuple, Optional

# Configure the root logger
# Reset logging as Python somehow seems to remember recently used format (?).
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'  # Format for asctime
)

class RootLogger:
    @staticmethod
    def printInfo(message: str):
        logging.info(message)
    
    @staticmethod
    def getLogger(logger_name, debug: False) -> logging.Logger:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG if debug else logging.INFO)
        return logger
    
class PdfUtil:
    @staticmethod
    def get_total_pages(pdf_path: str) -> int:
        with open(pdf_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            return len(pdf.pages)
    
    @staticmethod
    def get_page_dimension(pdf_path: str, page_num: int) -> Tuple[float]:
        """ Get number of pages and dimensions. """

        width_pts = 0
        height_pts = 0
        with open(pdf_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            the_page = pdf.pages[page_num-1]
            width_pts = float(the_page.mediabox.width)
            height_pts = float(the_page.mediabox.height)

        return width_pts, height_pts

    @staticmethod
    def convert_page_to_image(pdf_path: str, page_num: int, image_path: str, image_format: str, dpi: int) -> bool:
        """ Use Ghostscript to convert a specific PDF page to an image. """
        
        gs_command = [
            "gs",
            "-q",
            #"-dSAFER",
            "-dNOPAUSE",
            "-dBATCH",
            f"-sDEVICE={image_format}", # 'pngalpha'
            f"-sOutputFile={image_path}",
            f"-r{dpi}",  # resolution
            f"-dFirstPage={page_num}",
            f"-dLastPage={page_num}",
            pdf_path
        ]

        try:
            subprocess.run(gs_command, check=True)
        except Exception as e:
            logging.error(f"Error converting PDF page to image: {str(e)}")
            raise

        return True

    # not in use for now
    @staticmethod
    def convert_pdf_to_images(pdf_path: str, image_dir: str, image_format: str, dpi: int) -> List[str]:
        """ Convert all pages in the PDF file to images using Ghostscript. """
        image_paths = []
            
        # Ghostscript command
        gs_cmd = [
            'gs',
            '-q',
            '-dSAFER',
            '-dBATCH',
            '-dNOPAUSE',
            f'-r{dpi}',
            '-sDEVICE={image_format}', # 'png16m'
            '-dTextAlphaBits=4',
            '-dGraphicsAlphaBits=4',
            f'-sOutputFile={image_dir}/page_%d.png',
            pdf_path
        ]

        num_pages = PdfUtil.get_total_pages(pdf_path)
        
        try:
            result = subprocess.run(gs_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Ghostscript error: {result.stderr}")
            
            # Collect image paths
            for i in range(1, num_pages + 1):
                image_path = image_dir / f"page_{i}.png"
                if image_path.exists():
                    image_paths.append(str(image_path))
                else:
                    logging.error(f"Missing image for page {i}")
            
        except Exception as e:
            logging.error(f"Error converting PDF to images: {str(e)}")
            raise
        
        return image_paths

    @staticmethod
    def merge_pdfs(pdf_paths: List[str], output_pdf: str) -> bool:
        """ Merge the list of pdfs and write to the output pdf """
        
        pdf_merger = PyPDF2.PdfWriter()
        
        for pdf in pdf_paths:
            with open(pdf, 'rb') as input_file:
                pdf_merger.append(input_file)
        
        # Write final PDF
        with open(output_pdf, 'wb') as output_file:
            pdf_merger.write(output_file)
        
        return True
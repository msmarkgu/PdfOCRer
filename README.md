# PdfOCRer

PdfOCRer is a python script that runs OCR on an input PDF (possibly unsearchable) to produce a searchable PDF.

It uses [Paddle OCR](https://paddlepaddle.github.io/PaddleOCR/latest/index.html) as the OCR engine. Compared to the famous OCR engine [Tesseract](https://github.com/tesseract-ocr/tesseract), Paddle OCR shows better results for Chinese language in my experiments. However, it cannot seem to generate searchable PDF from its OCR result, whereas Tesseract can. If that's what you need, PdfOCRer can help.

PdfOCRer processes a PDF in four steps:

- Step 1: convert each pdf page into an image (default format PNG).
- Step 2: run OCR on each image to recognize text and bounding boxes.
- Step 3: add text/bbox on image as hidden layer to make 1-page PDF.
- Step 4: merge all 1-page pdfs to output the result searchable pdf.

# Dependencies

The script is tested in Python 3.10. It should work as long as the dependencies work.

- Paddle OCR and PaddlePaddle: follow its instruction [here](https://paddlepaddle.github.io/PaddleOCR/latest/ppocr/quick_start.html).

- PyPDF2, Pillow, ReportLab: ``` pip install pillow PyPDF2 reportlab ```

- Ghostscript: used to convert pdf to images, called from the script as subprocess. 

    -- on Linux/Ubuntu: ``` apt-get install ghostscript ```, 

    -- on MacOS machine: ``` brew install ghostscript ```,

    -- on Windows machine: [download 32/64 bit exe](https://www.ghostscript.com/releases/gsdnld.html), run it to install.

# Installation

Simply run in command line:

```
pip install pdfocrer
```

It will install all dependencies but Ghostscript.

# How to use

To use the script in command line, run it like following:

```
python pdf_ocrer.py -i <input_pdf> -o <output_pdf> -l <language> -t <temp_dir> [--debug]
```

Example:

```
python pdf_ocrer.py -i ../example/scanned_page.pdf -o ../example/scanned_page.ocr.pdf -t ../temp -l ch --debug
```

To use it in python code, do something like:

```
import os, sys

from pdfocrer.pdf_ocrer import PdfOCRer

input = './example/scanned_page.pdf'
output = './example/scanned_page.ocr.pdf'
isDebug = True
tempDir = './temp'
language = 'ch'  # or 'en', 'korean', 'japan', 'latin', 'arabic',  etc.

pp = PdfOCRer(isDebug, tempDir)

pp.process_pdf(input, output, language)

```

# Acknowledgement

Thanks to the authors of all the depencenies libraries, the Python and Open Source Community.

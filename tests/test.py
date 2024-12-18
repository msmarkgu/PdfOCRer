
import os, sys

from pdfocrer.pdf_ocrer import PdfOCRer

input = './example/scanned_page.pdf'
output = './example/scanned_page.ocr.pdf'
isDebug = True
tempDir = './temp'
language = 'ch'

pp = PdfOCRer(isDebug, tempDir)

pp.process_pdf(input, output, language)

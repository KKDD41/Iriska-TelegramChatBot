import io
import json
from urllib.request import Request, urlopen
from PyPDF2 import PdfFileReader


def text_from_pdf_url(url: str, pages=None):
    if pages is None:
        pages = []
    remote_file = urlopen(Request(url)).read()
    memory_file = io.BytesIO(remote_file)
    pdf_file = PdfFileReader(memory_file)

    result_str = ""
    pages.sort()
    for num in pages:
        result_str += pdf_file.getPage(num).extractText()
        result_str += "\n"
    return result_str


book = text_from_pdf_url("https://library.iliauni.edu.ge/wp-content/uploads/2017/04/Starshenbaum-G.V.-Addiktologiya"
                 ".-Psihologiya-i-psihoterapiya-zavisimostej-Kogito-TSentr-2006-368s.pdf", [44, 45])

print(book)

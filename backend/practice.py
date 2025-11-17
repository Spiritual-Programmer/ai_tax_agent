import pymupdf4llm


markdown = pymupdf4llm.to_markdown("./backend/w2.pdf")
print(markdown)
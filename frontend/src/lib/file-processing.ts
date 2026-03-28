import * as pdfjsLib from 'pdfjs-dist'
import mammoth from 'mammoth'

// Set worker source for PDF.js to the static file copied by vite-plugin-static-copy
pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs'

export async function extractTextFromFile(file: File): Promise<string> {
  const extension = file.name.split('.').pop()?.toLowerCase()

  if (extension === 'pdf') {
    return extractPdfText(file)
  } else if (extension === 'docx') {
    return extractDocxText(file)
  } else if (extension === 'txt' || extension === 'md') {
    return await file.text()
  } else {
    throw new Error('Unsupported file format. Please use PDF, DOCX, TXT, or MD.')
  }
}

async function extractPdfText(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer()
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise

  let fullText = ''

  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i)
    const textContent = await page.getTextContent()
    const pageText = textContent.items
      .map((item) => {
        const maybeStr = (item as { str?: unknown }).str
        return typeof maybeStr === 'string' ? maybeStr : ''
      })
      .filter(Boolean)
      .join(' ')

    fullText += pageText + '\n\n'
  }

  return fullText.trim()
}

async function extractDocxText(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer()
  const result = await mammoth.extractRawText({ arrayBuffer })
  return result.value.trim()
}

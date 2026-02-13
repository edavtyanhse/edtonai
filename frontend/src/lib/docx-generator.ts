
import {
    Document,
    Packer,
    Paragraph,
    TextRun,
    BorderStyle,
    AlignmentType,
    TabStopType,
    TabStopPosition,
} from 'docx'
import { saveAs } from 'file-saver'
import type { ParsedResume } from '@/api'

const FONT_FAMILY = 'Times New Roman'
const FONT_SIZE_TEXT = 22 // 11pt (docx uses half-points)
const FONT_SIZE_NAME = 32 // 16pt
const MARGINS = {
    top: 720, // 0.5 inch (1440 twips = 1 inch)
    bottom: 720,
    left: 720,
    right: 720,
}

export const generateHarvardDocx = async (data: ParsedResume) => {
    const { personal_info, work_experience, education, skills, summary, languages } = data

    const sections = []

    // 1. Header (Name, Contact)
    const contactParts = []
    if (personal_info?.location) contactParts.push(personal_info.location)
    if (personal_info?.contacts?.phone) contactParts.push(personal_info.contacts.phone)
    if (personal_info?.contacts?.email) contactParts.push(personal_info.contacts.email)
    // Limited links for simplicity in one line
    if (personal_info?.contacts?.links?.[0]) contactParts.push(personal_info.contacts.links[0])

    sections.push(
        new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
                new TextRun({
                    text: (personal_info?.name || 'NAME SURNAME').toUpperCase(),
                    bold: true,
                    font: FONT_FAMILY,
                    size: FONT_SIZE_NAME,
                }),
            ],
            spacing: { after: 100 },
        }),
        new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
                new TextRun({
                    text: contactParts.join(' | '),
                    font: FONT_FAMILY,
                    size: FONT_SIZE_TEXT - 2, // Slightly smaller for contact
                }),
            ],
            spacing: { after: 300 },
        })
    )

    // Helper for Section Title
    const createSectionTitle = (title: string) => {
        return new Paragraph({
            children: [
                new TextRun({
                    text: title.toUpperCase(),
                    bold: true,
                    font: FONT_FAMILY,
                    size: FONT_SIZE_TEXT,
                }),
            ],
            border: {
                bottom: {
                    color: '000000',
                    space: 1,
                    style: BorderStyle.SINGLE,
                    size: 6,
                },
            },
            spacing: { before: 200, after: 100 },
        })
    }

    // Helper for Experience Item
    const createExperienceItem = (
        company: string,
        title: string,
        startDate: string,
        endDate: string,
        location?: string,
        details?: string[]
    ) => {
        const lines = []

        // Line 1: Company (Left) + Date (Right)
        lines.push(
            new Paragraph({
                tabStops: [
                    {
                        type: TabStopType.RIGHT,
                        position: TabStopPosition.MAX, // Aligns to right margin
                    },
                ],
                children: [
                    new TextRun({
                        text: company,
                        bold: true,
                        font: FONT_FAMILY,
                        size: FONT_SIZE_TEXT,
                    }),
                    new TextRun({
                        children: [`\t${startDate || ''}${endDate ? ' – ' + endDate : ''}`],
                        font: FONT_FAMILY,
                        size: FONT_SIZE_TEXT,
                    }),
                ],
            })
        )

        // Line 2: Title (Left, Italic) + Location (Right)
        lines.push(
            new Paragraph({
                tabStops: [
                    {
                        type: TabStopType.RIGHT,
                        position: TabStopPosition.MAX,
                    },
                ],
                children: [
                    new TextRun({
                        text: title,
                        italics: true,
                        bold: true, // Harvard style often bolds title too or just italics
                        font: FONT_FAMILY,
                        size: FONT_SIZE_TEXT,
                    }),
                    new TextRun({
                        children: [`\t${location || ''}`],
                        font: FONT_FAMILY,
                        size: FONT_SIZE_TEXT,
                        italics: false,
                    }),
                ],
                spacing: { after: 50 },
            })
        )

        // Bullets
        if (details) {
            details.forEach((detail) => {
                lines.push(
                    new Paragraph({
                        children: [
                            new TextRun({
                                text: detail,
                                font: FONT_FAMILY,
                                size: FONT_SIZE_TEXT,
                            }),
                        ],
                        bullet: { level: 0 }, // Standard bullet
                    })
                )
            })
        }

        // Spacing after item
        lines.push(new Paragraph({ children: [], spacing: { after: 100 } }))

        return lines
    }

    // Helper for Education Item
    const createEducationItem = (
        institution: string,
        degree: string,
        field: string | undefined,
        start: string | undefined,
        end: string | undefined
    ) => {
        const lines = []

        // Line 1: Institution (Left) + Date (Right)
        lines.push(
            new Paragraph({
                tabStops: [
                    {
                        type: TabStopType.RIGHT,
                        position: TabStopPosition.MAX,
                    },
                ],
                children: [
                    new TextRun({
                        text: institution,
                        bold: true,
                        font: FONT_FAMILY,
                        size: FONT_SIZE_TEXT,
                    }),
                    new TextRun({
                        children: [`\t${end || ''}`], // Education usually shows Grad year
                        font: FONT_FAMILY,
                        size: FONT_SIZE_TEXT,
                    }),
                ],
            })
        )

        // Line 2: Degree
        lines.push(
            new Paragraph({
                children: [
                    new TextRun({
                        text: `${degree}${field ? ' in ' + field : ''}`,
                        italics: true,
                        font: FONT_FAMILY,
                        size: FONT_SIZE_TEXT,
                    }),
                ],
                spacing: { after: 100 }
            })
        )

        return lines
    }

    // 2. Summary
    if (summary) {
        // Harvard template usually skips summary, but if we have it:
        // Maybe verify if it fits? Or just add it.
        // Let's add it if present, but cleanly.
        sections.push(new Paragraph({ children: [new TextRun({ text: summary, font: FONT_FAMILY, size: FONT_SIZE_TEXT })], spacing: { after: 200 } }))
    }

    // 3. Education (Harvard puts Education first often for fresh grads, but we stick to typical order or data order)
    if (education && education.length > 0) {
        sections.push(createSectionTitle('Education'))
        education.forEach(edu => {
            sections.push(...createEducationItem(edu.institution, edu.degree || '', edu.field_of_study, edu.start_date, edu.end_date))
        })
    }

    // 4. Experience
    if (work_experience && work_experience.length > 0) {
        sections.push(createSectionTitle('Experience'))
        work_experience.forEach(exp => {
            const responsibilities = [...(exp.responsibilities || []), ...(exp.achievements || [])]
            sections.push(...createExperienceItem(exp.company, exp.title, exp.start_date || '', exp.end_date || '', exp.location, responsibilities))
        })
    }

    // 5. Skills
    if ((skills && skills.length > 0) || (languages && languages.length > 0)) {
        sections.push(createSectionTitle('Skills & Languages'))

        if (languages && languages.length > 0) {
            sections.push(new Paragraph({
                children: [
                    new TextRun({ text: 'Languages: ', bold: true, font: FONT_FAMILY, size: FONT_SIZE_TEXT }),
                    new TextRun({ text: languages.map(l => `${l.language} (${l.proficiency || ''})`).join(', '), font: FONT_FAMILY, size: FONT_SIZE_TEXT })
                ]
            }))
        }

        if (skills && skills.length > 0) {
            sections.push(new Paragraph({
                children: [
                    new TextRun({ text: 'Technical Skills: ', bold: true, font: FONT_FAMILY, size: FONT_SIZE_TEXT }),
                    new TextRun({ text: skills.map(s => s.name).join(', '), font: FONT_FAMILY, size: FONT_SIZE_TEXT })
                ]
            }))
        }
    }

    const doc = new Document({
        sections: [
            {
                properties: {
                    page: {
                        margin: MARGINS,
                    },
                },
                children: sections,
            },
        ],
    })

    Packer.toBlob(doc).then((blob) => {
        saveAs(blob, `Resume_${personal_info?.name?.replace(/\s+/g, '_') || 'Result'}.docx`)
    })
}

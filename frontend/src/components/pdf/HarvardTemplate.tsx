
import { Document, Page, Text, View, StyleSheet, Font } from '@react-pdf/renderer'
import type { ParsedResume } from '@/api'

// Register fonts for Cyrillic support
// Using Roboto as a safe, clean sans-serif/serif alternative that supports Cyrillic
Font.register({
    family: 'Roboto',
    fonts: [
        { src: 'https://cdnjs.cloudflare.com/ajax/libs/ink/3.1.10/fonts/Roboto/roboto-regular-webfont.ttf' },
        { src: 'https://cdnjs.cloudflare.com/ajax/libs/ink/3.1.10/fonts/Roboto/roboto-bold-webfont.ttf', fontWeight: 'bold' },
        { src: 'https://cdnjs.cloudflare.com/ajax/libs/ink/3.1.10/fonts/Roboto/roboto-italic-webfont.ttf', fontStyle: 'italic' },
    ],
})

const styles = StyleSheet.create({
    page: {
        padding: 30, // Approx 0.5 inch margins (Harvard standard is 0.5-1.0)
        fontFamily: 'Roboto',
        fontSize: 10,
        lineHeight: 1.4,
    },
    header: {
        marginBottom: 5,
        textAlign: 'center',
    },
    name: {
        fontSize: 16, // 14-16pt
        fontWeight: 'bold',
        textTransform: 'uppercase',
        marginBottom: 4,
    },
    contactInfo: {
        fontSize: 9,
        flexDirection: 'row',
        justifyContent: 'center',
        gap: 5,
        marginBottom: 10,
    },
    sectionTitle: {
        fontSize: 11,
        fontWeight: 'bold',
        textTransform: 'uppercase',
        borderBottomWidth: 1,
        borderBottomColor: '#000',
        marginBottom: 5,
        marginTop: 10,
        paddingBottom: 2,
    },
    itemContainer: {
        marginBottom: 5,
    },
    itemHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 1,
    },
    companyName: {
        fontWeight: 'bold',
    },
    location: {
        // fontStyle: 'italic', // Optional
    },
    positionHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 2,
    },
    positionTitle: {
        fontWeight: 'bold',
        fontStyle: 'italic',
    },
    dates: {
        // Regular font
    },
    bulletPoint: {
        flexDirection: 'row',
        marginBottom: 1,
        paddingLeft: 10,
    },
    bulletChar: {
        width: 10,
        fontSize: 10,
    },
    bulletContent: {
        flex: 1,
    },
    skillsContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
    },
    skillLine: {
        marginBottom: 2,
    },
    skillCategory: {
        fontWeight: 'bold',
    },
})

interface Props {
    data: ParsedResume
}

export default function HarvardTemplate({ data }: Props) {
    const { personal_info, work_experience, education, skills, summary, languages } = data

    return (
        <Document>
            <Page size="A4" style={styles.page}>
                {/* Header */}
                <View style={styles.header}>
                    <Text style={styles.name}>{personal_info?.name || 'NAME SURNAME'}</Text>
                    <View style={styles.contactInfo}>
                        {personal_info?.location && <Text>{personal_info.location} |</Text>}
                        {personal_info?.contacts?.phone && <Text>{personal_info.contacts.phone} |</Text>}
                        {personal_info?.contacts?.email && <Text>{personal_info.contacts.email} |</Text>}
                        {personal_info?.contacts?.links?.[0] && <Text>{personal_info.contacts.links[0]}</Text>}
                    </View>
                </View>

                {/* Summary (Optional for Harvard, but good to have) */}
                {summary && (
                    <View style={{ marginBottom: 10 }}>
                        <Text>{summary}</Text>
                    </View>
                )}

                {/* Education */}
                {education && education.length > 0 && (
                    <View>
                        <Text style={styles.sectionTitle}>Education</Text>
                        {education.map((edu, i) => (
                            <View key={i} style={styles.itemContainer}>
                                <View style={styles.itemHeader}>
                                    <Text style={styles.companyName}>{edu.institution}</Text>
                                    <Text style={styles.dates}>
                                        {edu.start_date && edu.end_date ? `${edu.start_date} – ${edu.end_date}` : edu.end_date || ''}
                                    </Text>
                                </View>
                                <View style={styles.positionHeader}>
                                    <Text style={styles.positionTitle}>{edu.degree} {edu.field_of_study && `in ${edu.field_of_study}`}</Text>
                                    {/* Location if available */}
                                </View>
                            </View>
                        ))}
                    </View>
                )}

                {/* Experience */}
                {work_experience && work_experience.length > 0 && (
                    <View>
                        <Text style={styles.sectionTitle}>Experience</Text>
                        {work_experience.map((exp, i) => (
                            <View key={i} style={styles.itemContainer}>
                                <View style={styles.itemHeader}>
                                    <Text style={styles.companyName}>{exp.company}</Text>
                                    <Text style={styles.dates}>
                                        {exp.start_date && exp.end_date ? `${exp.start_date} – ${exp.end_date}` : exp.start_date || ''}
                                    </Text>
                                </View>
                                <View style={styles.positionHeader}>
                                    <Text style={styles.positionTitle}>{exp.title}</Text>
                                    <Text style={styles.location}>{exp.location || ''}</Text>
                                </View>
                                {/* Responsibilities / Bullets */}
                                {exp.responsibilities && exp.responsibilities.map((resp, j) => (
                                    <View key={j} style={styles.bulletPoint}>
                                        <Text style={styles.bulletChar}>•</Text>
                                        <Text style={styles.bulletContent}>{resp}</Text>
                                    </View>
                                ))}
                                {exp.achievements && exp.achievements.map((ach, j) => (
                                    <View key={`ach-${j}`} style={styles.bulletPoint}>
                                        <Text style={styles.bulletChar}>•</Text>
                                        <Text style={styles.bulletContent}>{ach}</Text>
                                    </View>
                                ))}
                            </View>
                        ))}
                    </View>
                )}

                {/* Skills */}
                {(skills && skills.length > 0) || (languages && languages.length > 0) ? (
                    <View>
                        <Text style={styles.sectionTitle}>Skills & Languages</Text>
                        {languages && languages.length > 0 && (
                            <View style={styles.skillLine}>
                                <Text>
                                    <Text style={styles.skillCategory}>Languages: </Text>
                                    {languages.map(l => {
                                        if (typeof l === 'string') return l;
                                        return `${l.language} (${l.proficiency || ''})`
                                    }).join(', ')}
                                </Text>
                            </View>
                        )}

                        {/* Group skills by category if possible, or just list them */}
                        <View style={styles.skillLine}>
                            <Text>
                                <Text style={styles.skillCategory}>Technical Skills: </Text>
                                {skills?.map(s => s.name).join(', ')}
                            </Text>
                        </View>
                    </View>
                ) : null}

            </Page>
        </Document>
    )
}

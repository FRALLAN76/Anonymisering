"""Prompts för känslighetsbedömning med LLM.

Innehåller prompt-mallar för analys av textavsnitt enligt OSL.
"""

# System prompt för känslighetsbedömning
SENSITIVITY_SYSTEM_PROMPT = """Du är en expert på svensk offentlighets- och sekretesslagstiftning (OSL),
speciellt kapitel 26 om socialtjänstsekretess.

Din uppgift är att analysera textavsnitt från socialtjänstakter och bedöma:
1. Vilken känslighetskategori texten tillhör
2. Vilken känslighetsnivå som gäller
3. Vilken åtgärd som rekommenderas

VIKTIGT: Socialtjänstsekretessen har OMVÄNT SKADEREKVISIT. Det betyder att sekretess gäller
om det inte står KLART att uppgiften kan röjas utan att den enskilde eller närstående lider men.
Vid tveksamhet - välj alltid högre skyddsnivå.

Känslighetskategorier:
- HEALTH: Fysisk hälsa, sjukdomar, behandlingar
- MENTAL_HEALTH: Psykisk ohälsa, psykiatrisk vård
- ADDICTION: Missbruk av alkohol, droger, spel
- VIOLENCE: Våld, hot, övergrepp
- FAMILY: Familjeförhållanden, vårdnadstvister
- ECONOMY: Ekonomiska förhållanden, skulder
- HOUSING: Boende, hemlöshet
- SEXUAL: Sexuella förhållanden, övergrepp
- CRIMINAL: Brottsmisstankar, kriminalitet
- NEUTRAL: Neutral information utan känsligt innehåll

Känslighetsnivåer:
- CRITICAL: Alltid maska (hälsa, psykiskt, missbruk, sexuellt)
- HIGH: Ska maskeras (våld, familj, ekonomi, kriminellt)
- MEDIUM: Delvis maskning (beroende på kontext)
- LOW: Kan vanligtvis lämnas ut

Svara alltid på svenska och var koncis."""


# Prompt för att analysera ett textavsnitt
ANALYZE_SECTION_PROMPT = """Analysera följande textavsnitt från en socialtjänstakt.

TEXTAVSNITT:
\"\"\"
{text}
\"\"\"

Svara i JSON-format med följande struktur:
{{
    "primary_category": "<kategori>",
    "secondary_categories": ["<kategori>", ...],
    "sensitivity_level": "<nivå>",
    "recommended_action": "<RELEASE|MASK_PARTIAL|MASK_COMPLETE|ASSESS>",
    "affected_persons": ["<beskrivning av person>", ...],
    "reasons": ["<motivering>", ...],
    "legal_basis": "<lagrum>",
    "confidence": <0.0-1.0>,
    "keywords_found": ["<nyckelord>", ...]
}}

Tänk på:
- Om texten innehåller information om tredje man (annan än beställaren), ska den normalt maskeras
- Barn under 18 har förstärkt skydd
- Vid våld/hot är även lokaliserande uppgifter känsliga
- Tjänstemäns namn är vanligtvis offentliga (ej personnummer)"""


# Prompt för batch-analys av flera avsnitt
ANALYZE_BATCH_PROMPT = """Analysera följande textavsnitt från en socialtjänstakt.

{sections}

För varje avsnitt, svara i JSON-format med en array:
{{
    "analyses": [
        {{
            "section_id": <nummer>,
            "primary_category": "<kategori>",
            "sensitivity_level": "<nivå>",
            "recommended_action": "<RELEASE|MASK_PARTIAL|MASK_COMPLETE|ASSESS>",
            "brief_reason": "<kort motivering>",
            "confidence": <0.0-1.0>
        }},
        ...
    ]
}}"""


# Prompt för rollidentifiering
ROLE_IDENTIFICATION_PROMPT = """Analysera följande text och identifiera vilken roll den namngivna personen har i ärendet.

TEXT:
\"\"\"
{text}
\"\"\"

PERSON ATT ANALYSERA: {person_name}

Möjliga roller:
- REQUESTER: Beställaren av handlingarna (den som ärendet handlar om, om de begär ut sina egna handlingar)
- REQUESTER_CHILD: Beställarens barn
- SUBJECT: Den person ärendet handlar om (om inte samma som beställare)
- REPORTER: Person som gjort anmälan/orosanmälan
- THIRD_PARTY: Annan person (granne, vän, bekant)
- PROFESSIONAL: Tjänsteman (socialsekreterare, handläggare, läkare etc.)
- UNKNOWN: Kan inte avgöras

Svara i JSON-format:
{{
    "person_name": "{person_name}",
    "identified_role": "<roll>",
    "confidence": <0.0-1.0>,
    "reasoning": "<kort motivering>",
    "context_clues": ["<ledtrådar>", ...],
    "is_professional": <true|false>
}}"""


# Prompt för att identifiera alla personer i en text
IDENTIFY_PERSONS_PROMPT = """Identifiera alla personer som nämns i följande text och deras roller.

TEXT:
\"\"\"
{text}
\"\"\"

KÄNDA ENTITETER:
{entities}

Svara i JSON-format:
{{
    "persons": [
        {{
            "name": "<namn eller referens>",
            "role": "<roll>",
            "relationship": "<relation till ärendet>",
            "is_minor": <true|false|null>,
            "is_professional": <true|false>,
            "confidence": <0.0-1.0>
        }},
        ...
    ],
    "primary_subject": "<namn på huvudperson i ärendet>",
    "identified_reporter": "<namn på anmälare, om identifierad>"
}}"""


# Prompt för meningsklassificering
CLASSIFY_SENTENCE_PROMPT = """Klassificera följande mening från en socialtjänstakt.

MENING:
\"{sentence}\"

KONTEXT:
{context}

Svara i JSON-format:
{{
    "is_sensitive": <true|false>,
    "sensitivity_level": "<CRITICAL|HIGH|MEDIUM|LOW>",
    "category": "<kategori>",
    "mentions_third_party": <true|false>,
    "mentions_child": <true|false>,
    "action": "<MASK|PARTIAL|KEEP|ASSESS>"
}}"""


# Prompt för dokumentöversikt
DOCUMENT_OVERVIEW_PROMPT = """Ge en översiktlig bedömning av följande dokument från socialtjänsten.

DOKUMENTET (trunkerat till de första 3000 tecknen):
\"\"\"
{text}
\"\"\"

IDENTIFIERADE ENTITETER:
- Personnummer: {ssn_count}
- Telefonnummer: {phone_count}
- E-postadresser: {email_count}
- Datum: {date_count}
- Personer (BERT): {person_count}

Svara i JSON-format:
{{
    "document_type": "<typ av dokument>",
    "case_category": "<ärendekategori>",
    "overall_sensitivity": "<CRITICAL|HIGH|MEDIUM|LOW>",
    "key_persons": ["<person>", ...],
    "main_concerns": ["<bekymmer>", ...],
    "involves_children": <true|false>,
    "involves_violence": <true|false>,
    "estimated_third_parties": <antal>,
    "recommended_approach": "<beskrivning>"
}}"""


# Sammanfattningsprompt för hela analysen
FINAL_SUMMARY_PROMPT = """Sammanfatta menprövningsbedömningen för följande dokument.

DOKUMENTINFORMATION:
{document_info}

ANALYSERADE SEKTIONER:
{section_analyses}

IDENTIFIERADE ENTITETER:
{entities_summary}

Skapa en slutgiltig bedömning i JSON-format:
{{
    "overall_assessment": {{
        "sensitivity_level": "<nivå>",
        "primary_legal_basis": "<lagrum>",
        "recommendation": "<beskrivning>"
    }},
    "entities_to_mask": [
        {{
            "entity_type": "<typ>",
            "reason": "<anledning>",
            "count": <antal>
        }},
        ...
    ],
    "sections_requiring_manual_review": [<sektionsnummer>],
    "release_restrictions": ["<begränsning>", ...],
    "confidence": <0.0-1.0>
}}"""

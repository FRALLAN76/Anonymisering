# Plan för AI-stött Menprövningsverktyg
**Datum:** 2025-11-25
**Version:** 1.0
**Status:** Planering

---

## Sammanfattning

Detta dokument beskriver en komplett plan för att utveckla ett AI-stött verktyg för menprövning av sociala handlingar enligt Offentlighets- och Sekretesslagen (OSL) kapitel 26.

### Nyckeltal
- **Tidsplan:** 7 månader från start till produktion
- **Kostnad:** ~2,75 miljoner kr (första året)
- **Förväntad tidsbesparing:** 50% reduktion av tid för menprövning
- **AI-precision:** Mål 95% korrekthet i rekommendationer

### Teknisk Lösning
Hybrid-arkitektur som kombinerar:
- **KBLab Swedish BERT NER** (befintlig) - Snabb entitetsigenkänning
- **GPT-OSS 120B** (on-prem) - Djup kontextuell analys och juridiskt resonemang
- **Integration** med befintligt anonymiseringsverktyg

---

## 1. BAKGRUND OCH SYFTE

### 1.1 Menprövningsprocessen
När en begäran om utlämnande av sociala handlingar inkommer ska en menprövning genomföras enligt OSL. Processen innebär:

1. **Omvänt skaderekvisit** - Sekretess är huvudregel, inte undantag
2. **Individuell bedömning** - Varje fall måste granskas separat
3. **Riskbedömning** - Bedöma risk för men, obehag, integritetsintrång
4. **Relationell analys** - Hur påverkas olika parter om information röjs
5. **Dokumentation** - Alla beslut måste motiveras juridiskt

### 1.2 Utmaningar idag
- Tidskrävande manuell genomgång av omfattande akter
- Subjektiva bedömningar kan variera mellan handläggare
- Svårt att identifiera alla känsliga detaljer i stora dokument
- Komplexa relationsanalyser mellan flera personer
- Krävande juridisk dokumentation

### 1.3 Målet med verktyget
Utveckla ett AI-stött verktyg som:
- Automatiskt identifierar känsliga uppgifter
- Föreslår vilka avsnitt som bör maskas
- Analyserar relationer och risker
- Genererar juridiska motiveringar
- Dokumenterar alla beslut för revision
- Minskar tid och ökar konsistens

---

## 2. TEKNISK ARKITEKTUR

### 2.1 Hybrid AI-modell

```
┌─────────────────────────────────────────────────┐
│         SNABB PIPELINE (BERT)                   │
│  ⚡ Låg latens (~100ms), strukturerad extraktion│
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────▼─────────┐
        │  1. Entitets-     │
        │     igenkänning   │
        │  - Personer       │
        │  - Telefonnummer  │
        │  - E-post         │
        │  - Adresser       │
        │  - Personnummer   │
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │  2. Bas-kategori- │
        │     klassificering│
        │  - HEALTH         │
        │  - VIOLENCE       │
        │  - ADDICTION      │
        │  - FAMILY         │
        └─────────┬─────────┘
                  │
                  │ Strukturerad data
                  ▼
┌─────────────────────────────────────────────────┐
│       DJUP ANALYS (GPT-OSS 120B)                │
│  🧠 Kontextuell förståelse (~10-30s)            │
└─────────────────────────────────────────────────┘
                  │
        ┌─────────▼─────────┐
        │  3. Kontextuell   │
        │     känslighets-  │
        │     analys        │
        │  - Sammanhang     │
        │  - Indirekta risker│
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │  4. Relations-    │
        │     analys        │
        │  - Persongrafer   │
        │  - Konflikter     │
        │  - Maktförhållanden│
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │  5. Juridisk      │
        │     resonemang    │
        │  - OSL-tillämpning│
        │  - Riskbedömning  │
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────┐
        │  6. Motivering    │
        │     generering    │
        │  - Lagstöd        │
        │  - Dokumentation  │
        └───────────────────┘
```

### 2.2 Systemkomponenter

```
┌────────────────────────────────────────────────┐
│         Användargränssnitt (Webb)              │
│  - Ärendehantering                             │
│  - Dokumentvisning med färgkodning             │
│  - Interaktiv maskning                         │
│  - Beslutsgränssnitt                           │
└─────────────────┬──────────────────────────────┘
                  │
┌─────────────────▼──────────────────────────────┐
│         Orchestration Layer                    │
│  - Bestämmer när BERT/LLM ska användas        │
│  - Parallellisering av anrop                   │
│  - Resultatcaching (Redis)                     │
│  - Arbetsflödeshantering                       │
└─────┬──────────────────┬────────────┬──────────┘
      │                  │            │
┌─────▼─────┐   ┌───────▼──────┐  ┌──▼─────────────┐
│  BERT NER │   │   GPT-OSS    │  │  Befintligt    │
│  Pipeline │   │   120B       │  │  Anonymiserings│
│           │   │   (on-prem)  │  │  verktyg       │
│ KBLab     │◄──┤              │  │                │
│ Swedish   │──►│ • Kontext    │  │ • Maskering    │
│ BERT      │   │ • Resonemang │  │ • Export       │
│           │   │ • Motivering │  │                │
│ 10-100ms  │   │ 5-30 sek     │  │                │
└───────────┘   └──────────────┘  └────────────────┘
      │                │                  │
┌─────▼────────────────▼──────────────────▼────────┐
│         Databas (PostgreSQL)                     │
│  - Ärenden och beslut                            │
│  - Dokument (original + maskade versioner)       │
│  - Relationsgrafer                               │
│  - Kunskapsbas (tidigare beslut, prejudikat)     │
│  - Användardata och behörigheter                 │
└──────────────────────────────────────────────────┘
```

### 2.3 Teknologistack

**Backend:**
- Python 3.11+
- FastAPI (REST API)
- PostgreSQL 15 (databas)
- Redis (cache och session)
- Celery (asynkrona uppgifter)

**AI/ML:**
- KBLab Swedish BERT NER (befintlig)
- GPT-OSS 120B (on-prem via vLLM eller text-generation-inference)
- spaCy för NLP-pipeline
- NetworkX för relationsgrafanalys
- Sentence-transformers för semantisk likhet

**Frontend:**
- React 18 / Next.js 14
- TypeScript
- TailwindCSS
- PDF.js för dokumentvisning
- D3.js / React-Flow för grafer

**Infrastruktur:**
- Docker + Docker Compose
- Kubernetes (produktion)
- GitLab CI/CD
- Prometheus + Grafana (monitoring)

---

## 3. FUNKTIONELLA KRAV

### 3.1 Automatisk Analys

**Entitetsigenkänning (BERT):**
- PERSON - Namn på personer
- TELEFON - Telefonnummer
- EPOST - E-postadresser
- ADRESS - Gatuadresser, postnummer
- PERSONNUMMER - Svenska personnummer
- ORGANISATION - Företag, myndigheter
- PLATS - Städer, områden

**Känslighetskategorisering (BERT + GPT-OSS):**
- HEALTH - Hälsouppgifter, sjukdomar
- MENTAL_HEALTH - Psykisk ohälsa
- ADDICTION - Missbruk (alkohol, droger)
- VIOLENCE - Våld, övergrepp, hot
- FAMILY - Familjekonflikter, relationer
- ECONOMY - Ekonomiska förhållanden, skulder
- HOUSING - Boendesituation, hemliv
- SEXUAL - Sexuell läggning, sexualitet
- CRIMINAL - Brottslighet, poliskontakter

### 3.2 Kontextuell Analys (GPT-OSS)

**Djupanalys av känsliga avsnitt:**
```python
För varje identifierat känsligt avsnitt, analysera:
1. Kontext - I vilket sammanhang förekommer uppgiften?
2. Påverkan - Hur kan uppgiften uppfattas av olika läsare?
3. Indirekta risker - Finns det dolda integritetshot?
4. Relationer - Vilka personer påverkas?
5. Stigmatisering - Risk för negativ social påverkan?
6. Maktdynamik - Kan info användas i maktutövande?
```

**Exempel:**
```
Text: "Agnes är mycket ensam i Göteborg och saknar släkt här"

BERT-klassificering: NEUTRAL (missar kontexten)

GPT-OSS-analys:
- Kategori: FAMILY + MENTAL_HEALTH
- Känslighet: MEDIUM-HIGH
- Resonemang: "I kombination med andra uppgifter om
  psykisk ohälsa och brist på stödnätverk kan denna
  uppgift bidra till en bild av sårbarhet. Kan påverka
  bedömningar om föräldraförmåga."
- Berör: Agnes Grenqvist (mormor)
- Rekommendation: Överväg maskning beroende på beställare
```

### 3.3 Relationskartläggning

**Automatisk byggnad av relationsgraf:**
```
Identifiera:
- Familjerelationer (mormor, morfar, barn, syskon)
- Professionella relationer (socialsekreterare, läkare)
- Konfliktrelationer (ex-partner, anmälare)
- Beroenderelationer (vårdnadshavare, ombud)

Analysera:
- Informationsflöden mellan personer
- Potentiella intressekonflikter
- Maktförhållanden
- Skyddsbehov
```

**Visualisering:**
```
     [Beställare: Maria]
           │
    ┌──────┴──────┐
    │ Konflikt    │
    ▼             ▼
[Agnes]────[Sveinung]
    │          │
    │ Vårdnad  │ Vårdnad
    ▼          ▼
[Adrian]   [Kenneth]

Risk: Uppgifter om Agnes kan användas
av Maria i familjekonflikt
```

### 3.4 Sekretessbedömning

**Tidsdimension:**
- Beräkna ålder på uppgifter
- Tillämpa 70-årsgräns
- Bedöm om sekretess försvagats över tid

**Personstatus:**
- Levande/avlidna
- Myndiga/omyndiga
- Särskilt skyddsbehov

**Insiktsbedömning (GPT-OSS):**
```python
Analysera:
1. Är beställaren omnämnd i händelser i akten?
2. Var beställaren närvarande vid dokumenterade händelser?
3. Har beställaren själv lämnat uppgiften till socialtjänsten?
4. Kan beställaren rimligen redan känna till uppgiften?

Om JA på flera punkter → Sekretessen kan vara försvagad
```

**Sekretessbrytande faktorer:**
- Samtycke från berörda personer
- Fullmakt att ta del av uppgifter
- Lagstöd (t.ex. annan myndighet)
- Förbehåll med särskilda villkor

### 3.5 Interaktivt Arbetsflöde

**Guidat process:**

```
1. REGISTRERA ÄRENDE
   - Beställarens uppgifter
   - Relation till ärendet
   - Syfte med begäran
   - Samtycken (om finns)

2. LADDA UPP HANDLING
   - PDF, Word, txt
   - Automatisk OCR vid behov

3. AUTOMATISK ANALYS (20-40 sek)
   - BERT: Entiteter + kategorier
   - GPT-OSS: Djupanalys
   - Relationsgraf byggs

4. GRANSKA RESULTAT
   - Färgkodad dokumentvy:
     🔴 Röd = Hög risk, föreslås maskning
     🟡 Gul = Osäker, kräver bedömning
     🟢 Grön = Låg risk, kan lämnas ut

5. JUSTERA OCH MOTIVERA
   - Godkänn/ändra AI-förslag
   - Lägg till egna motiveringar
   - Dokumentera avvikelser

6. GENERERA MASKAD VERSION
   - Automatisk maskning
   - PDF med [MASKERAD TEXT]
   - Versionering

7. BESLUT OCH UTLÄMNING
   - Formellt beslut
   - Juridisk dokumentation
   - Logga allt för revision
```

### 3.6 Beslutsstöd

**Kunskapsbas:**
- Tidigare liknande ärenden
- Rättsfall och prejudikat
- OSL-kommentarer
- Best practices

**Automatiska kontroller:**
```
☑ Har alla identifierade personer bedömts?
☑ Finns samtycke för känsliga uppgifter?
☑ Är barn särskilt skyddade?
☑ Är motivering tillräckligt detaljerad?
☑ Har sekretessbrytande faktorer beaktats?
☑ Är beslutet proportionerligt?
```

**Varningssystem:**
```
⚠️ VARNING: Beställaren är i konflikt med berörda
⚠️ VARNING: Högrisk-information identifierad
⚠️ VARNING: Barn under 18 år berörs
⚠️ VARNING: Våldsproblematik dokumenterad
```

---

## 4. GPT-OSS INTEGRATION

### 4.1 Användningsfall för GPT-OSS

#### Användningsfall 1: Kontextuell Känslighetsbedömning

**Prompt-template:**
```python
SYSTEM_PROMPT = """
Du är expert på menprövning enligt Offentlighets- och
Sekretesslagen (OSL) kapitel 26. Din uppgift är att analysera
textavsnitt från sociala akter och bedöma deras känslighet
i sitt sammanhang.

Beakta alltid:
- Omvänt skaderekvisit (sekretess är huvudregel)
- Risk för att person lider men
- Samhällelig kontext och värderingar
- Indirekta integritetshot
- Relationella risker
"""

USER_PROMPT = f"""
DOKUMENT-SAMMANHANG:
{document_context}

IDENTIFIERADE ENTITETER (från BERT):
{entities_json}

TEXTAVSNITT ATT BEDÖMA:
"{text_section}"

Analysera detta avsnitt och svara i följande JSON-format:
{{
  "sensitivity_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "primary_category": "HEALTH|VIOLENCE|ADDICTION|etc",
  "reasons": ["lista med konkreta skäl"],
  "affected_persons": ["lista över berörda personer"],
  "indirect_risks": ["indirekta risker om uppgiften röjs"],
  "context_notes": "förklaring av varför kontexten är viktig",
  "recommendation": "RELEASE|MASK_PARTIAL|MASK_COMPLETE",
  "confidence": 0.0-1.0
}}
"""
```

**Exempel-analys:**
```json
{
  "text": "Agnes har missbruksproblem och lever på ekonomiskt bistånd",
  "bert_category": "ADDICTION",
  "gpt_analysis": {
    "sensitivity_level": "HIGH",
    "primary_category": "ADDICTION",
    "secondary_categories": ["ECONOMY", "STIGMA"],
    "reasons": [
      "Känslig hälsouppgift enligt OSL 26:1",
      "Stigmatiserande information om tredje part",
      "Ekonomisk utsatthet ökar sårbarhet",
      "Kan påverka bedömning av föräldraförmåga"
    ],
    "affected_persons": ["Agnes Grenqvist"],
    "indirect_risks": [
      "Risk att information används i vårdnadstvist",
      "Kan påverka Agnes relation till barnbarn",
      "Social stigmatisering i lokalsamhället"
    ],
    "context_notes": "I samband med barnutredning är uppgifter om vårdnadshavares missbruk särskilt känsliga då de kan påverka barnens framtid.",
    "recommendation": "MASK_COMPLETE",
    "confidence": 0.92
  }
}
```

#### Användningsfall 2: Relationell Riskanalys

**Prompt:**
```python
PROMPT = f"""
ÄRENDE: Begäran om utlämnande av socialakt

BESTÄLLARE:
- Namn: {requester_name}
- Personnummer: {requester_pnr}
- Relation till ärende: {relation}
- Angivet syfte: {stated_purpose}

PERSONER I ÄRENDET:
{person_list_with_roles}

DOKUMENTERADE HÄNDELSER OCH KONFLIKTER:
{conflict_summary}

IDENTIFIERADE KÄNSLIGA UPPGIFTER:
{sensitive_info_list}

UPPGIFT:
Analysera relationerna mellan personerna och bedöm risken för
att någon lider men om uppgifterna lämnas ut till beställaren.

Beakta särskilt:
1. Finns pågående eller tidigare konflikter?
2. Finns maktförhållanden som kan missbrukas?
3. Kan information användas för att skada någon?
4. Finns särskilda skyddsbehov (barn, våldsutsatta)?
5. Finns dokumenterad våldsproblematik?
6. Kan familjerelationer skadas permanent?

Svara i JSON-format:
{{
  "overall_risk": "LOW|MEDIUM|HIGH|CRITICAL",
  "identified_conflicts": [
    {{
      "between": ["person1", "person2"],
      "nature": "beskrivning",
      "severity": "LOW|MEDIUM|HIGH"
    }}
  ],
  "power_dynamics": [
    {{
      "holder": "person med makt",
      "subject": "utsatt person",
      "type": "economic|physical|emotional|legal",
      "risk": "hur kan makt missbrukas"
    }}
  ],
  "vulnerable_persons": [
    {{
      "name": "person",
      "vulnerabilities": ["lista"],
      "protection_needed": "beskrivning"
    }}
  ],
  "risk_assessment_per_information": [
    {{
      "information": "specifik uppgift",
      "risk_if_disclosed": "beskrivning",
      "recommended_action": "RELEASE|MASK|REDACT_PARTIALLY"
    }}
  ],
  "overall_recommendation": "fritext-rekommendation",
  "legal_basis": "hänvisning till OSL"
}}
"""
```

#### Användningsfall 3: Juridisk Motivering

**Prompt för automatisk motivering:**
```python
PROMPT = f"""
Som handläggare på socialtjänsten har du beslutat att maskera
följande uppgift vid utlämnande:

UPPGIFT: "{text_to_mask}"
KATEGORI: {sensitivity_category}
BERÖR: {affected_persons}
BESTÄLLARE: {requester_info}
RISKBEDÖMNING: {risk_summary}

Skriv en professionell juridisk motivering för beslutet enligt
följande struktur:

BESLUT:
[Kort sammanfattning av beslut]

LAGSTÖD:
[Hänvisning till OSL 26:1 och relevanta bestämmelser]

OMSTÄNDIGHETER:
[Beskrivning av relevanta omständigheter i ärendet]

RISKBEDÖMNING:
[Bedömning av risk för men enligt omvänt skaderekvisit]

PROPORTIONALITETSBEDÖMNING:
[Varför maskning är proportionerligt och nödvändigt]

SLUTSATS:
[Sammanfattande slutsats]

Krav på texten:
- Juridiskt korrekt språk
- Objektiv och saklig ton
- Begriplig även för icke-jurister
- Konkret och specificerad till just detta fall
- 200-400 ord
"""
```

**Exempel-output:**
```
BESLUT:
Uppgiften om Agnes Grenqvists missbruksproblematik maskeras
vid utlämnande av socialakten till beställaren.

LAGSTÖD:
Enligt 26 kap. 1 § första stycket offentlighets- och
sekretesslagen (OSL) gäller sekretess inom socialtjänsten
för uppgift om en enskilds personliga förhållanden, om det
inte står klart att uppgiften kan röjas utan att den enskilde
eller någon närstående till denne lider men.

OMSTÄNDIGHETER:
Uppgiften om missbruksproblematik utgör känslig
hälsoinformation avseende barnens mormor Agnes Grenqvist.
Akten rör en barnutredning där Agnes och hennes partner
Sveinung är vårdnadshavare för två små barn. Beställaren
är en extern part utan etablerad rätt till information om
Agnes personliga hälsosituation. Samtycke från Agnes föreligger ej.

RISKBEDÖMNING:
Det föreligger uppenbar risk för att Agnes skulle lida men
om uppgiften röjs. Missbruksinformation är starkt
stigmatiserande och kan påverka Agnes relationer, anseende
och framtida möjligheter. Med hänsyn till den pågående
konfliktsituationen i familjen och den känsliga
vårdnadsfrågan föreligger även risk att informationen kan
användas på ett sätt som skadar Agnes och indirekt påverkar
barnens situation negativt.

PROPORTIONALITETSBEDÖMNING:
Maskning av uppgiften är proportionerligt då beställarens
informationsbehov kan tillgodoses utan att denna specifika
hälsouppgift röjs. Det omvända skaderekvistiet innebär att
vid minsta osäkerhet om risk för men ska uppgiften inte
lämnas ut.

SLUTSATS:
Uppgiften maskeras i enlighet med 26 kap. 1 § OSL då det
inte står klart att den kan röjas utan att Agnes lider men.
```

#### Användningsfall 4: Intelligent Fragmentering

**Prompt:**
```python
PROMPT = f"""
Följande textstycke innehåller både sekretessbelagd och
icke-känslig information:

ORIGINAL TEXT:
"{paragraph}"

IDENTIFIERADE KÄNSLIGA DELAR (från BERT):
{sensitive_entities}

UPPGIFT:
Föreslå MINSTA MÖJLIGA MASKNING som skyddar sekretessen
men maximerar mängden information som kan lämnas ut.

Överväg dessa alternativ:
1. Komplett maskning av hela stycket
2. Partiell maskning av endast känsliga ord/fraser
3. Omformulering som behåller budskap utan känsliga detaljer
4. Abstraktion (ersätt specifikt med generellt)

För varje alternativ, beskriv:
- Exakt hur texten skulle se ut
- Vad som går förlorat
- Vad som bevaras
- Sekretessnivå (säkerhet)
- Informationsvärde för beställare

Ge sedan en rekommendation med motivering.

Svara i JSON-format.
"""
```

**Exempel:**
```json
{
  "original": "Agnes har missbruksproblem och bor hos sin mamma Aina i Umeå.",
  "alternatives": [
    {
      "method": "COMPLETE_MASKING",
      "result": "[MASKERAD TEXT]",
      "information_lost": "All information",
      "information_preserved": "Ingen",
      "security_level": "MAXIMUM",
      "information_value": "NONE"
    },
    {
      "method": "PARTIAL_MASKING",
      "result": "Agnes har [HÄLSOPROBLEM] och bor hos sin mamma [NAMN] i [PLATS].",
      "information_lost": "Specifik hälsoinformation, moderens namn, stad",
      "information_preserved": "Att Agnes har hälsoutmaningar, bor hos modern",
      "security_level": "HIGH",
      "information_value": "MEDIUM"
    },
    {
      "method": "REFORMULATION",
      "result": "Den berörda personen har dokumenterade hälsoutmaningar och bor hos en anhörig i norra Sverige.",
      "information_lost": "Identifierbara detaljer",
      "information_preserved": "Huvudbudskap om situation",
      "security_level": "MEDIUM-HIGH",
      "information_value": "MEDIUM-HIGH"
    },
    {
      "method": "ABSTRACTION",
      "result": "Agnes bor hos en anhörig.",
      "information_lost": "Hälsoinformation helt, specifik anhörig, plats",
      "information_preserved": "Boendesituation i allmänna termer",
      "security_level": "MEDIUM",
      "information_value": "LOW-MEDIUM"
    }
  ],
  "recommendation": {
    "method": "PARTIAL_MASKING",
    "reasoning": "Balanserar sekretess och informationsvärde. Missbruksinformationen är känslig enligt OSL 26:1 och måste maskas. Namn och exakt plats är också känsligt i detta sammanhang. Däremot kan det faktum att Agnes har hälsoutmaningar och bor hos modern vara relevant för beställaren att känna till. Partiell maskning ger maximal information utan att röja specifika känsliga detaljer."
  }
}
```

#### Användningsfall 5: Insiktsbedömning

**Prompt:**
```python
PROMPT = f"""
FRÅGA: Kan beställaren rimligen redan känna till denna information?

UPPGIFT I AKTEN:
"{information}"

BESTÄLLARE:
- Namn: {requester_name}
- Relation till ärende: {relation}
- Angivet syfte: {purpose}

KONTEXT FRÅN AKTEN:
{relevant_context_from_case}

ANALYSFRÅGOR:
1. Är beställaren direkt omnämnd i denna del av akten?
2. Beskrivs beställaren som närvarande vid händelsen?
3. Har beställaren själv lämnat denna information till socialtjänsten?
4. Är informationen av sådan karaktär att beställaren rimligen
   måste känna till den (t.ex. gemensamma upplevelser)?
5. Finns bevis i akten för att beställaren känner till uppgiften?

Gör en steg-för-steg-analys av sannolikheten att beställaren
redan känner till informationen.

Om beställaren med hög sannolikhet redan känner till uppgiften
kan "insiktsregeln" tillämpas och sekretessen är försvagad.

Svara i JSON-format:
{{
  "mentioned_in_document": boolean,
  "present_at_event": "YES|NO|UNCLEAR",
  "provided_information_themselves": boolean,
  "reasonable_knowledge": boolean,
  "evidence_of_knowledge": ["lista med bevis från text"],
  "probability_score": 0-100,
  "step_by_step_reasoning": "detaljerat resonemang",
  "conclusion": "LIKELY_KNOWS|POSSIBLY_KNOWS|UNLIKELY_KNOWS|UNKNOWN",
  "recommendation": "APPLY_INSIGHT_RULE|DO_NOT_APPLY|UNCERTAIN",
  "additional_notes": "ytterligare överväganden"
}}
"""
```

### 4.2 Prompt Engineering Best Practices

**Struktur för alla prompts:**

1. **System-instruktion** - Definiera expertroll
2. **Uppgift** - Tydlig beskrivning av vad som ska göras
3. **Kontext** - All relevant information
4. **Riktlinjer** - Specifika saker att beakta
5. **Format** - Strukturerat output (JSON)
6. **Exempel** (vid behov) - Few-shot learning

**Säkerhetsprinciper:**
```python
# Alltid inkludera i system-prompt:
SAFETY_GUIDELINES = """
VIKTIGA PRINCIPER:
1. Vid minsta tvivel, rekommendera maskning (omvänt skaderekvisit)
2. Barn under 18 år har förstärkt skydd
3. Våldsutsatta personer har särskilt skyddsbehov
4. Hälsouppgifter är generellt sekretessbelagda
5. Bedöm alltid relationella risker
6. Dokumentera alltid ditt resonemang
7. Var transparent om osäkerhet
"""
```

**Temperatur-inställningar:**
- Känslighetsbedömning: `temperature=0.1` (konsistent)
- Motivering: `temperature=0.3` (något mer varierad text)
- Relationanalys: `temperature=0.2` (balanserat)

### 4.3 Implementation

```python
import asyncio
from typing import Dict, List
import json

class GPT_OSS_Analyzer:
    """Handler för GPT-OSS 120B analys"""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.model = "gpt-oss-120b"

    async def analyze_sensitivity(
        self,
        text: str,
        context: Dict,
        entities: Dict
    ) -> Dict:
        """Kontextuell känslighetsbedömning"""

        prompt = self._build_sensitivity_prompt(text, context, entities)

        response = await self._call_llm(
            prompt=prompt,
            max_tokens=1500,
            temperature=0.1
        )

        return self._parse_json_response(response)

    async def analyze_relations(
        self,
        case_summary: str,
        persons: List[Dict],
        requester: Dict
    ) -> Dict:
        """Relationell riskanalys"""

        prompt = self._build_relations_prompt(
            case_summary, persons, requester
        )

        response = await self._call_llm(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.2
        )

        return self._parse_json_response(response)

    async def generate_legal_reasoning(
        self,
        decision: str,
        context: Dict
    ) -> str:
        """Generera juridisk motivering"""

        prompt = self._build_reasoning_prompt(decision, context)

        response = await self._call_llm(
            prompt=prompt,
            max_tokens=800,
            temperature=0.3
        )

        return response.strip()

    async def suggest_minimal_redaction(
        self,
        paragraph: str,
        sensitive_parts: List[str]
    ) -> Dict:
        """Föreslå minimal maskning"""

        prompt = self._build_redaction_prompt(paragraph, sensitive_parts)

        response = await self._call_llm(
            prompt=prompt,
            max_tokens=1500,
            temperature=0.2
        )

        return self._parse_json_response(response)

    async def assess_insight(
        self,
        information: str,
        requester: Dict,
        case_context: str
    ) -> Dict:
        """Bedöm om beställare redan känner till info"""

        prompt = self._build_insight_prompt(
            information, requester, case_context
        )

        response = await self._call_llm(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.1
        )

        return self._parse_json_response(response)

    async def _call_llm(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """Anropa GPT-OSS via API"""

        # Implementation beroende på er setup
        # vLLM, text-generation-inference, eller custom API

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        # API-anrop här
        pass

    def _parse_json_response(self, response: str) -> Dict:
        """Extrahera JSON från LLM-svar"""
        try:
            # Hitta JSON i response
            start = response.find('{')
            end = response.rfind('}') + 1
            json_str = response[start:end]
            return json.loads(json_str)
        except:
            # Hantera fel
            return {"error": "Could not parse JSON", "raw": response}

    @property
    def system_prompt(self) -> str:
        return """
        Du är expert på menprövning enligt Offentlighets- och
        Sekretesslagen (OSL) kapitel 26. Din uppgift är att
        analysera sociala akter och hjälpa handläggare fatta
        välgrundade beslut om utlämnande av information.

        VIKTIGA PRINCIPER:
        1. Vid minsta tvivel, rekommendera maskning (omvänt skaderekvisit)
        2. Barn under 18 år har förstärkt skydd
        3. Våldsutsatta personer har särskilt skyddsbehov
        4. Hälsouppgifter är generellt sekretessbelagda
        5. Bedöm alltid relationella risker
        6. Dokumentera alltid ditt resonemang
        7. Var transparent om osäkerhet

        Svara alltid i specificerat JSON-format.
        """


class HybridMenprovningEngine:
    """Kombinerar BERT och GPT-OSS för optimal analys"""

    def __init__(self):
        self.bert = KBLabBERTNER()
        self.gpt = GPT_OSS_Analyzer(endpoint="http://llm-server:8000")

    async def full_analysis(
        self,
        document_path: str,
        requester_info: Dict
    ) -> Dict:
        """Komplett menprövningsanalys"""

        # STEG 1: BERT - Snabb strukturerad extraktion
        print("⚡ BERT-analys...")
        bert_results = await asyncio.gather(
            self.bert.extract_entities(document_path),
            self.bert.classify_sections(document_path),
            self.bert.identify_persons(document_path)
        )

        entities, sections, persons = bert_results

        # STEG 2: GPT-OSS - Djupanalys (parallellt där möjligt)
        print("🧠 GPT-OSS djupanalys...")

        # Analysera alla sektioner parallellt
        sensitivity_tasks = [
            self.gpt.analyze_sensitivity(
                text=section['text'],
                context=section,
                entities=entities
            )
            for section in sections if section['bert_category'] != 'NEUTRAL'
        ]

        sensitivity_analyses = await asyncio.gather(*sensitivity_tasks)

        # Relationanalys
        relation_analysis = await self.gpt.analyze_relations(
            case_summary=self._summarize_case(sections),
            persons=persons,
            requester=requester_info
        )

        # STEG 3: Kombinera resultat
        combined = self._combine_results(
            bert_entities=entities,
            bert_sections=sections,
            bert_persons=persons,
            gpt_sensitivity=sensitivity_analyses,
            gpt_relations=relation_analysis
        )

        # STEG 4: Generera rekommendationer
        recommendations = self._generate_recommendations(combined)

        return {
            "entities": entities,
            "sections_analysis": combined,
            "relations": relation_analysis,
            "recommendations": recommendations,
            "processing_time": "35 sekunder"
        }
```

### 4.4 Prestanda och Kostnader

**On-prem GPT-OSS 120B:**

```
Setup (engångskostnad):
- GPU-server (8x NVIDIA A100 80GB): ~2 000 000 kr
- Eller hyra från svensk leverantör: 50 000-80 000 kr/månad

Driftkostnad per menprövning:
- Elektricitet (~500W GPU-last i 30s): ~0.50 kr
- Total kostnad: ~0.50 kr per analys

Jämfört med Cloud:
- GPT-4 Turbo: ~20-30 kr per analys
- Claude 3: ~15-25 kr per analys
- Break-even: Efter 400-800 analyser/månad

Beräkningstid:
- BERT (entiteter + kategorier): 0.5-2 sekunder
- GPT-OSS (djupanalys): 10-30 sekunder
- Total tid: 10-35 sekunder per ärende
```

**Optimeringar:**
```python
# Caching av LLM-resultat för liknande text
@cached(ttl=86400)  # 24 timmar
async def analyze_common_phrase(text: str):
    # Om samma text analyseras ofta, cacha resultat
    pass

# Batch-processning för flera ärenden
async def batch_analyze(documents: List[str]):
    # Kör flera analyser parallellt
    tasks = [analyze(doc) for doc in documents]
    return await asyncio.gather(*tasks)

# Adaptiv djup - enklare fall behöver inte LLM
def needs_llm_analysis(bert_result: Dict) -> bool:
    # Om BERT är mycket säker och kategorin är tydlig
    if bert_result['confidence'] > 0.95 and \
       bert_result['category'] in ['NEUTRAL', 'PUBLIC_INFO']:
        return False
    return True
```

---

## 5. IMPLEMENTATIONSPLAN

### 5.1 Fas 1: Grund (Månad 1-3)

**Vecka 1-4: Projektuppsättning**
```
☐ Teknisk miljö
  - Docker-miljö för utveckling
  - PostgreSQL databas
  - Redis för caching
  - Git-repo och CI/CD

☐ Integration med befintligt
  - Studera befintligt anonymiseringsverktyg
  - Identifiera återanvändningsbara komponenter
  - API-kontrakt mellan system

☐ Databas-design
  - Tabell för ärenden
  - Tabell för dokument och versioner
  - Tabell för beslut och motiveringar
  - Relationsdata
```

**Vecka 5-8: AI-grund**
```
☐ BERT-integration
  - Återanvänd KBLab BERT NER
  - Wrapper för entitetsigenkänning
  - Basklassificering av kategorier

☐ GPT-OSS setup
  - Anslut till er on-prem GPT-OSS
  - Testa API och prestanda
  - Utveckla prompt-templates
  - Implementera error handling

☐ Pipeline
  - Orchestration layer
  - BERT → GPT-OSS flöde
  - Resultat-aggregering
```

**Vecka 9-12: UI MVP**
```
☐ Grundläggande gränssnitt
  - Ärenderegistrering
  - Dokumentuppladdning
  - Resultatvisning
  - Enkel maskning

☐ PDF-hantering
  - PDF.js integration
  - Textextraktion
  - Färgkodning av text

☐ Testning
  - Unit tests
  - Integration tests
  - Användartest med testdata
```

**Leverans Fas 1:**
- Fungerande MVP
- BERT + GPT-OSS pipeline
- Grundläggande UI
- Kan analysera enkla ärenden

### 5.2 Fas 2: Intelligens (Månad 4-5)

**Vecka 13-16: Relationanalys**
```
☐ Personidentifiering
  - Extrahera alla personer från text
  - Identifiera roller (mormor, barn, anmälare etc)
  - Koppla personer till information

☐ Relationsgraf
  - NetworkX-implementation
  - Visualisering med D3.js
  - Konfliktidentifiering

☐ GPT-OSS relationanalys
  - Prompt för relationsbedömning
  - Risk-scoring
  - Koppling beställare-berörda
```

**Vecka 17-20: Beslutsstöd**
```
☐ Riskbedömningsmotor
  - Viktning av olika risker
  - Ensemble av BERT + GPT-OSS
  - Confidence scoring

☐ Regelmotor för OSL
  - Tidsbedömning (70-årsgräns)
  - Sekretessbrytande faktorer
  - Automatiska kontroller

☐ Kunskapsbas
  - Databas med tidigare beslut
  - Sökfunktion för liknande fall
  - Rättsfall och prejudikat

☐ Motivering
  - GPT-OSS generering av juridisk text
  - Template-system
  - Redigering av AI-text
```

**Leverans Fas 2:**
- Intelligent riskbedömning
- Relationanalys med visualisering
- Automatisk motivering
- Kunskapsbas

### 5.3 Fas 3: Produktion (Månad 6-7)

**Vecka 21-24: Arbetsflöde**
```
☐ Ärendehantering
  - Komplett lifecycle (registrering → beslut → utlämning)
  - Status och milestolpar
  - Handläggar-tilldelning

☐ Versionshantering
  - Dokumentversioner
  - Ändringshistorik
  - Rollback-möjlighet

☐ Godkännanden
  - Arbetsflöde för granskning
  - Chefsgodkännande
  - Juristgranskning vid behov

☐ Integration
  - API mot befintligt ärendesystem
  - Export till e-arkiv
  - Integration med signering
```

**Vecka 25-28: Säkerhet och Drift**
```
☐ Säkerhet
  - Kryptering (rest + transit)
  - Rollbaserad åtkomstkontroll (RBAC)
  - Audit logging
  - Penetrationstester
  - GDPR-compliance

☐ Monitoring
  - Prometheus + Grafana
  - Alerts vid fel
  - Prestandaövervakning
  - AI-modell monitoring

☐ Deployment
  - Kubernetes-setup
  - CI/CD pipeline
  - Blue-green deployment
  - Backup-strategi

☐ Dokumentation
  - Teknisk dokumentation
  - Användarmanual
  - API-dokumentation
  - Driftinstruktioner

☐ Utbildning
  - Utbildningsmaterial
  - Workshops för handläggare
  - Support-dokumentation
```

**Leverans Fas 3:**
- Produktionsklart system
- Komplett säkerhet
- Monitoring och drift
- Utbildat team

### 5.4 Fas 4: Optimering (Löpande)

```
☐ Användarf eedback
  - Samla in feedback från handläggare
  - Identifiera förbättringsområden
  - Prioritera features

☐ Modellförbättring
  - Fine-tuning baserat på verkliga data
  - A/B-testning av olika prompts
  - Förbättra precision

☐ Ny funktionalitet
  - Baserat på användarönskemål
  - Integrera med fler system

☐ Skalning
  - Optimera prestanda
  - Hantera ökad belastning
```

---

## 6. ORGANISATION OCH ROLLER

### 6.1 Projektteam

**Kärnteam:**
- **Projektledare (50%)** - Samordning, planering, uppföljning
- **Backend-utvecklare x2 (100%)** - API, databas, integration
- **AI/ML-specialist (75%)** - BERT, GPT-OSS, prompt engineering
- **Frontend-utvecklare (75%)** - React, UI/UX
- **UX-designer (25%)** - Användargränssnitt, användartest

**Stödfunktioner:**
- **Juridisk expert (konsult, ~20 dagar)** - OSL-rådgivning, validation
- **DevOps (25%)** - Infrastruktur, deployment
- **Säkerhetsexpert (konsult, ~10 dagar)** - Security audit
- **Testare (50% under fas 3)** - Systematisk testning

### 6.2 Styrgrupp

- Socialtjänsten (chef, handläggare)
- IT-avdelning
- Dataskyddsombud
- Jurist
- Projektledare

**Möten:** Var 3:e vecka, beslut om prioriteringar

### 6.3 Referensgrupp

- 5-8 handläggare från olika enheter
- Testar prototyper
- Ger feedback
- Validerar AI-beslut

---

## 7. BUDGET

### 7.1 Personal (7 månader)

| Roll | Omfattning | Kostnad |
|------|------------|---------|
| Projektledare | 50%, 7 mån | 200 000 kr |
| Backend-utvecklare x2 | 100%, 7 mån | 1 000 000 kr |
| AI/ML-specialist | 75%, 7 mån | 400 000 kr |
| Frontend-utvecklare | 75%, 7 mån | 350 000 kr |
| UX-designer | 25%, 7 mån | 100 000 kr |
| DevOps | 25%, 7 mån | 100 000 kr |
| Testare | 50%, 3 mån | 100 000 kr |
| Juridisk expert | 20 dagar | 200 000 kr |
| Säkerhetsexpert | 10 dagar | 100 000 kr |
| **SUMMA PERSONAL** | | **2 550 000 kr** |

### 7.2 Infrastruktur och Licenser

| Post | Kostnad |
|------|---------|
| Utvecklingsmiljö (servrar, verktyg) | 50 000 kr |
| GPU-tid för träning (om extern) | 50 000 kr |
| Testmiljö | 30 000 kr |
| Licenser (IDE, verktyg, bibliotek) | 50 000 kr |
| Säkerhetsverktyg | 30 000 kr |
| **SUMMA INFRASTRUKTUR** | **210 000 kr** |

### 7.3 Drift (År 1)

| Post | Kostnad |
|------|---------|
| Servrar/hosting | 120 000 kr |
| GPT-OSS on-prem (elektricitet) | 30 000 kr |
| Support och underhåll | 200 000 kr |
| Vidareutveckling | 300 000 kr |
| Utbildning | 50 000 kr |
| **SUMMA DRIFT** | **700 000 kr** |

### 7.4 Total Budget

| Fas | Kostnad |
|-----|---------|
| Utveckling (7 mån) | 2 760 000 kr |
| Drift (år 1) | 700 000 kr |
| **TOTALT ÅR 1** | **3 460 000 kr** |

**Efterföljande år:** ~700 000 kr/år (drift + vidareutveckling)

---

## 8. RISKER OCH ÅTGÄRDER

### 8.1 Tekniska Risker

| Risk | Sannolikhet | Påverkan | Åtgärd |
|------|-------------|----------|--------|
| GPT-OSS prestanda otillräcklig | Låg | Medel | Testa tidigt, optimera prompts, fallback till enklare modell |
| BERT precision för låg | Medel | Medel | Fine-tuning, human-in-loop, ensemble-metoder |
| Integration med befintligt system svår | Medel | Medel | Tidiga tekniska spikes, API-kontrakt |
| Skalbarhetsproblem | Låg | Medel | Load testing, caching, optimering |

### 8.2 Juridiska Risker

| Risk | Sannolikhet | Påverkan | Åtgärd |
|------|-------------|----------|--------|
| AI ger felaktiga rekommendationer | Medel | Hög | Human-in-loop (ALLTID), konservativ default, logging |
| Juridisk tolkning felaktig | Medel | Hög | Nära samarbete med jurist, regelbunden validering |
| GDPR-överträdelse vid dataläckage | Låg | Kritisk | Kryptering, audit logs, penetrationstester, säkerhetsaudit |
| Felaktig utlämning av sekretess | Låg | Kritisk | Konservativ AI-inställning, dubbel-check, revision |

### 8.3 Organisatoriska Risker

| Risk | Sannolikhet | Påverkan | Åtgärd |
|------|-------------|----------|--------|
| Låg användara cceptans | Medel | Hög | Tidigt användartest, referensgrupp, utbildning |
| Bristande juridisk förankring | Medel | Hög | Juridisk expert i teamet, regelbundna avstämningar |
| Resursb rist under projekt | Medel | Medel | Backup-resurser, flexibel planering |
| Förändrade juridiska krav | Låg | Medel | Flexibel arkitektur, regelbunden regelbevakning |

### 8.4 Datakvalitetsrisker

| Risk | Sannolikhet | Påverkan | Åtgärd |
|------|-------------|----------|--------|
| Träningsdata bristfällig | Medel | Medel | Syntetisk data, expert-annotation, validering |
| Bias i AI-modeller | Medel | Hög | Bias-testing, mångfald i träningsdata, transparent AI |
| OCR-fel i äldre dokument | Hög | Medel | Manuell korrektur, konfidensscoring, varning till användare |

---

## 9. FRAMGÅNGSFAKTORER

### 9.1 Kritiska Faktorer

1. **Juridisk förankring**
   - Kontinuerlig dialog med jurist och dataskyddsombud
   - Validering av AI-beslut mot rättsfall
   - Uppdaterad kunskapsbas

2. **Användarcentrering**
   - Handläggare involverade från start
   - Iterativ design med feedback
   - Användarvänligt gränssnitt

3. **Säkerhet först**
   - Security by design
   - Kryptering end-to-end
   - Regelbundna säkerhetsaudits

4. **Transparens**
   - AI-beslut måste vara förklarbara
   - Dokumentation av all logik
   - Möjlighet att granska AI-resonemang

5. **Human-in-the-loop**
   - AI är STÖD, inte ersättning
   - Människa fattar alltid slutgiltigt beslut
   - Möjlighet att alltid övertyra AI

6. **Kvalitetssäkring**
   - Regelbunden validering av AI-precision
   - A/B-testning av förbättringar
   - Kontinuerlig uppföljning

7. **Utbildning och support**
   - Grundlig utbildning av alla användare
   - Tillgänglig support
   - Dokumentation och guides

### 9.2 Mätbara Mål

**Effektivitet:**
- 50% reducerad tid för menprövning (från ~2h till ~1h)
- 80% av ärenden kan hanteras utan juristgranskning

**Kvalitet:**
- 95% korrekthet i AI-rekommendationer (verifierat av expert)
- <5% av beslut behöver omprovas
- 100% spårbarhet av alla beslut

**Säkerhet:**
- 0 säkerhetsincidenter
- 0 felaktiga utlämnanden
- 100% kryptering av känslig data

**Användarnöjdhet:**
- >80% användarnöjdhet
- >70% upplever ökad säkerhet i beslut
- >60% känner sig mer effektiva

**Efterlevnad:**
- 100% compliance med OSL
- 100% GDPR-efterlevnad
- 100% dokumentation av beslut

---

## 10. NÄSTA STEG

### 10.1 Beslutsunderlag

För att påbörja projektet behövs:

1. **Godkännande av budget** (~3.5 MSEK år 1)
2. **Tilldelning av resurser** (projektteam)
3. **Beslut om tidsplan** (start-datum)
4. **Godkännande av leverantör** för GPT-OSS (om extern)

### 10.2 Förberedelser

**Innan projektstart:**

1. **Teknisk förberedelse**
   - Inventera befintlig infrastruktur
   - Verifiera GPT-OSS 120B-tillgång
   - Testa API-anslutning
   - Sätt upp utvecklingsmiljö

2. **Datainsamling**
   - Identifiera avidentifierade testakter
   - Skapa syntetiska testdata
   - Säkerställ juridisk godkännande

3. **Juridisk förankring**
   - Workshop med jurister
   - Inventera OSL-tillämpning
   - Dokumentera nuvarande process

4. **Användarförberedelse**
   - Rekrytera referensgrupp
   - Inventera nuvarande smärtpunkter
   - Kartlägga arbetsflöden

### 10.3 Pilot-projekt (rekommenderas)

**Innan full utveckling:**

Överväg en 2-månaders pilot med begränsad scope:
- Enkel integration BERT + GPT-OSS
- Analysera 10-20 testärenden
- Validera teknisk genomförbarhet
- Verifiera AI-precision
- Testa användargränssnitt

**Kostnad pilot:** ~400 000 kr
**Värde:** Reducerad risk, verifierad approach

---

## 11. KONTAKTER OCH DOKUMENTREFERENSER

### 11.1 Dokumentation

- Detta dokument: `/anonymisering/PLAN_Menprovningsverktyg.md`
- Menprövningsprocess: `/anonymisering/Menprövning...docx`
- Testdokument: `/anonymisering/testfilAi.pdf`
- Befintligt verktyg: `github.com/FRALLAN76/Anonymisering`

### 11.2 Nyckelpersoner (exempel)

- **Projektansvarig:** [Namn]
- **Juridisk expert:** [Namn]
- **AI/ML-lead:** [Namn]
- **Dataskyddsombud:** [Namn]

### 11.3 Externa Resurser

**Lagstiftning:**
- Offentlighets- och sekretesslagen (SFS 2009:400)
- GDPR (EU 2016/679)

**AI-modeller:**
- KBLab Swedish BERT: huggingface.co/KB/bert-base-swedish-cased-ner
- GPT-OSS 120B: [Er leverantör]

**Community:**
- Svenska AI-forum
- OSL-praxis databas
- Socialtjänstens rättsliga nätverk

---

## 12. VERSIONSHISTORIK

| Version | Datum | Författare | Ändringar |
|---------|-------|------------|-----------|
| 1.0 | 2025-11-25 | AI-assistent | Första version, komplett plan |

---

## BILAGOR

### Bilaga A: Exempel-prompts för GPT-OSS

Se avsnitt 4.1 för detaljerade prompt-templates

### Bilaga B: Databas-schema

```sql
-- Kommer att utvecklas i fas 1
CREATE TABLE cases (
    id SERIAL PRIMARY KEY,
    requester_id VARCHAR(13),
    requester_name VARCHAR(255),
    relation_to_case VARCHAR(100),
    purpose TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id),
    original_path VARCHAR(500),
    version INTEGER,
    created_at TIMESTAMP
);

CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    entity_type VARCHAR(50),
    entity_text VARCHAR(500),
    start_pos INTEGER,
    end_pos INTEGER,
    confidence FLOAT
);

CREATE TABLE decisions (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id),
    section_id VARCHAR(100),
    decision VARCHAR(50), -- RELEASE, MASK, PARTIAL
    reasoning TEXT,
    legal_basis VARCHAR(200),
    decided_by VARCHAR(100),
    decided_at TIMESTAMP
);

-- Flera fler tabeller...
```

### Bilaga C: API-specifikation

```yaml
# OpenAPI-spec kommer att utvecklas
openapi: 3.0.0
info:
  title: Menprövnings-API
  version: 1.0.0
paths:
  /api/v1/cases:
    post:
      summary: Skapa nytt ärende
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                requester_id: string
                document: binary
  # etc...
```

---

## SAMMANFATTNING

Detta dokument beskriver en komplett plan för att utveckla ett AI-stött verktyg för menprövning av sociala handlingar. Verktyget kombinerar snabb BERT-baserad entitetsigenkänning med djup GPT-OSS-analys för att hjälpa handläggare fatta välgrundade beslut enligt Offentlighets- och Sekretesslagen.

**Kärnvärden:**
- Effektivitet: 50% snabbare menprövning
- Kvalitet: 95% precision i AI-rekommendationer
- Säkerhet: Konservativa defaults, human-in-loop
- Transparens: Alla AI-beslut förklaras och loggas

**Tidsplan:** 7 månader till produktion
**Kostnad:** 3.5 MSEK (år 1), 0.7 MSEK/år därefter
**ROI:** Efter 1-2 år genom tidsbesparing och ökad kvalitet

För frågor eller diskussion, kontakta projektledare.

---
**Dokument slut**

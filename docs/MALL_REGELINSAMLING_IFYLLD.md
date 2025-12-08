# Mall för insamling av menprövningsregler - IFYLLD EXEMPEL

**Instruktion:** Detta är en ifylld exempelmall baserad på officiella källor och testfilen testfilAi.pdf. Arkivarier bör komplettera och anpassa efter sin verksamhets specifika behov.

**Ifylld av:** AI (baserat på officiella källor)
**Datum:** 2025-12-08
**Status:** Exempel - ska kompletteras av verksamheten

---

## DEL 1: UPPGIFTSTYPER OCH LAGRUM

| Uppgiftstyp | Lagrum | Alltid sekretess? | Kommentar |
|-------------|--------|-------------------|-----------|
| Personnummer | OSL 26:1 | **JA** | Maska alltid, oavsett vems |
| Namn på anmälare (privatperson) | OSL 26:1 | **JA** | Skydd mot repressalier |
| Namn på anmälare (myndighet) | OSL 26:1 | Delvis | Myndighetsnamn OK, inte individnamn |
| Namn på tredje man | OSL 26:1, 10:3 | **JA** | Alla som nämns utom beställare/ämne |
| Adress till tredje man | OSL 26:1 | **JA** | Kontaktuppgifter skyddas |
| Telefonnummer till tredje man | OSL 26:1 | **JA** | Kontaktuppgifter skyddas |
| Hälsouppgifter | OSL 26:1 | **JA** | Känslig kategori |
| Missbruksuppgifter | OSL 26:1 | **JA** | Känslig kategori |
| Ekonomiska uppgifter | OSL 26:1 | Oftast | Maska detaljer |
| Tjänstemans namn | OSL 26:1 | Nej | Offentlig uppgift |
| Tjänstemans personnummer | OSL 26:1 | **JA** | Maska alltid |

---

## DEL 2: KATEGORIER AV KÄNSLIG INFORMATION

### Hälsouppgifter
| Typ av uppgift | Exempel | Åtgärd | Lagrum |
|----------------|---------|--------|--------|
| Diagnoser | "depression", "ADHD", "cancer", "diabetes" | MASKA | OSL 26:1 |
| Behandling | "medicinering", "terapi", "operation" | MASKA | OSL 26:1 |
| Medicinering | "tar medicin för...", specifika läkemedel | MASKA | OSL 26:1 |
| Funktionsnedsättning | "LSS-insats", "rullstolsburen" | MASKA | OSL 26:1 |
| Psykisk ohälsa | "mår dåligt", "ångest", "BUP-kontakt" | MASKA | OSL 26:1 |
| Sjukskrivning | "sjukskriven sedan..." | MASKA | OSL 26:1 |

### Missbruk
| Typ av uppgift | Exempel | Åtgärd | Lagrum |
|----------------|---------|--------|--------|
| Alkoholmissbruk | "missbruka alkohol", "berusad", "nykter" | MASKA | OSL 26:1 |
| Narkotikamissbruk | "använder droger", "cannabis", "amfetamin" | MASKA | OSL 26:1 |
| Spelmissbruk | "spelproblem", "spelande" | MASKA | OSL 26:1 |
| Behandling | "avgiftning", "behandlingshem", "AA" | MASKA | OSL 26:1 |

### Ekonomi
| Typ av uppgift | Exempel | Åtgärd | Lagrum |
|----------------|---------|--------|--------|
| Skulder | "betalningsanmärkningar", "kronofogden" | MASKA | OSL 26:1 |
| Försörjningsstöd | "socialbidrag", "ekonomiskt bistånd" | MASKA | OSL 26:1 |
| Arbetslöshet | "arbetslös sedan...", "saknar inkomst" | MASKA detaljer | OSL 26:1 |
| Vräkning | "vräkningshotad", "hyresskuld" | MASKA | OSL 26:1 |

### Familjesituation
| Typ av uppgift | Exempel | Åtgärd | Lagrum |
|----------------|---------|--------|--------|
| Vårdnadstvist | "vårdnad", "umgängesrätt" | MASKA detaljer | OSL 26:1 |
| Umgängesfrågor | "umgänge med...", "umgängesstöd" | MASKA | OSL 26:1 |
| LVU | "omhändertagande", "LVU-placering" | KONTEXTUELLT | OSL 26:1 |
| Familjekonflikt | "konflikt mellan...", "bråk" | MASKA | OSL 26:1 |

### Våld och hot
| Typ av uppgift | Exempel | Åtgärd | Lagrum |
|----------------|---------|--------|--------|
| Fysiskt våld | "slagen", "misshandel", "sparkar" | MASKA | OSL 26:1 |
| Hot | "hotad", "rädd för", "kontaktförbud" | MASKA | OSL 26:1 |
| Skyddsbehov | "skyddat boende", "kvinnojour" | MASKA KRITISKT | OSL 26:1 |

---

## DEL 3: ROLLER OCH RELATIONER

### Vem är "tredje man"?

| Roll | Relation till ärendet | Ska alltid maskeras? |
|------|----------------------|---------------------|
| Mormor/morfar | Släkting till barnet | **JA** |
| Farmor/farfar | Släkting till barnet | **JA** |
| Anmälare (privatperson) | Uppgiftslämnare | **JA** |
| Granne | Vittne/anmälare | **JA** |
| Lärare | Professionell kontakt | Namn JA, roll OK |
| Tidigare partner | Nämnd i ärende | **JA** |
| Vänner till familjen | Nämns i beskrivning | **JA** |
| Barn till tredje man | Indirekt omnämnd | **JA** |

### Professionella roller

| Roll | Maska namn? | Maska personnr? | Kommentar |
|------|-------------|-----------------|-----------|
| Socialsekreterare | Nej | **JA** | Namn är offentligt |
| Handläggare | Nej | **JA** | Namn är offentligt |
| Familjepedagog | Nej | **JA** | Namn är offentligt |
| Kurator | Nej | **JA** | Namn är offentligt |
| Psykolog | Nej | **JA** | Namn är offentligt |
| Läkare | Nej | **JA** | Namn är offentligt |
| Polis | Nej | **JA** | Namn är offentligt |

---

## DEL 4: VANLIGA SCENARIER

### Scenario 1: Förälder begär ut egen akt
**Situation:** En förälder begär ut sin egen akt från socialtjänsten
**Beställare:** Den enskilde själv
**Vad ska maskeras:**
- Alla tredje mäns namn och kontaktuppgifter
- Anmälares identitet (om privatperson)
- Känsliga uppgifter om andra personer
**Vad kan lämnas ut:**
- Uppgifter om beställaren själv
- Administrativa uppgifter
- Tjänstemäns namn
**Lagrum:** OSL 26:6 (partsinsyn)
**Motivering:** Part har rätt till insyn i eget ärende, men tredje man skyddas

### Scenario 2: Förälder begär ut barnets akt
**Situation:** Vårdnadshavare begär ut akt som rör deras barn
**Beställare:** Vårdnadshavare
**Vad ska maskeras:**
- Tredje mäns uppgifter
- Anmälares identitet
- Uppgifter som kan skada barnet vid utlämnande
**Vad kan lämnas ut:**
- Uppgifter om barnet (prövning av barnets bästa)
- Administrativa beslut
**Lagrum:** OSL 26:1, barnets bästa
**Motivering:** Vårdnadshavare har partsinsyn men barnets bästa kan begränsa

### Scenario 3: LVU-placerat barn
**Situation:** Vårdnadshavare begär ut akt för LVU-placerat barn
**Beställare:** Vårdnadshavare
**Vad ska maskeras:**
- Tredje mäns uppgifter
- Uppgifter som kan missbrukas
- Uppgifter som kan skada barnet
**Vad kan lämnas ut:**
- Information om hur det går för barnet (i allmänna termer)
- Beslut om placering
**Lagrum:** OSL 26:1, LVU
**Motivering:** Vårdnadshavare är part men socialnämnden kan begränsa vid risk för barnet

### Scenario 4: Forskare begär ut akter
**Situation:** Forskare begär ut material för forskning
**Beställare:** Extern part (forskare)
**Vad ska maskeras:**
- ALLA identifierande uppgifter
- ALLA personnummer
- ALLA namn
- ALLA adresser och kontaktuppgifter
**Vad kan lämnas ut:**
- Avidentifierad information
- Statistisk information
**Lagrum:** OSL 26:1, etikprövning
**Motivering:** Stark sekretess gäller mot utomstående

### Scenario 5: Anmälare vill veta vad som hänt
**Situation:** Person som gjort orosanmälan vill veta utfall
**Beställare:** Anmälare
**Vad ska maskeras:**
- All information om ärendet
- Familjens identitet
- Beslut och åtgärder
**Vad kan lämnas ut:**
- Bekräftelse att anmälan mottagits (endast)
**Lagrum:** OSL 26:1
**Motivering:** Anmälare har ingen partsställning, stark sekretess gäller

---

## DEL 5: NYCKELORD OCH FRASER

### Hälsa
- diagnos, sjuk, sjukdom, behandling, medicin, medicinering
- läkare, sjukhus, vårdcentral, BVC, MVC
- operation, cancer, diabetes, hjärtsjukdom
- funktionsnedsättning, handikapp, LSS, assistans
- sjukskriven, rehabilitering, habilitering

### Psykisk ohälsa
- depression, ångest, psykos, psykisk ohälsa
- BUP, psykiatri, psykolog, psykiatriker
- mår dåligt, självmord, suicid, självskada
- ätstörning, anorexi, bulimi
- ADHD, autism, ADD
- utmattning, utbrändhet, stress
- tvångsvård, LPT, inlagd

### Missbruk
- missbruk, alkohol, alkoholist, berusad
- narkotika, drog, droger, knark
- beroende, abstinens, återfall
- nykter, nykterhetsarbete
- spelmissbruk, spelberoende
- cannabis, amfetamin, heroin, kokain
- avgiftning, behandlingshem, AA, NA

### Våld
- våld, misshandel, slagen, slag
- spark, knuff, strypning
- hot, hotad, rädd, skyddsbehov
- kontaktförbud, polisanmälan
- kvinnofrid, skyddat boende, kvinnojour
- övergrepp, förövare

### Ekonomi
- skuld, skulder, kronofogden
- betalningsanmärkning, inkasso
- fattig, fattigt, dålig ekonomi
- försörjningsstöd, socialbidrag, ekonomiskt bistånd
- vräkning, hyresskuld, avhysning
- arbetslös, a-kassa

### Familj/Barn
- vårdnadstvist, umgänge, umgängesrätt
- separation, skilsmässa
- LVU, omhändertagande, placering
- familjehem, HVB, institution
- orosanmälan, barnavårdsutredning
- bristande omsorg, föräldrars förmåga
- barn som far illa

### Boende
- hemlös, bostadslös
- vräkning, avhysning
- trångbodd, sanitär olägenhet
- ohygienisk, smutsigt
- störningsjouren, grannar klagar

---

## DEL 6: UNDANTAG OCH SPECIALFALL

| Situation | Standardregel | Undantag | Motivering |
|-----------|---------------|----------|------------|
| Samtycke finns | Maska | Kan lämnas ut | OSL 26:3 - samtycke häver sekretess |
| Fara för liv/hälsa | Maska | Kan lämnas ut | OSL 26:4 - nödvändigt utlämnande |
| Anmälare är myndighet | Maska individ | Myndighetsnamn OK | Myndigheten är offentlig |
| Handling äldre än 70 år | Maska | Pröva utlämnande | Sekretess kan ha upphört |
| "PRIVATPERSON" i text | Maska | Behåll | Redan anonymiserat |
| Beslut om LVU | Maska detaljer | Beslut är offentligt | Bara beslutet, inte underlag |

---

## DEL 7: TIDSGRÄNSER

| Uppgiftstyp | Tidsgräns | Kommentar |
|-------------|-----------|-----------|
| Generell socialtjänstsekretess | 70 år | OSL 26:1 |
| Skyddade personuppgifter | Tills vidare | Så länge skyddet gäller |
| Uppgifter om levande person | Livstid + 70 år | Kan gälla i vissa fall |

**OBS:** Arkivet gör alltid sekretessprövning av handlingar yngre än 70 år.

---

## DEL 8: FORMULERINGAR I BESLUT

### Standardformuleringar för maskning

**Vid maskning av tredje man:**
> "Uppgiften maskeras med stöd av OSL 26:1 då det rör sig om uppgift om tredje mans personliga förhållanden och det inte står klart att uppgiften kan röjas utan men."

**Vid maskning av anmälare:**
> "Uppgiften maskeras med stöd av OSL 26:1 då det rör sig om uppgift som kan identifiera anmälaren och det inte står klart att röjande kan ske utan men för denne."

**Vid maskning av känslig uppgift:**
> "Uppgiften maskeras med stöd av OSL 26:1 då det rör känslig uppgift om [hälsa/missbruk/ekonomi] och det inte står klart att uppgiften kan röjas utan men."

**Vid maskning av personnummer:**
> "Personnummer maskeras med stöd av OSL 26:1 då det utgör identifierande uppgift."

### Standardformuleringar för utlämnande

**Vid partsinsyn:**
> "Uppgiften lämnas ut med stöd av OSL 26:6 då beställaren är part i ärendet och har rätt till insyn."

**Vid samtycke:**
> "Uppgiften lämnas ut då den enskilde har samtyckt till utlämnande enligt OSL 26:3."

---

## EXEMPEL FRÅN TESTFIL (testfilAi.pdf)

### Identifierade entiteter och åtgärder

| Entitet | Typ | Åtgärd | Motivering |
|---------|-----|--------|------------|
| 18091331-1234 | Personnummer | MASKA | Alltid identifierande |
| 18561225-1234 | Personnummer | MASKA | Alltid identifierande |
| Agnes Grenqvist | Person | PRÖVA | Beror på beställare |
| Sveinung Grenqvist | Person | PRÖVA | Tredje man om ej beställare |
| Klara Ohlsson-Nilsson | Person | MASKA | Anmälare |
| Svea Brunnsdotter | Person | MASKA | Tredje man (mormor) |
| 0707-720707 | Telefon | MASKA | Kontaktuppgift |
| 1234-556789 | Telefon | MASKA | Anmälares kontaktuppgift |
| Ebbe Lieberathsgatan 93 | Adress | PRÖVA | Beror på beställare |
| "missbruka alkohol" | Känslig | MASKA | Missbruk - OSL 26:1 |
| "sanitär olägenhet" | Känslig | MASKA | Boende - OSL 26:1 |
| "betalningsanmärkningar" | Känslig | MASKA | Ekonomi - OSL 26:1 |

---

**SIGNATUR**

Ifylld av: AI (baserat på officiella källor)
Datum: 2025-12-08
Roll: Systemstöd för menprövning

---

**Detta är ett exempel. Verksamheten ska komplettera med egna regler och scenarier.**

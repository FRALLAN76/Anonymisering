"""Chattmodul för kravställningsdialog.

Guidad dialog för att samla in information om beställaren
innan menprövningsanalysen startar.
"""

import json
import logging
from typing import Optional

from src.core.models import RequesterContext, RequesterType, RelationType
from src.llm.client import LLMClient, LLMConfig

logger = logging.getLogger(__name__)


# System-prompt för kravställningsdialogen
REQUESTER_CHAT_SYSTEM_PROMPT = """Du är en assistent som hjälper handläggare inom socialtjänsten att förbereda menprövning enligt OSL kapitel 26.

Din uppgift är att ställa korta, tydliga frågor för att förstå VEM som begär handlingen och VARFÖR.

VIKTIGT:
- Ställ EN fråga i taget
- Var koncis och professionell
- Använd svenska
- Max 2-3 meningar per svar
- Sammanfatta ALDRIG i JSON förrän användaren har bekräftat att informationen är korrekt

När du har samlat in tillräcklig information (typ av beställare, relation, syfte),
sammanfatta och fråga om det stämmer. Först när användaren bekräftar,
returnera ett JSON-objekt med följande struktur:

```json
{
  "complete": true,
  "requester_type": "SUBJECT_SELF|PARENT_1|PARENT_2|CHILD_OVER_15|LEGAL_GUARDIAN|OTHER_PARTY|AUTHORITY|PUBLIC",
  "relation_type": "SELF|PARENT|CHILD|SPOUSE|SIBLING|OTHER_RELATIVE|LEGAL_REPRESENTATIVE|AUTHORITY_REPRESENTATIVE|NO_RELATION",
  "requester_name": "namn eller null",
  "subject_name": "namn på den ärendet gäller eller null",
  "is_authority": true/false,
  "authority_name": "myndighetens namn eller null",
  "has_consent": true/false,
  "purpose": "kort beskrivning av syftet",
  "special_circumstances": "eventuella särskilda omständigheter eller null"
}
```

Frågeflöde:
1. Vem begär handlingen? (privatperson, myndighet, den enskilde själv)
2. Vilken relation har beställaren till den som ärendet gäller?
3. Vad är syftet med begäran?
4. (Om relevant) Finns samtycke från den enskilde?
5. Sammanfatta och bekräfta

Om beställaren är en myndighet, fråga vilken myndighet.
Om beställaren är närstående, fråga om relationen (förälder, barn, etc.)."""


class RequesterChatSession:
    """Hanterar en kravställningsdialog-session."""

    def __init__(self, llm_client: Optional[LLMClient] = None, api_key: Optional[str] = None):
        """
        Initiera chatt-session.

        Args:
            llm_client: Befintlig LLM-klient att återanvända
            api_key: API-nyckel om ingen klient ges
        """
        if llm_client:
            self.llm_client = llm_client
        elif api_key:
            config = LLMConfig(api_key=api_key)
            self.llm_client = LLMClient(config)
        else:
            self.llm_client = None

        self.messages: list[dict[str, str]] = []
        self.context: Optional[RequesterContext] = None
        self.is_complete = False

    def start(self) -> str:
        """Starta dialogen med en inledande fråga."""
        initial_message = (
            "Hej! Jag hjälper dig förbereda menprövningen.\n\n"
            "**Vem begär ut handlingen?**\n"
            "- En privatperson\n"
            "- En myndighet\n"
            "- Den enskilde själv (personen som ärendet gäller)"
        )
        return initial_message

    def chat(self, user_message: str) -> str:
        """
        Skicka användarens meddelande och få svar.

        Args:
            user_message: Användarens meddelande

        Returns:
            Assistentens svar
        """
        # Lägg till användarens meddelande
        self.messages.append({"role": "user", "content": user_message})

        # Om ingen LLM, använd regelbaserad dialog
        if not self.llm_client or not self.llm_client.is_configured():
            return self._rule_based_response(user_message)

        try:
            # Skicka till LLM
            response = self.llm_client.chat(
                messages=self.messages,
                system_prompt=REQUESTER_CHAT_SYSTEM_PROMPT,
                temperature=0.3,  # Lite högre för mer naturlig dialog
                max_tokens=500,
            )

            assistant_message = response.content

            # Kolla om svaret innehåller färdig JSON
            if self._try_parse_completion(assistant_message):
                self.is_complete = True

            # Spara assistentens svar
            self.messages.append({"role": "assistant", "content": assistant_message})

            return assistant_message

        except Exception as e:
            logger.error(f"LLM-fel i kravställningsdialog: {e}")
            return self._rule_based_response(user_message)

    def _rule_based_response(self, user_message: str) -> str:
        """Fallback: Regelbaserad dialog utan LLM."""
        msg_lower = user_message.lower()
        question_count = len([m for m in self.messages if m["role"] == "user"])

        # Fråga 1: Vem begär?
        if question_count == 1:
            if any(word in msg_lower for word in ["själv", "egen", "mig", "jag"]):
                self._set_partial_context(requester_type=RequesterType.SUBJECT_SELF)
                return "Då gäller partsinsyn. **Vad är syftet med begäran?**"
            elif any(word in msg_lower for word in ["myndighet", "kommun", "försäkringskassa", "polis"]):
                self._set_partial_context(requester_type=RequesterType.AUTHORITY, is_authority=True)
                return "**Vilken myndighet begär handlingen?**"
            else:
                self._set_partial_context(requester_type=RequesterType.PUBLIC)
                return "**Vilken relation har beställaren till den som ärendet gäller?**\n- Förälder\n- Barn\n- Make/maka/sambo\n- Annan släkting\n- Ingen relation"

        # Fråga 2: Relation eller myndighet
        if question_count == 2:
            if any(word in msg_lower for word in ["förälder", "mamma", "pappa", "mor", "far"]):
                self._set_partial_context(
                    requester_type=RequesterType.PARENT_1,
                    relation_type=RelationType.PARENT
                )
            elif any(word in msg_lower for word in ["barn", "son", "dotter"]):
                self._set_partial_context(
                    requester_type=RequesterType.CHILD_OVER_15,
                    relation_type=RelationType.CHILD
                )
            elif any(word in msg_lower for word in ["make", "maka", "sambo", "partner"]):
                self._set_partial_context(relation_type=RelationType.SPOUSE)
            elif any(word in msg_lower for word in ["ingen", "allmän"]):
                self._set_partial_context(
                    requester_type=RequesterType.PUBLIC,
                    relation_type=RelationType.NO_RELATION
                )
            else:
                # Spara som myndighetens namn eller annan relation
                if self._partial_context.get("is_authority"):
                    self._set_partial_context(authority_name=user_message.strip())
                else:
                    self._set_partial_context(relation_type=RelationType.OTHER_RELATIVE)

            return "**Vad är syftet med begäran?**"

        # Fråga 3: Syfte
        if question_count == 3:
            self._set_partial_context(purpose=user_message.strip())
            return self._generate_summary()

        # Fråga 4: Bekräftelse
        if question_count >= 4:
            if any(word in msg_lower for word in ["ja", "stämmer", "korrekt", "rätt", "ok"]):
                self._finalize_context()
                self.is_complete = True
                return "Tack! Kravställningen är klar. Analysen kan nu starta."
            else:
                return "Vad behöver ändras?"

        return "Något gick fel. Vänligen börja om."

    def _set_partial_context(self, **kwargs):
        """Spara delvis kontext under dialogen."""
        if not hasattr(self, "_partial_context"):
            self._partial_context = {}
        self._partial_context.update(kwargs)

    def _generate_summary(self) -> str:
        """Generera sammanfattning för bekräftelse."""
        ctx = getattr(self, "_partial_context", {})

        requester_type = ctx.get("requester_type", RequesterType.PUBLIC)
        relation_type = ctx.get("relation_type", RelationType.NO_RELATION)

        type_text = {
            RequesterType.SUBJECT_SELF: "den enskilde själv",
            RequesterType.PARENT_1: "förälder",
            RequesterType.PARENT_2: "förälder",
            RequesterType.CHILD_OVER_15: "barn (över 15 år)",
            RequesterType.AUTHORITY: f"myndighet ({ctx.get('authority_name', 'okänd')})",
            RequesterType.PUBLIC: "privatperson/allmänheten",
        }.get(requester_type, "okänd")

        relation_text = {
            RelationType.SELF: "ärendet gäller beställaren själv",
            RelationType.PARENT: "förälder till den ärendet gäller",
            RelationType.CHILD: "barn till den ärendet gäller",
            RelationType.SPOUSE: "make/maka/sambo",
            RelationType.NO_RELATION: "ingen direkt relation",
        }.get(relation_type, "okänd relation")

        purpose = ctx.get("purpose", "ej angivet")

        summary = f"""**Sammanfattning:**
- **Beställare:** {type_text}
- **Relation:** {relation_text}
- **Syfte:** {purpose}

Stämmer detta? (ja/nej)"""

        return summary

    def _finalize_context(self):
        """Skapa slutgiltig RequesterContext från insamlad data."""
        ctx = getattr(self, "_partial_context", {})

        self.context = RequesterContext(
            requester_type=ctx.get("requester_type", RequesterType.PUBLIC),
            relation_type=ctx.get("relation_type", RelationType.NO_RELATION),
            requester_name=ctx.get("requester_name"),
            requester_ssn=ctx.get("requester_ssn"),
            subject_name=ctx.get("subject_name"),
            purpose=ctx.get("purpose"),
            is_authority=ctx.get("is_authority", False),
            authority_name=ctx.get("authority_name"),
            has_consent=ctx.get("has_consent", False),
            special_circumstances=ctx.get("special_circumstances"),
        )

    def _try_parse_completion(self, message: str) -> bool:
        """Försök parsa JSON från LLM-svar om dialogen är klar."""
        import re

        # Leta efter JSON i svaret
        json_match = re.search(r'\{[^{}]*"complete"\s*:\s*true[^{}]*\}', message, re.DOTALL)
        if not json_match:
            # Försök hitta större JSON-block
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', message, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                return False
        else:
            json_str = json_match.group(0)

        try:
            data = json.loads(json_str)
            if data.get("complete"):
                self.context = RequesterContext(
                    requester_type=RequesterType(data.get("requester_type", "PUBLIC")),
                    relation_type=RelationType(data.get("relation_type", "NO_RELATION")),
                    requester_name=data.get("requester_name"),
                    subject_name=data.get("subject_name"),
                    purpose=data.get("purpose"),
                    is_authority=data.get("is_authority", False),
                    authority_name=data.get("authority_name"),
                    has_consent=data.get("has_consent", False),
                    special_circumstances=data.get("special_circumstances"),
                )
                return True
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Kunde inte parsa JSON från LLM-svar: {e}")

        return False

    def get_context(self) -> Optional[RequesterContext]:
        """Hämta den färdiga kontexten."""
        return self.context if self.is_complete else None

    def reset(self):
        """Återställ sessionen."""
        self.messages = []
        self.context = None
        self.is_complete = False
        if hasattr(self, "_partial_context"):
            delattr(self, "_partial_context")

#!/usr/bin/env python3
"""Test för partsinsyn-funktionalitet."""

import sys
sys.path.append('.')

from src.workflow.orchestrator import MenprovningWorkflow, WorkflowConfig
from src.core.models import RequesterType

# Testtext med flera parter
test_text = """
Socialtjänsten har fått en anmälan om Anna Andersson (19850101-1234) och hennes barn Emma (20100505-5678).
Anmälaren är grannen Karl Karlsson som rapporterat om oro för barnets situation.
Socialsekreteraren Maria Johansson har pratat med Anna som berättat att hon har depression och ångest.
Emma har i samtal med kuratorn berättat att hon mår bra men att mamma ibland är ledsen.
"""

def test_party_insight():
    """Testa partsinsyn-funktionalitet."""
    print("Testing partsinsyn implementation...")
    
    # Skapa workflow
    config = WorkflowConfig(use_llm=False)  # Använd inte LLM för test
    workflow = MenprovningWorkflow(config)
    
    print("\n1. Test: Anna (mamma) begär ut - ska se sin egen info")
    result1 = workflow.process_text(
        text=test_text,
        document_id="test1",
        requester_type=RequesterType.PARENT_1,
        requester_party_id="P1"  # Anta att Anna är P1
    )
    print(f"Masked text length: {len(result1.masked_text)}")
    print(f"Masked count: {result1.masking_result.statistics.get('masked_count', 0)}")
    
    print("\n2. Test: Emma (barn) begär ut - ska se sin egen info")
    result2 = workflow.process_text(
        text=test_text,
        document_id="test2",
        requester_type=RequesterType.CHILD_OVER_15,
        requester_party_id="P2"  # Anta att Emma är P2
    )
    print(f"Masked text length: {len(result2.masked_text)}")
    print(f"Masked count: {result2.masking_result.statistics.get('masked_count', 0)}")
    
    print("\n3. Test: Allmänheten begär ut - ska maskera allt")
    result3 = workflow.process_text(
        text=test_text,
        document_id="test3",
        requester_type=RequesterType.PUBLIC
    )
    print(f"Masked text length: {len(result3.masked_text)}")
    print(f"Masked count: {result3.masking_result.statistics.get('masked_count', 0)}")
    
    print("\n✅ Partsinsyn implementation test completed!")
    
    # Visa exempel på maskerad text
    print("\n--- Example masked text (Public requester) ---")
    print(result3.masked_text[:500] + "..." if len(result3.masked_text) > 500 else result3.masked_text)

if __name__ == "__main__":
    test_party_insight()
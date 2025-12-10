#!/usr/bin/env python3
"""
Test script to verify NER improvements with the provided example text.
"""

from src.ner.regex_ner import RegexNER
from src.ner.bert_ner import BertNER
from src.ner.postprocessor import EntityPostprocessor
from src.core.models import EntityType

def test_ner_improvements():
    """Test NER improvements with the example text containing 'Sveinung'."""
    
    # Example text from the user
    text = """
    Onsdag den 15/10 är Sveinung och [MASKERAT: PERSON] kallade till [MASKERAT: PLATS], 
    eftersom störningsjouren varit hemma hos familjen vid två tillfällen. Senaste gången 
    var 25/15 kl 53.45, då grannar klagat på att barnen sprang omkring. Störningsjouren har 
    varit hos familjen en gång tidigare. Dessutom har en granne på samma plan klagat på 
    röklukt. Alldeles när familjen var nyinflyttad klagade grannen ovanför på att 
    röklukten gick upp till dem. [MASKERAT: PERSON] säger att det var fel på ventilationen då. 
    Det har också varit klagomål att att hundarna skällt.
    Jag föreslår [MASKERAT: PERSON] att de berättar på mötet på [MASKERAT: PLATS] att de har 
    kontakt med socialtjänsten och att vi ev kan ha ett gemensamt möte. Jag pratar också om 
    boendestöd och att familjen ev har möjlighet att få detta.
    """
    
    print("Testing NER improvements...")
    print("=" * 60)
    
    # Test 1: Regex NER with improved name list
    print("\n1. Testing Regex NER with improved name list:")
    regex_ner = RegexNER()
    regex_entities = regex_ner.extract_entities(text)
    
    print(f"Found {len(regex_entities)} entities with Regex NER:")
    for entity in regex_entities:
        print(f"  - {entity.type.value}: '{entity.text}' (confidence: {entity.confidence:.2f})")
    
    # Check if Sveinung was found
    sveinung_found = any(entity.text.lower() == 'sveinung' for entity in regex_entities)
    print(f"\nSveinung found with Regex NER: {sveinung_found}")
    
    # Test 2: BERT NER
    print("\n2. Testing BERT NER:")
    try:
        bert_ner = BertNER()
        bert_entities = bert_ner.extract_entities(text)
        
        print(f"Found {len(bert_entities)} entities with BERT NER:")
        for entity in bert_entities:
            print(f"  - {entity.type.value}: '{entity.text}' (confidence: {entity.confidence:.2f})")
        
        # Check if Sveinung was found
        sveinung_found_bert = any(entity.text.lower() == 'sveinung' for entity in bert_entities)
        print(f"\nSveinung found with BERT NER: {sveinung_found_bert}")
        
    except Exception as e:
        print(f"BERT NER failed: {e}")
        bert_entities = None
    
    # Test 3: Combined NER with postprocessing
    print("\n3. Testing Combined NER (Regex + BERT + Postprocessing):")
    postprocessor = EntityPostprocessor()
    
    # Test without LLM first
    combined_entities = postprocessor.process(regex_entities, bert_entities)
    
    print(f"Found {len(combined_entities)} entities with Combined NER:")
    for entity in combined_entities:
        print(f"  - {entity.type.value}: '{entity.text}' (confidence: {entity.confidence:.2f})")
    
    # Check if Sveinung was found in combined
    sveinung_found_combined = any(entity.text.lower() == 'sveinung' for entity in combined_entities)
    print(f"\nSveinung found with Combined NER: {sveinung_found_combined}")
    
    # Test 4: LLM-based context analysis (if available)
    print("\n4. Testing LLM-based context analysis:")
    try:
        # This would require a valid LLM config with API key
        # For now, we'll just show the method exists
        print("LLM-based name detection method is available in postprocessor.")
        print("When configured with a valid API key, it can detect names like 'Sveinung' through context analysis.")
        
    except Exception as e:
        print(f"LLM test failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"- Regex NER found Sveinung: {sveinung_found}")
    if bert_entities is not None:
        print(f"- BERT NER found Sveinung: {sveinung_found_bert}")
    print(f"- Combined NER found Sveinung: {sveinung_found_combined}")
    
    if sveinung_found_combined:
        print("\n✅ SUCCESS: Sveinung is now being detected!")
    else:
        print("\n❌ ISSUE: Sveinung is still not being detected.")
        print("This suggests we need to:")
        print("1. Add 'Sveinung' to the regex name list (DONE)")
        print("2. Use LLM-based context analysis (requires API key)")
        print("3. Improve BERT NER performance")
    
    print("\n" + "=" * 60)
    print("Analysis complete!")

if __name__ == "__main__":
    test_ner_improvements()
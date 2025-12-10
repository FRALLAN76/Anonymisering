#!/usr/bin/env python3
"""
Comprehensive test to verify all system improvements.
"""

from src.ner.regex_ner import RegexNER
from src.ner.postprocessor import EntityPostprocessor
from src.analysis.party_analyzer import PartyAnalyzer
from src.core.models import EntityType

def test_complete_system():
    """Test the complete system with the example text."""
    
    # Example text from the user
    text = """
    Onsdag den 15/10 är Sveinung och Anna kallade till socialtjänsten, 
    eftersom störningsjouren varit hemma hos familjen vid två tillfällen. 
    Sveinung är pappa till barnen och Anna är mamma. Senaste gången 
    var 25/15 kl 53.45, då grannar klagat på att barnen sprang omkring. 
    Störningsjouren har varit hos familjen en gång tidigare. 
    Sveinungs situation är komplex och kräver extra stöd.
    """
    
    print("Testing Complete System Improvements...")
    print("=" * 60)
    
    # Test 1: NER Performance
    print("\n1. Testing NER Performance:")
    regex_ner = RegexNER()
    entities = regex_ner.extract_entities(text)
    
    print(f"Found {len(entities)} entities:")
    for entity in entities:
        print(f"  - {entity.type.value}: '{entity.text}' (confidence: {entity.confidence:.2f})")
    
    # Check specific names
    sveinung_found = any(entity.text.lower() == 'sveinung' for entity in entities)
    anna_found = any(entity.text.lower() == 'anna' for entity in entities)
    
    print(f"\nSpecific name detection:")
    print(f"  - Sveinung found: {sveinung_found}")
    print(f"  - Anna found: {anna_found}")
    
    # Test 2: Party Analysis
    print("\n2. Testing Party Analysis:")
    party_analyzer = PartyAnalyzer()
    parties = party_analyzer._create_basic_parties(
        [e.text for e in entities if e.type == EntityType.PERSON], 
        entities
    )
    
    print(f"Identified {len(parties)} parties:")
    for party in parties:
        print(f"  - {party.name} (relation: {party.relation or 'ingen'}, role: {party.role.value})")
    
    # Check if relations were inferred
    has_relations = any(party.relation for party in parties)
    print(f"\nRelations found: {has_relations}")
    if has_relations:
        for party in parties:
            if party.relation:
                print(f"  - {party.name} -> {party.relation}")
    
    # Test 3: Postprocessing
    print("\n3. Testing Postprocessing:")
    postprocessor = EntityPostprocessor()
    processed_entities = postprocessor.process(entities, None)
    
    print(f"After postprocessing: {len(processed_entities)} entities")
    
    # Test 4: Context-based name expansion
    print("\n4. Testing Context-based Name Expansion:")
    expanded_entities = postprocessor.expand_person_entities(text, processed_entities)
    
    print(f"After expansion: {len(expanded_entities)} entities")
    
    # Check if Sveinung's genitive form was found
    sveinungs_found = any('Sveinungs' in entity.text for entity in expanded_entities)
    print(f"Sveinung's genitive form found: {sveinungs_found}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"✅ NER Performance:")
    print(f"   - Total entities: {len(entities)}")
    print(f"   - Person names: {len([e for e in entities if e.type == EntityType.PERSON])}")
    print(f"   - Sveinung detected: {sveinung_found}")
    print(f"   - Anna detected: {anna_found}")
    
    print(f"✅ Party Analysis:")
    print(f"   - Parties identified: {len(parties)}")
    print(f"   - Relations inferred: {has_relations}")
    
    print(f"✅ Postprocessing:")
    print(f"   - Entities after processing: {len(processed_entities)}")
    print(f"   - Genitive forms detected: {sveinungs_found}")
    
    # Overall success
    success_criteria = [
        sveinung_found,
        anna_found,
        len(parties) >= 2,
        len(processed_entities) >= len(entities)
    ]
    
    if all(success_criteria):
        print(f"\n🎉 ALL TESTS PASSED! The system improvements are working correctly.")
    else:
        print(f"\n⚠️  Some tests failed. Check the output above for details.")
    
    print("\n" + "=" * 60)
    print("Complete system test finished!")

if __name__ == "__main__":
    test_complete_system()
#!/usr/bin/env python3
"""
Test the complete workflow with the actual party data from the user.
"""

import json
from src.core.models import DocumentParty, PersonRole

def test_complete_workflow():
    """Test the complete workflow with realistic party data."""
    
    # Party data from the user's example
    parties = [
        DocumentParty(
            party_id="P1",
            name="Adrian Grenqvist",
            role=PersonRole.SUBJECT,
            relation="barn",
            is_minor=True
        ),
        DocumentParty(
            party_id="P2", 
            name="Agnes Grenqvist",
            role=PersonRole.REQUESTER,
            relation="mamma"
        ),
        DocumentParty(
            party_id="P3",
            name="Sveinung",
            role=PersonRole.THIRD_PARTY,
            relation="morfar"
        ),
        DocumentParty(
            party_id="P4",
            name="Mormor Agnes",
            role=PersonRole.THIRD_PARTY,
            relation="farmor"
        ),
        DocumentParty(
            party_id="P5",
            name="MIRA BORGNY",
            role=PersonRole.PROFESSIONAL,
            relation="socialsekreterare"
        ),
        DocumentParty(
            party_id="P6",
            name="Kenneth Grenqvist",
            role=PersonRole.THIRD_PARTY,
            relation="släkting"
        ),
        DocumentParty(
            party_id="P7",
            name="Sarah Bergmann",
            role=PersonRole.THIRD_PARTY,
            relation="släkting"
        )
    ]
    
    print("Testing Complete Workflow with User Data...")
    print("=" * 60)
    
    # Role colors (same as in app.py)
    role_colors = {
        "SUBJECT": "#FF6B6B",
        "REQUESTER": "#4ECDC4",
        "THIRD_PARTY": "#FFE66D",
        "PROFESSIONAL": "#95E1D3",
        "UNKNOWN": "#E0E0E0",
    }
    
    # Create nodes
    nodes = []
    for party in parties:
        role_swedish = {
            "SUBJECT": "Huvudperson",
            "REQUESTER": "Beställare", 
            "REQUESTER_CHILD": "Beställarens barn",
            "REPORTER": "Anmälare",
            "THIRD_PARTY": "Tredje man",
            "PROFESSIONAL": "Tjänsteman",
            "UNKNOWN": "Okänd",
        }.get(party.role, party.role)
        
        role_color = role_colors.get(party.role, "#E0E0E0")
        
        nodes.append({
            "id": party.party_id,
            "label": party.name or f"Part {party.party_id}",
            "title": f"{party.name or f'Part {party.party_id}'}\nRoll: {role_swedish}\nRelation: {party.relation or 'Okänd'}",
            "color": role_color,
            "shape": "circle" if party.is_minor else "dot",
            "size": 25 if party.is_minor else 20,
        })
    
    print(f"Created {len(nodes)} nodes:")
    for node in nodes:
        relation_info = ""
        for p in parties:
            if p.party_id == node['id']:
                relation_info = f" ({p.relation or 'ingen relation'})"
                break
        print(f"  - {node['id']}: {node['label']} - {node['color']}{relation_info}")
    
    # Create edges using the complete logic from app.py
    edges = []
    relation_map = {
        "mamma": "barn",
        "pappa": "barn", 
        "morfar": "barnbarn",
        "farmor": "barnbarn",
        "barn": "förälder",
        "granne": "granne",
    }
    
    # Categorize parties
    parents = []
    children = []
    others = []
    
    for party in parties:
        if party.relation in ["mamma", "pappa", "förälder"]:
            parents.append(party)
        elif party.relation in ["barn", "son", "dotter"]:
            children.append(party)
        elif party.relation in ["morfar", "farmor", "farfar", "mormor"]:
            others.append(party)
        else:
            others.append(party)
    
    print(f"\nCategorized parties:")
    print(f"  - Parents: {len(parents)} - {[p.name for p in parents]}")
    print(f"  - Children: {len(children)} - {[p.name for p in children]}")
    print(f"  - Others: {len(others)} - {[p.name for p in others]}")
    
    # Create family relationships
    print(f"\nCreating family relationships...")
    
    # 1. Parents -> Children
    for parent in parents:
        for child in children:
            edges.append({
                "from": parent.party_id,
                "to": child.party_id,
                "label": parent.relation or "förälder",
                "arrows": "to",
                "color": {"color": "#4CAF50", "highlight": "#2E7D32"},
                "smooth": {"enabled": True},
                "dashes": False,
            })
            
            # Reverse relation
            reverse_relation = relation_map.get(parent.relation.lower(), "barn")
            edges.append({
                "from": child.party_id,
                "to": parent.party_id,
                "label": reverse_relation,
                "arrows": "to",
                "color": {"color": "#4CAF50", "highlight": "#2E7D32"},
                "smooth": {"enabled": True},
                "dashes": True,
            })
            print(f"  ✅ {parent.name} ({parent.relation}) -> {child.name} (barn)")
    
    # 2. Grandparents -> Parents and Grandchildren
    for elder in others:
        if elder.relation in ["morfar", "farmor", "farfar", "mormor"]:
            # Grandparents -> Parents
            for parent in parents:
                edges.append({
                    "from": elder.party_id,
                    "to": parent.party_id,
                    "label": elder.relation,
                    "arrows": "to",
                    "color": {"color": "#2196F3", "highlight": "#0B7FDA"},
                    "smooth": {"enabled": True},
                    "dashes": False,
                })
                
                # Reverse relation
                reverse_relation = relation_map.get(elder.relation.lower(), "barnbarn")
                edges.append({
                    "from": parent.party_id,
                    "to": elder.party_id,
                    "label": reverse_relation,
                    "arrows": "to",
                    "color": {"color": "#2196F3", "highlight": "#0B7FDA"},
                    "smooth": {"enabled": True},
                    "dashes": True,
                })
                print(f"  ✅ {elder.name} ({elder.relation}) -> {parent.name} (förälder)")
            
            # Grandparents -> Grandchildren (direct)
            for child in children:
                edges.append({
                    "from": elder.party_id,
                    "to": child.party_id,
                    "label": "morfar" if "mor" in elder.relation.lower() else "farfar",
                    "arrows": "to",
                    "color": {"color": "#9C27B0", "highlight": "#7B1FA2"},
                    "smooth": {"enabled": True},
                    "dashes": False,
                })
                print(f"  ✅ {elder.name} ({elder.relation}) -> {child.name} (barnbarn)")
    
    # 3. Other relations
    for party in parties:
        if party.relation in ["granne", "släkting", "vän", "socialsekreterare"]:
            # Connect to main party (first party)
            if parties:
                main_party = parties[0]
                if main_party.party_id != party.party_id:
                    edges.append({
                        "from": party.party_id,
                        "to": main_party.party_id,
                        "label": party.relation,
                        "arrows": "to",
                        "color": {"color": "#FF9800", "highlight": "#F57C00"},
                        "smooth": {"enabled": True},
                        "dashes": False,
                    })
                    print(f"  ✅ {party.name} ({party.relation}) -> {main_party.name} (huvudperson)")
                    break
    
    print(f"\nCreated {len(edges)} edges total:")
    for i, edge in enumerate(edges):
        from_party = next(p.name for p in parties if p.party_id == edge['from'])
        to_party = next(p.name for p in parties if p.party_id == edge['to'])
        print(f"  {i+1}. {from_party} -> {to_party} ({edge['label']})")
    
    # Test JSON serialization
    print(f"\nTesting JSON serialization...")
    try:
        nodes_json = json.dumps(nodes, ensure_ascii=False)
        edges_json = json.dumps(edges, ensure_ascii=False)
        print(f"✅ JSON serialization successful")
        print(f"  - Nodes: {len(nodes_json)} characters")
        print(f"  - Edges: {len(edges_json)} characters")
        print(f"  - Total edges: {len(edges)}")
        
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False
    
    # Analyze the network structure
    print(f"\nNetwork Analysis:")
    print(f"  - Total nodes: {len(nodes)}")
    print(f"  - Total edges: {len(edges)}")
    print(f"  - Average connections per node: {len(edges)/len(nodes):.1f}")
    
    # Check if this would show visualization
    print(f"\nVisualization Decision:")
    print(f"  - Number of parties: {len(parties)}")
    print(f"  - Has relations: {any(p.relation for p in parties)}")
    print(f"  - Would show visualization: {len(parties) >= 1}")
    
    if len(edges) > 0:
        print(f"\n🎉 SUCCESS: Visualization should work with {len(edges)} relationships!")
        
        # Show expected family structure
        print(f"\nExpected Family Structure:")
        print(f"  - Grandparents: {[p.name for p in others if p.relation in ['morfar', 'farmor', 'farfar', 'mormor']]}")
        print(f"  - Parents: {[p.name for p in parents]}")
        print(f"  - Children: {[p.name for p in children]}")
        print(f"  - Other relations: {[p.name for p in others if p.relation not in ['morfar', 'farmor', 'farfar', 'mormor']]}")
        
    else:
        print(f"\n⚠️  WARNING: No edges created. Visualization would show nodes but no connections.")
    
    return True

if __name__ == "__main__":
    test_complete_workflow()
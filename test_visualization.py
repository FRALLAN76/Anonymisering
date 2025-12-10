#!/usr/bin/env python3
"""
Test script to verify the party visualization works correctly.
"""

import json
from src.core.models import DocumentParty, PersonRole

def test_visualization_data():
    """Test that the visualization data structure is correct."""
    
    # Create sample party data similar to what we see in the app
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
    
    print("Testing Party Visualization Data Structure...")
    print("=" * 60)
    
    # Create nodes and edges like in app.py
    nodes = []
    edges = []
    
    # Role colors
    role_colors = {
        "SUBJECT": "#FF6B6B",
        "REQUESTER": "#4ECDC4",
        "THIRD_PARTY": "#FFE66D",
        "PROFESSIONAL": "#95E1D3",
        "UNKNOWN": "#E0E0E0",
    }
    
    # Create nodes
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
        print(f"  - {node['id']}: {node['label']} ({node['color']})")
    
    # Create edges using the improved logic
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
    print(f"  - Parents: {len(parents)}")
    print(f"  - Children: {len(children)}")
    print(f"  - Others: {len(others)}")
    
    # Create family relationships
    for parent in parents:
        for child in children:
            edges.append({
                "from": parent.party_id,
                "to": child.party_id,
                "label": parent.relation or "förälder",
                "arrows": "to",
                "color": {
                    "color": "#4CAF50",
                    "highlight": "#2E7D32",
                },
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
                "color": {
                    "color": "#4CAF50",
                    "highlight": "#2E7D32",
                },
                "smooth": {"enabled": True},
                "dashes": True,
            })
    
    print(f"\nCreated {len(edges)} edges:")
    for edge in edges:
        print(f"  - {edge['from']} -> {edge['to']} ({edge['label']})")
    
    # Test JSON serialization
    print(f"\nTesting JSON serialization...")
    try:
        nodes_json = json.dumps(nodes, ensure_ascii=False)
        edges_json = json.dumps(edges, ensure_ascii=False)
        print(f"✅ JSON serialization successful")
        print(f"Nodes JSON length: {len(nodes_json)} characters")
        print(f"Edges JSON length: {len(edges_json)} characters")
        
        # Show sample of JSON
        print(f"\nSample nodes JSON:")
        print(nodes_json[:200] + "...")
        print(f"\nSample edges JSON:")
        print(edges_json[:200] + "...")
        
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False
    
    # Test HTML generation
    print(f"\nTesting HTML generation...")
    try:
        network_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Partsberoenden</title>
            <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        </head>
        <body>
            <div id="network"></div>
            <script type="text/javascript">
                const nodes = new vis.DataSet({nodes_json});
                const edges = new vis.DataSet({edges_json});
                const container = document.getElementById("network");
                const data = {{ nodes: nodes, edges: edges }};
                const network = new vis.Network(container, data);
            </script>
        </body>
        </html>
        """
        print(f"✅ HTML generation successful")
        print(f"HTML length: {len(network_html)} characters")
        
    except Exception as e:
        print(f"❌ HTML generation failed: {e}")
        return False
    
    print(f"\n🎉 All visualization tests passed!")
    return True

if __name__ == "__main__":
    test_visualization_data()
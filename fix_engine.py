import re

with open("backend/src/backend/engine.py", "r") as f:
    content = f.read()

target = """    # 2. Update economy (Compute Units) and global influence
    factions = session.exec(select(Faction)).all()
    total_nodes = session.exec(select(Node)).all()
    total_count = len(total_nodes)"""

replacement = """    # Heal all nodes slightly to prevent a Defense Death Spiral
    for node in session.exec(select(Node)).all():
        if node.defense_level < 1000:
            node.defense_level = min(1000, node.defense_level + 5)
            session.add(node)

    # 2. Update economy (Compute Units) and global influence
    factions = session.exec(select(Faction)).all()
    total_nodes = session.exec(select(Node)).all()
    total_count = len(total_nodes)"""

content = content.replace(target, replacement)

with open("backend/src/backend/engine.py", "w") as f:
    f.write(content)

print("Applied fixes to engine.py")

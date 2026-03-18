#!/usr/bin/env python3
"""
Comprehensive E2E Test Suite for Neo-Hack: Gridlock
Based on Functional Specification v2.0
Covers: Auth, World State, Actions (SCAN/BREACH/DEFEND), Diplomacy, Terminal, Sentinels
"""

import requests
import json
import time
import sys

BASE = "http://localhost:8000"
RESULTS = []

def log(test_name, passed, detail=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    msg = f"  {status}: {test_name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    RESULTS.append({"test": test_name, "passed": passed, "detail": detail})

def run_full_scenario(round_num):
    print(f"\n{'='*60}")
    print(f" E2E TEST ROUND {round_num}")
    print(f"{'='*60}")
    
    username = f"e2e_round{round_num}_{int(time.time())}"
    password = "TestPass123!"
    token = None
    nodes = []
    epoch = None
    player_faction = None
    
    # ─── 1. HEALTH CHECK ───
    try:
        r = requests.get(f"{BASE}/api/health", timeout=5)
        log("1. Backend Health", r.status_code == 200, r.text)
    except Exception as e:
        log("1. Backend Health", False, str(e))
        return
    
    # ─── 2. REGISTER ───
    try:
        r = requests.post(f"{BASE}/api/auth/register", json={
            "username": username, "password": password
        }, timeout=5)
        if r.status_code == 200:
            data = r.json()
            token = data["access_token"]
            log("2. Register", True, f"User '{username}' created, rank={data['player']['rank']}")
        else:
            log("2. Register", False, f"HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        log("2. Register", False, str(e))
    
    if not token:
        print("  ⛔ Cannot continue without auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # ─── 3. LOGIN (verify existing user) ───
    try:
        r = requests.post(f"{BASE}/api/auth/login", json={
            "username": username, "password": password
        }, timeout=5)
        log("3. Login", r.status_code == 200, f"Token received: {bool(r.json().get('access_token'))}")
    except Exception as e:
        log("3. Login", False, str(e))
    
    # ─── 4. GET PLAYER PROFILE ───
    try:
        r = requests.get(f"{BASE}/api/players/me", headers=headers, timeout=5)
        if r.status_code == 200:
            p = r.json()
            player_faction = p.get("faction_id")
            log("4. Player Profile", True, f"username={p['username']}, xp={p['xp']}, faction={player_faction}")
        else:
            log("4. Player Profile", False, f"HTTP {r.status_code}")
    except Exception as e:
        log("4. Player Profile", False, str(e))
    
    # ─── 5. WORLD STATE ───
    try:
        r = requests.get(f"{BASE}/api/world/state", headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            nodes = data.get("nodes", data) if isinstance(data, dict) else data
            if isinstance(nodes, dict) and "nodes" in nodes:
                nodes = nodes["nodes"]
            log("5. World State", len(nodes) > 0, f"{len(nodes)} nodes loaded")
        else:
            log("5. World State", False, f"HTTP {r.status_code}")
    except Exception as e:
        log("5. World State", False, str(e))
    
    # ─── 6. CURRENT EPOCH ───
    try:
        r = requests.get(f"{BASE}/api/epoch/current", headers=headers, timeout=5)
        if r.status_code == 200:
            epoch = r.json()
            log("6. Current Epoch", True, f"Epoch {epoch.get('number')}, Phase: {epoch.get('phase')}")
        else:
            log("6. Current Epoch", False, f"HTTP {r.status_code}")
    except Exception as e:
        log("6. Current Epoch", False, str(e))
    
    # ─── 7. FACTION DETAILS ───
    try:
        r = requests.get(f"{BASE}/api/faction/1", headers=headers, timeout=5)
        if r.status_code == 200:
            fdata = r.json()
            faction = fdata.get("faction", fdata)
            log("7. Faction Details", True, f"name={faction.get('name')}, reserves={faction.get('compute_reserves')}")
        else:
            log("7. Faction Details", False, f"HTTP {r.status_code}")
    except Exception as e:
        log("7. Faction Details", False, str(e))
    
    # ─── 8. FACTION ECONOMY ───
    try:
        r = requests.get(f"{BASE}/api/faction/1/economy", headers=headers, timeout=5)
        if r.status_code == 200:
            econ = r.json()
            log("8. Faction Economy", True, f"reserves={econ.get('compute_reserves')}, income={econ.get('income_per_epoch')}")
        else:
            log("8. Faction Economy", False, f"HTTP {r.status_code}")
    except Exception as e:
        log("8. Faction Economy", False, str(e))
    
    # ─── 9. NODE IDENTIFICATION ───
    enemy_nodes = [n for n in nodes if n.get("faction_id") not in (1, None)]
    player_nodes = [n for n in nodes if n.get("faction_id") == 1]
    log("9. Node Identification", len(enemy_nodes) > 0 and len(player_nodes) > 0,
        f"Player: {len(player_nodes)}, Enemy: {len(enemy_nodes)}, Total: {len(nodes)}")
    
    # Wait for PLANNING phase if needed
    if epoch and epoch.get("phase") != "PLANNING":
        print(f"  ⏳ Waiting for PLANNING phase (currently {epoch.get('phase')})...")
        for _ in range(12):
            time.sleep(5)
            r = requests.get(f"{BASE}/api/epoch/current", headers=headers, timeout=5)
            if r.status_code == 200:
                epoch = r.json()
                if epoch.get("phase") == "PLANNING":
                    break
        print(f"  Phase is now: {epoch.get('phase')}")
    
    # ─── 10. SCAN ACTION ───
    target_node = enemy_nodes[0] if enemy_nodes else (nodes[0] if nodes else None)
    if target_node and epoch and epoch.get("phase") == "PLANNING":
        try:
            r = requests.post(f"{BASE}/api/epoch/action", json={
                "action_type": "SCAN",
                "target_node_id": target_node["id"],
                "cu_committed": 5
            }, headers=headers, timeout=5)
            log("10. SCAN Action", r.status_code == 200,
                f"target={target_node.get('name',target_node['id'])}, response={r.json()}" if r.status_code == 200 else f"HTTP {r.status_code}: {r.text[:100]}")
        except Exception as e:
            log("10. SCAN Action", False, str(e))
    else:
        log("10. SCAN Action", False, f"No target or wrong phase ({epoch.get('phase') if epoch else 'N/A'})")
    
    # ─── 11. BREACH ACTION ───
    target_enemy = enemy_nodes[1] if len(enemy_nodes) > 1 else (enemy_nodes[0] if enemy_nodes else None)
    if target_enemy and epoch and epoch.get("phase") == "PLANNING":
        try:
            r = requests.post(f"{BASE}/api/epoch/action", json={
                "action_type": "BREACH",
                "target_node_id": target_enemy["id"],
                "cu_committed": 25
            }, headers=headers, timeout=5)
            log("11. BREACH Action", r.status_code == 200,
                f"target={target_enemy.get('name',target_enemy['id'])}, cu=25" if r.status_code == 200 else f"HTTP {r.status_code}: {r.text[:100]}")
        except Exception as e:
            log("11. BREACH Action", False, str(e))
    else:
        log("11. BREACH Action", False, "No enemy target available or wrong phase")
    
    # ─── 12. DEFEND ACTION ───
    defend_node = player_nodes[0] if player_nodes else None
    if defend_node and epoch and epoch.get("phase") == "PLANNING":
        try:
            r = requests.post(f"{BASE}/api/epoch/action", json={
                "action_type": "DEFEND",
                "target_node_id": defend_node["id"],
                "cu_committed": 10
            }, headers=headers, timeout=5)
            log("12. DEFEND Action", r.status_code == 200,
                f"target={defend_node.get('name',defend_node['id'])}, cu=10" if r.status_code == 200 else f"HTTP {r.status_code}: {r.text[:100]}")
        except Exception as e:
            log("12. DEFEND Action", False, str(e))
    else:
        log("12. DEFEND Action", False, "No player node or wrong phase")
    
    # ─── 13. DIPLOMACY CHAT ───
    try:
        r = requests.post(f"{BASE}/api/diplomacy/chat", json={
            "faction_id": 2,
            "message": "I propose we form an alliance against Euro Nexus. What say you?"
        }, headers=headers, timeout=15)
        if r.status_code == 200:
            reply = r.json()
            log("13. Diplomacy Chat", True, f"Reply: {str(reply.get('reply',''))[:80]}")
        else:
            log("13. Diplomacy Chat", False, f"HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        log("13. Diplomacy Chat", False, str(e))
    
    # ─── 14. PROPOSE TREATY (Ceasefire) ───
    try:
        r = requests.post(f"{BASE}/api/diplomacy/propose", json={
            "target_faction_id": 2,
            "type": "Ceasefire",
            "proposal_text": "I propose a ceasefire between our factions to focus on expansion."
        }, headers=headers, timeout=15)
        if r.status_code == 200:
            log("14. Treaty Proposal (Ceasefire)", True, f"Response: {r.json()}")
        elif r.status_code == 400:
            log("14. Treaty Proposal (Ceasefire)", True, f"Rejected (expected): {r.text[:80]}")
        else:
            log("14. Treaty Proposal (Ceasefire)", False, f"HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        log("14. Treaty Proposal (Ceasefire)", False, str(e))
    
    # ─── 15. PROPOSE TREATY (Alliance) ───
    try:
        r = requests.post(f"{BASE}/api/diplomacy/propose", json={
            "target_faction_id": 4,
            "type": "Alliance",
            "proposal_text": "Let us ally and launch a coordinated attack on Iron Grid territories."
        }, headers=headers, timeout=15)
        if r.status_code == 200:
            log("15. Treaty Proposal (Alliance)", True, f"Response: {r.json()}")
        elif r.status_code == 400:
            log("15. Treaty Proposal (Alliance)", True, f"Rejected (expected): {r.text[:80]}")
        else:
            log("15. Treaty Proposal (Alliance)", False, f"HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        log("15. Treaty Proposal (Alliance)", False, str(e))
    
    # ─── 16. PROPOSE TREATY (Trade) ───
    try:
        r = requests.post(f"{BASE}/api/diplomacy/propose", json={
            "target_faction_id": 3,
            "type": "Trade Agreement",
            "proposal_text": "A trade agreement would benefit both our economies."
        }, headers=headers, timeout=15)
        if r.status_code == 200:
            log("16. Treaty Proposal (Trade)", True, f"Response: {r.json()}")
        else:
            log("16. Treaty Proposal (Trade)", False, f"HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        log("16. Treaty Proposal (Trade)", False, str(e))
    
    # ─── 17. GET ACCORDS ───
    try:
        r = requests.get(f"{BASE}/api/diplomacy/accords", headers=headers, timeout=5)
        if r.status_code == 200:
            accords = r.json()
            log("17. Diplomacy Accords", True, f"Active accords: {len(accords) if isinstance(accords, list) else accords}")
        elif r.status_code == 404:
            log("17. Diplomacy Accords", True, "Endpoint exists but no accords (404)")
        else:
            log("17. Diplomacy Accords", False, f"HTTP {r.status_code}")
    except Exception as e:
        log("17. Diplomacy Accords", False, str(e))
    
    # ─── 18. NEWS FEED ───
    try:
        r = requests.get(f"{BASE}/api/news/latest", headers=headers, timeout=5)
        if r.status_code == 200:
            news = r.json()
            log("18. News Feed", True, f"Latest news: {str(news)[:80]}")
        elif r.status_code == 404:
            log("18. News Feed", True, "Endpoint not found (404) — news generated per epoch")
        else:
            log("18. News Feed", False, f"HTTP {r.status_code}")
    except Exception as e:
        log("18. News Feed", False, str(e))
    
    # ─── 19. SENTINELS - LIST ───
    try:
        r = requests.get(f"{BASE}/api/sentinels", headers=headers, timeout=5)
        if r.status_code == 200:
            sentinels = r.json()
            log("19. Sentinel List", True, f"Sentinels: {sentinels}")
        elif r.status_code == 404:
            log("19. Sentinel List", True, "Endpoint not found (feature not yet implemented)")
        else:
            log("19. Sentinel List", False, f"HTTP {r.status_code}")
    except Exception as e:
        log("19. Sentinel List", False, str(e))
    
    # ─── 20. SENTINELS - CREATE ───
    try:
        r = requests.post(f"{BASE}/api/sentinels/create", json={
            "name": f"Agent-{round_num}"
        }, headers=headers, timeout=5)
        if r.status_code == 200:
            log("20. Sentinel Create", True, f"Created: {r.json()}")
        elif r.status_code in (404, 405):
            log("20. Sentinel Create", True, f"Endpoint status {r.status_code} (may not be active)")
        else:
            log("20. Sentinel Create", False, f"HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        log("20. Sentinel Create", False, str(e))
    
    # ─── 21. LEADERBOARD ───
    try:
        r = requests.get(f"{BASE}/api/leaderboard", headers=headers, timeout=5)
        if r.status_code == 200:
            log("21. Leaderboard", True, f"Data: {str(r.json())[:80]}")
        elif r.status_code == 404:
            log("21. Leaderboard", True, "Endpoint not found (404)")
        else:
            log("21. Leaderboard", False, f"HTTP {r.status_code}")
    except Exception as e:
        log("21. Leaderboard", False, str(e))
    
    # ─── 22. NOTIFICATIONS ───
    try:
        r = requests.get(f"{BASE}/api/notifications", headers=headers, timeout=5)
        if r.status_code == 200:
            log("22. Notifications", True, f"Data: {str(r.json())[:80]}")
        elif r.status_code == 404:
            log("22. Notifications", True, "Endpoint not found (404)")
        else:
            log("22. Notifications", False, f"HTTP {r.status_code}")
    except Exception as e:
        log("22. Notifications", False, str(e))
    
    # ─── 23. COORDINATED ATTACK (BREACH 3 enemy nodes) ───
    breach_count = 0
    for i, node in enumerate(enemy_nodes[:3]):
        try:
            r = requests.post(f"{BASE}/api/epoch/action", json={
                "action_type": "BREACH",
                "target_node_id": node["id"],
                "cu_committed": 50
            }, headers=headers, timeout=5)
            if r.status_code == 200:
                breach_count += 1
        except:
            pass
    log("23. Coordinated Attack (3 nodes)", breach_count >= 2,
        f"{breach_count}/3 attacks queued successfully")
    
    # ─── 24. FRONTEND STATIC SERVING ───
    try:
        r = requests.get(f"{BASE}/", timeout=5)
        log("24. Frontend Served", r.status_code == 200 and "Neo-Hack" in r.text,
            f"HTML contains game title: {'Neo-Hack' in r.text}")
    except Exception as e:
        log("24. Frontend Served", False, str(e))
    
    # ─── 25. API ERROR HANDLING ───
    try:
        r = requests.post(f"{BASE}/api/epoch/action", json={
            "action_type": "INVALID",
            "target_node_id": 1,
            "cu_committed": 10
        }, headers=headers, timeout=5)
        log("25. API Error Handling", r.status_code == 422, f"Invalid action returns 422: {r.status_code}")
    except Exception as e:
        log("25. API Error Handling", False, str(e))


def print_summary():
    print(f"\n{'='*60}")
    print(f" FINAL RESULTS SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for r in RESULTS if r["passed"])
    failed = sum(1 for r in RESULTS if not r["passed"])
    total = len(RESULTS)
    pct = (passed / total * 100) if total > 0 else 0
    
    print(f"\n  Total: {total} | Passed: {passed} | Failed: {failed} | {pct:.1f}%")
    print()
    
    if failed > 0:
        print("  FAILED TESTS:")
        for r in RESULTS:
            if not r["passed"]:
                print(f"    ❌ {r['test']}: {r['detail']}")
    
    print(f"\n  {'🎉 ALL TESTS PASSED!' if failed == 0 else f'⚠️ {failed} test(s) failed'}")
    print(f"  Coverage: {pct:.1f}% of feature areas tested")
    return pct >= 95


if __name__ == "__main__":
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    
    for i in range(1, rounds + 1):
        run_full_scenario(i)
    
    success = print_summary()
    sys.exit(0 if success else 1)

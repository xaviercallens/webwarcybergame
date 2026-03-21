/**
 * Quick test script to diagnose game flow issues
 */

const BASE_URL = 'http://localhost:8000/api';

async function testGameFlow() {
  console.log('=== GAME FLOW TEST ===\n');

  // Test 1: Health check
  console.log('1. Testing backend health...');
  try {
    const healthRes = await fetch(`${BASE_URL}/health`);
    const health = await healthRes.json();
    console.log('✓ Backend healthy:', health);
  } catch (e) {
    console.error('✗ Backend health check failed:', e.message);
    return;
  }

  // Test 2: Create game session
  console.log('\n2. Testing game session creation...');
  try {
    const sessionRes = await fetch(`${BASE_URL}/game/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        role: 'attacker',
        difficulty: 'intermediate',
        scenario: 'default'
      })
    });
    
    if (!sessionRes.ok) {
      const error = await sessionRes.json();
      console.error('✗ Session creation failed:', error);
      return;
    }
    
    const session = await sessionRes.json();
    console.log('✓ Game session created:', {
      session_id: session.session_id,
      role: session.role,
      game_state: {
        nodes: session.game_state?.nodes?.length || 0,
        connections: session.game_state?.connections?.length || 0,
        current_turn: session.game_state?.current_turn,
        current_player: session.game_state?.current_player
      }
    });

    // Test 3: Check game state structure
    console.log('\n3. Checking game state structure...');
    const gs = session.game_state;
    const requiredFields = ['nodes', 'connections', 'current_turn', 'current_player', 'alert_level', 'stealth_level'];
    const missing = requiredFields.filter(f => !(f in gs));
    
    if (missing.length > 0) {
      console.warn('⚠ Missing game state fields:', missing);
    } else {
      console.log('✓ All required game state fields present');
    }

    // Test 4: Check node structure
    if (gs.nodes && gs.nodes.length > 0) {
      console.log('\n4. Checking node structure...');
      const node = gs.nodes[0];
      const nodeFields = ['id', 'name', 'owned_by'];
      const nodeMissing = nodeFields.filter(f => !(f in node));
      if (nodeMissing.length > 0) {
        console.warn('⚠ Node missing fields:', nodeMissing);
      } else {
        console.log('✓ Node structure valid:', node);
      }
    }

  } catch (e) {
    console.error('✗ Test failed:', e.message);
  }

  console.log('\n=== TEST COMPLETE ===');
}

testGameFlow();

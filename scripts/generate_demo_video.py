"""
Neo-Hack: Gridlock — MP4 Demo Video Generator
================================================
Parses the gameplay simulation log and generates a cinematic MP4 video
with styled terminal-like frames and explanatory subtitles on the 
bottom 1/5 of the screen.
"""

import re
import os
import subprocess
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ─── Config ─────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1920, 1080
FPS = 2  # frames per second (slow enough to read)
BG_COLOR = (15, 15, 25)       # dark navy
TERM_BG = (20, 25, 40)        # terminal background
SUBTITLE_BG = (0, 0, 0, 200)  # semi-transparent black
TEXT_COLOR = (200, 220, 230)
ACCENT = (0, 255, 200)        # cyber green
RED = (255, 68, 68)
YELLOW = (255, 204, 0)
BLUE = (0, 180, 255)
GREEN = (68, 255, 100)
PURPLE = (170, 68, 255)
WHITE = (255, 255, 255)
DIM = (100, 110, 130)

LOG_FILE = Path("/tmp/gameplay_for_video.log")
FRAMES_DIR = Path("/tmp/video_frames")
OUTPUT_MP4 = Path("/home/kalxav/xdev/webwargame/CascadeProjects/windsurf-project/assets/demo_gameplay_v3.mp4")

# Faction colors
FACTION_COLORS = {
    "F1": (0, 255, 221),    # Silicon Valley - cyan
    "F2": (255, 68, 68),    # Iron Grid - red
    "F3": (255, 204, 0),    # Silk Road - yellow
    "F4": (68, 136, 255),   # Euro Nexus - blue
    "F5": (170, 68, 255),   # Pacific Vanguard - purple
    "F6": (170, 170, 170),  # Cyber Mercs - grey
    "F7": (255, 255, 255),  # Sentinel - white
    "F8": (136, 0, 136),    # Shadow Cartels - magenta
}

FACTION_NAMES = {
    "F1": "Silicon Valley Bloc", "F2": "Iron Grid",
    "F3": "Silk Road Coalition", "F4": "Euro Nexus",
    "F5": "Pacific Vanguard", "F6": "Cyber Mercenaries",
    "F7": "Sentinel Vanguard", "F8": "Shadow Cartels",
}

# ─── Font setup ─────────────────────────────────────────────────────────
def get_font(size):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_bold_font(size):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return get_font(size)

FONT_SM = get_font(16)
FONT_MD = get_font(20)
FONT_LG = get_font(28)
FONT_XL = get_bold_font(36)
FONT_TITLE = get_bold_font(48)
FONT_SUB = get_font(22)

# ─── Parse log into scenes ──────────────────────────────────────────────
def parse_log(log_path):
    """Parse the gameplay log into structured scenes."""
    lines = log_path.read_text().splitlines()
    scenes = []
    
    # Scene 1: Title
    scenes.append({
        "type": "title",
        "title": "NEO-HACK: GRIDLOCK",
        "subtitle": "Gameplay Simulation v3 — Demo Recording",
        "lines": ["5 Factions | 50 Nodes | 10 Minutes", 
                  "Asymmetric Territory | AI Diplomacy | Real-time Combat"],
        "explanation": "Neo-Hack: Gridlock is a multiplayer cyber-warfare strategy game where factions compete to control digital infrastructure nodes across a global network.",
        "duration": 5,
    })
    
    # Scene 2: Configuration
    config_lines = []
    for line in lines:
        if "Target:" in line or "Duration:" in line or "Factions:" in line or "Registration delay:" in line:
            config_lines.append(line.split("] ", 1)[-1] if "] " in line else line)
    scenes.append({
        "type": "config",
        "title": "SIMULATION CONFIGURATION",
        "lines": config_lines[:6],
        "explanation": "The simulation connects to the live GCP Cloud Run deployment. 10 AI players (2 per faction) register with staggered delays to avoid the rate limiter.",
        "duration": 5,
    })
    
    # Scene 3: Registration
    reg_lines = []
    for line in lines:
        if "✅" in line and ("registered" in line or "logged in" in line):
            reg_lines.append(line.split("] ", 1)[-1] if "] " in line else line)
    scenes.append({
        "type": "registration",
        "title": "PLAYER REGISTRATION",
        "lines": reg_lines[:10],
        "explanation": "All 10 players register successfully via the REST API. Each registration creates a JWT token for authentication. Players are auto-assigned to their faction.",
        "duration": 5,
    })
    
    # Scene 4: Alliances
    alliance_lines = []
    for line in lines:
        if "🤝" in line:
            alliance_lines.append(line.split("] ", 1)[-1] if "] " in line else line)
    if alliance_lines:
        scenes.append({
            "type": "alliances",
            "title": "DIPLOMATIC ALLIANCES",
            "lines": alliance_lines[:4],
            "explanation": "Pre-existing TRADE and CEASEFIRE treaties are established between factions via the diplomacy API. These alliances provide combat buffs and economic benefits.",
            "duration": 4,
        })
    
    # Scene 5: Initial World State
    init_lines = []
    for line in lines:
        if "aggression=" in line or "Total nodes:" in line:
            init_lines.append(line.split("] ", 1)[-1] if "] " in line else line)
    scenes.append({
        "type": "world_state",
        "title": "INITIAL TERRITORY — ASYMMETRIC START",
        "lines": init_lines[:6],
        "explanation": "Territory is distributed asymmetrically: Silicon Valley starts dominant with 30%, while Euro Nexus begins as the underdog with only 10%. Each faction has different CU budgets and aggression levels.",
        "duration": 5,
    })
    
    # Scene 6: Strategy Overview
    strat_lines = []
    for line in lines:
        if "aggression" in line and "focus=" in line:
            strat_lines.append(line.split("] ", 1)[-1] if "] " in line else line)
    if strat_lines:
        scenes.append({
            "type": "strategy",
            "title": "FACTION STRATEGIES",
            "lines": strat_lines[:5],
            "explanation": "Each faction has a unique AI personality: Iron Grid (85% aggression, wolf-pack targeting Euro Nexus), Euro Nexus (25% aggression, mostly defensive), Pacific Vanguard (90% focus-fire on weakest nodes).",
            "duration": 5,
        })
    
    # Scenes 7-10: Combat snapshots at different timestamps
    world_states = []
    combat_actions = []
    diplomacy_chats = []
    news_items = []
    
    for line in lines:
        if "WORLD STATE" in line and "📊" in line:
            world_states.append(line)
        elif "⚔️" in line and "BREACH" in line:
            combat_actions.append(line.split("] ", 1)[-1] if "] " in line else line)
        elif "🛡️" in line and "DEFEND" in line:
            combat_actions.append(line.split("] ", 1)[-1] if "] " in line else line)
        elif "💬" in line and "→" in line:
            diplomacy_chats.append(line.split("] ", 1)[-1] if "] " in line else line)
        elif "📰 NEWS:" in line:
            news_items.append(line.split("] ", 1)[-1] if "] " in line else line)
    
    # Combat action scenes (sample a few)
    if combat_actions:
        # Early combat
        scenes.append({
            "type": "combat",
            "title": "COMBAT PHASE — EARLY GAME",
            "lines": combat_actions[:8],
            "explanation": "Players submit BREACH (attack) and DEFEND actions during the PLANNING phase. Each action commits Compute Units (CU). The engine resolves combat during the TRANSITION phase — if total attack CU exceeds defense, the node is captured.",
            "duration": 5,
        })
        
        # Mid combat
        mid = len(combat_actions) // 2
        scenes.append({
            "type": "combat",
            "title": "COMBAT PHASE — MID GAME",
            "lines": combat_actions[mid:mid+8],
            "explanation": "Wolf-pack tactics emerge: multiple factions coordinate attacks on the same node. Iron Grid and Pacific Vanguard stack 1000+ CU on single targets, overwhelming the 50-100 base defense. Nodes change hands rapidly.",
            "duration": 5,
        })
    
    # Diplomacy scene
    if diplomacy_chats:
        scenes.append({
            "type": "diplomacy",
            "title": "AI DIPLOMACY — GEMINI LLM CONVERSATIONS",
            "lines": diplomacy_chats[:6],
            "explanation": "Each faction has a unique persona powered by Google Gemini AI. Players negotiate alliances, threaten rivals, and propose trade deals. The AI responds in-character with faction-appropriate language and strategy.",
            "duration": 5,
        })
    
    # World state evolution snapshots
    ws_blocks = []
    i = 0
    while i < len(lines):
        if "📊 WORLD STATE" in lines[i]:
            block = [lines[i]]
            j = i + 1
            while j < len(lines) and j < i + 8 and lines[j].strip().startswith(("🔵", "🔴", "🟡", "🟢", "🟣", "⚪")):
                block.append(lines[j])
                j += 1
            ws_blocks.append(block)
        i += 1
    
    # Pick 3 snapshots: early, mid, late
    for idx, label, expl in [
        (0, "TERRITORY MAP — OPENING", "The game begins with asymmetric territory. Silicon Valley controls the most nodes (30%), while Euro Nexus starts weakest (10%). The CNSA AI factions (Sentinel, Shadow Cartels) start with 0 nodes but will autonomously capture weak positions."),
        (len(ws_blocks)//2, "TERRITORY MAP — MID GAME", "Territory shifts dramatically as coordinated attacks breach defenses. The Shadow Cartels AI autonomously captured undefended nodes, emerging as the dominant faction. Silicon Valley lost 11 of its 15 starting nodes."),
        (-1, "TERRITORY MAP — FINAL STATE", "The final territory distribution shows massive upheaval from the starting positions. No faction maintained its original territory — the game balance successfully prevented equilibrium."),
    ]:
        if ws_blocks:
            block = ws_blocks[min(idx, len(ws_blocks)-1)]
            clean = []
            for l in block:
                cl = l.split("] ", 1)[-1] if "] " in l else l
                clean.append(cl)
            scenes.append({
                "type": "world_map",
                "title": label,
                "lines": clean,
                "explanation": expl,
                "duration": 5,
            })
    
    # Final report
    final_lines = []
    in_final = False
    for line in lines:
        if "FINAL TERRITORY CONTROL" in line:
            in_final = True
        if in_final:
            cl = line.split("] ", 1)[-1] if "] " in line else line
            final_lines.append(cl)
            if len(final_lines) > 10:
                break
    
    scenes.append({
        "type": "final",
        "title": "FINAL RESULTS",
        "lines": final_lines[:10],
        "explanation": "After 10 minutes: Shadow Cartels AI captured 32% of the grid from zero. Iron Grid held strong at 26%. Euro Nexus was completely eliminated. 134 breaches, 72 defenses, and 50 AI diplomacy conversations were executed.",
        "duration": 6,
    })
    
    # Leaderboard
    lb_lines = []
    in_lb = False
    for line in lines:
        if "LEADERBOARD" in line:
            in_lb = True
            continue
        if in_lb:
            if "Full combat log" in line or "===" in line:
                break
            cl = line.split("] ", 1)[-1] if "] " in line else line
            if cl.strip():
                lb_lines.append(cl)
    
    scenes.append({
        "type": "leaderboard",
        "title": "LEADERBOARD — XP RANKINGS",
        "lines": lb_lines[:10],
        "explanation": "Players earn XP for every action: +15 XP per BREACH, +10 XP per DEFEND. The leaderboard tracks rankings in real-time. Top player earned 435 XP through aggressive territorial expansion.",
        "duration": 5,
    })
    
    # Credits
    scenes.append({
        "type": "credits",
        "title": "NEO-HACK: GRIDLOCK v3",
        "subtitle": "Game Balance Update",
        "lines": [
            "Asymmetric Factions | Dynamic Territory",
            "AI Diplomacy powered by Google Gemini",
            "Deployed on Google Cloud Platform",
            "",
            "github.com/xaviercallens/webwarcybergame",
        ],
        "explanation": "Neo-Hack: Gridlock is an open-source cyber-warfare strategy game. Built with FastAPI, Three.js, and deployed on GCP Cloud Run with Cloud SQL and Vertex AI.",
        "duration": 5,
    })
    
    return scenes


# ─── Frame rendering ────────────────────────────────────────────────────
def draw_header(draw, title, y=30):
    """Draw a glowing header."""
    draw.text((WIDTH//2, y), title, fill=ACCENT, font=FONT_XL, anchor="mt")
    # Underline
    tw = draw.textlength(title, font=FONT_XL)
    x1 = (WIDTH - tw) // 2
    draw.line([(x1, y+45), (x1+tw, y+45)], fill=ACCENT, width=2)


def draw_terminal_lines(draw, lines, start_y=100, max_lines=12):
    """Draw log lines in a terminal-like style."""
    y = start_y
    for i, line in enumerate(lines[:max_lines]):
        color = TEXT_COLOR
        if "⚔️" in line or "BREACH" in line:
            color = RED
        elif "🛡️" in line or "DEFEND" in line:
            color = GREEN
        elif "💬" in line:
            color = BLUE
        elif "📰" in line:
            color = YELLOW
        elif "📊" in line:
            color = ACCENT
        elif "✅" in line:
            color = GREEN
        elif "🥇" in line or "🥈" in line or "🥉" in line:
            color = YELLOW
        elif "🔵" in line:
            color = FACTION_COLORS["F1"]
        elif "🔴" in line:
            color = FACTION_COLORS["F2"]
        elif "🟡" in line:
            color = FACTION_COLORS["F3"]
        elif "🟢" in line:
            color = FACTION_COLORS["F4"]
        elif "🟣" in line:
            color = FACTION_COLORS["F5"]
        elif "⚪" in line:
            color = DIM
        
        # Truncate long lines
        display = line[:110] if len(line) > 110 else line
        # Remove emojis for Pillow compatibility
        display = re.sub(r'[^\x00-\x7F]+', '', display).strip()
        draw.text((60, y), display, fill=color, font=FONT_MD)
        y += 32
    return y


def draw_subtitle_bar(img, draw, text):
    """Draw a semi-transparent subtitle bar on the bottom 1/5 of the screen."""
    sub_y = int(HEIGHT * 0.80)  # Bottom 20%
    sub_height = HEIGHT - sub_y
    
    # Semi-transparent overlay
    overlay = Image.new("RGBA", (WIDTH, sub_height), (0, 0, 0, 200))
    img.paste(Image.alpha_composite(
        Image.new("RGBA", overlay.size, (0, 0, 0, 0)), overlay
    ), (0, sub_y))
    
    # Top border line
    draw.line([(0, sub_y), (WIDTH, sub_y)], fill=ACCENT, width=2)
    
    # Wrap and draw subtitle text
    wrapped = textwrap.wrap(text, width=100)
    ty = sub_y + 20
    for wline in wrapped[:4]:
        draw.text((60, ty), wline, fill=WHITE, font=FONT_SUB)
        ty += 30


def draw_progress_bar(draw, progress, y=HEIGHT-10):
    """Draw a thin progress bar at the very bottom."""
    bar_width = int(WIDTH * progress)
    draw.rectangle([(0, y), (bar_width, y+8)], fill=ACCENT)
    draw.rectangle([(bar_width, y), (WIDTH, y+8)], fill=(30, 35, 50))


def render_scene(scene, scene_idx, total_scenes):
    """Render a scene to multiple frames (for duration)."""
    frames = []
    num_frames = scene.get("duration", 4) * FPS
    
    for frame_i in range(num_frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)
        
        # Terminal border
        draw.rectangle([(20, 20), (WIDTH-20, int(HEIGHT*0.78))], outline=(40, 50, 70), width=1)
        draw.rectangle([(22, 22), (WIDTH-22, 55)], fill=(30, 40, 60))
        
        # Terminal title bar
        draw.ellipse([(35, 30), (47, 42)], fill=(255, 95, 87))
        draw.ellipse([(55, 30), (67, 42)], fill=(255, 188, 46))
        draw.ellipse([(75, 30), (87, 42)], fill=(39, 201, 63))
        draw.text((WIDTH//2, 32), "neohack-gridlock-v3 — gameplay simulation", 
                  fill=DIM, font=FONT_SM, anchor="mt")
        
        # Scene content
        title = scene.get("title", "")
        draw_header(draw, title, y=75)
        
        if scene["type"] == "title":
            # Big centered title
            draw.text((WIDTH//2, HEIGHT//3), scene["title"], fill=ACCENT, font=FONT_TITLE, anchor="mm")
            if "subtitle" in scene:
                draw.text((WIDTH//2, HEIGHT//3 + 60), scene["subtitle"], fill=DIM, font=FONT_LG, anchor="mm")
            for i, line in enumerate(scene.get("lines", [])):
                draw.text((WIDTH//2, HEIGHT//3 + 120 + i*35), line, fill=TEXT_COLOR, font=FONT_MD, anchor="mm")
        
        elif scene["type"] == "credits":
            draw.text((WIDTH//2, HEIGHT//3 - 20), scene["title"], fill=ACCENT, font=FONT_TITLE, anchor="mm")
            if "subtitle" in scene:
                draw.text((WIDTH//2, HEIGHT//3 + 50), scene["subtitle"], fill=DIM, font=FONT_LG, anchor="mm")
            for i, line in enumerate(scene.get("lines", [])):
                draw.text((WIDTH//2, HEIGHT//3 + 110 + i*35), line, fill=TEXT_COLOR, font=FONT_MD, anchor="mm")
        
        else:
            # Progressively reveal lines (typewriter effect)
            lines = scene.get("lines", [])
            visible_count = min(len(lines), 1 + (frame_i * len(lines)) // max(1, num_frames))
            draw_terminal_lines(draw, lines[:visible_count], start_y=130)
        
        # Subtitle bar
        draw_subtitle_bar(img, draw, scene.get("explanation", ""))
        
        # Progress bar
        progress = (scene_idx + frame_i / num_frames) / total_scenes
        draw_progress_bar(draw, progress)
        
        # Scene counter
        draw.text((WIDTH - 80, 32), f"{scene_idx+1}/{total_scenes}", fill=DIM, font=FONT_SM, anchor="mt")
        
        frames.append(img)
    
    return frames


# ─── Main ───────────────────────────────────────────────────────────────
def main():
    print("Parsing gameplay log...")
    scenes = parse_log(LOG_FILE)
    print(f"Generated {len(scenes)} scenes")
    
    # Create frames directory
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clean old frames
    for f in FRAMES_DIR.glob("*.png"):
        f.unlink()
    
    print("Rendering frames...")
    frame_num = 0
    for scene_idx, scene in enumerate(scenes):
        frames = render_scene(scene, scene_idx, len(scenes))
        for frame in frames:
            frame_path = FRAMES_DIR / f"frame_{frame_num:05d}.png"
            frame.save(str(frame_path))
            frame_num += 1
        print(f"  Scene {scene_idx+1}/{len(scenes)}: '{scene['title']}' ({len(frames)} frames)")
    
    print(f"\nTotal frames: {frame_num}")
    
    # Encode to MP4 using ffmpeg
    OUTPUT_MP4.parent.mkdir(parents=True, exist_ok=True)
    
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%05d.png"),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(OUTPUT_MP4)
    ]
    
    print(f"Encoding MP4: {' '.join(ffmpeg_cmd)}")
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        size_mb = OUTPUT_MP4.stat().st_size / (1024 * 1024)
        print(f"\n✅ Video saved: {OUTPUT_MP4}")
        print(f"   Size: {size_mb:.1f} MB")
        print(f"   Resolution: {WIDTH}x{HEIGHT}")
        print(f"   Duration: ~{frame_num // FPS}s")
        print(f"   FPS: {FPS}")
    else:
        print(f"❌ ffmpeg error: {result.stderr}")


if __name__ == "__main__":
    main()

import http.server
import socketserver
import webbrowser
import threading
import time
import os
import urllib.parse

PORT = 8000

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# נתיבי התמונות במחשב
PELEG_IMAGE_PATH = r"C:\Users\Noya\OneDrive\תמונות\Screenshots\peleg.png"
LOTEM_IMAGE_PATH = r"C:\Users\Noya\OneDrive\תמונות\Screenshots\lotem.png"


def resolve_image(path, name):
    """מחפש את התמונה: הנתיב המקורי (png/jpg/jpeg) ואז ליד הסקריפט."""
    base, _ = os.path.splitext(path)
    candidates = [path, base + ".png", base + ".jpg", base + ".jpeg"]
    for ext in (".png", ".jpg", ".jpeg"):
        candidates.append(os.path.join(SCRIPT_DIR, name + ext))
    for c in candidates:
        if os.path.exists(c):
            return c
    return path


PELEG_IMAGE_PATH = resolve_image(PELEG_IMAGE_PATH, "peleg")
LOTEM_IMAGE_PATH = resolve_image(LOTEM_IMAGE_PATH, "lotem")

HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NBA & Hapoel Tivon All-Star Shootout</title>
    <style>
        * { box-sizing: border-box; user-select: none; }
        body {
            margin: 0; padding: 0; background: #090d16;
            font-family: 'Segoe UI', Arial, sans-serif; color: #ffffff;
            display: flex; align-items: center; justify-content: center;
            min-height: 100vh; overflow: hidden;
        }
        #app-container {
            width: 100vw; height: 100vh; background: #030712;
            position: relative; overflow: hidden; display: flex; flex-direction: column;
        }

        /* MENU SCREEN */
        #menu-screen {
            position: absolute; inset: 0;
            background:
                radial-gradient(ellipse at 50% 0%, rgba(59,130,246,0.25), transparent 60%),
                radial-gradient(ellipse at 50% 100%, rgba(239,68,68,0.18), transparent 60%),
                rgba(10, 15, 30, 0.99);
            z-index: 20; display: flex; flex-direction: column;
            align-items: center; justify-content: center; padding: 20px;
        }
        h1 {
            font-size: 3rem; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 2px;
            background: linear-gradient(90deg, #38bdf8, #3b82f6, #ef4444);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-align: center; filter: drop-shadow(0 4px 18px rgba(59,130,246,0.45));
        }
        p.subtitle { color: #94a3b8; margin-bottom: 20px; font-size: 1.1rem; }

        .player-grid {
            display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px;
            width: 100%; max-width: 1250px; max-height: 520px; overflow-y: auto; padding: 10px;
        }
        .player-card {
            background: linear-gradient(160deg, #243049, #131b2e);
            border: 2px solid #334155; border-radius: 14px; padding: 10px;
            text-align: center; cursor: pointer; transition: all 0.2s ease; position: relative;
            overflow: hidden;
        }
        .player-card::before {
            content: ''; position: absolute; left: 0; right: 0; top: 0; height: 52px;
            background: linear-gradient(135deg, var(--c1, #334155), var(--c2, #1e293b));
            opacity: 0.55;
        }
        .player-card:hover {
            transform: translateY(-4px); border-color: #3b82f6;
            box-shadow: 0 8px 16px rgba(59, 130, 246, 0.3);
        }
        .player-card.selected {
            border-color: #38bdf8; box-shadow: 0 0 22px rgba(56, 189, 248, 0.65);
        }
        .player-card.star-player { border-color: #f59e0b; }
        .player-card.falafel-card {
            border-color: #eab308; box-shadow: 0 0 15px rgba(234, 179, 8, 0.4);
        }
        .player-card img {
            position: relative; width: 78px; height: 78px; border-radius: 50%; object-fit: cover;
            border: 3px solid var(--c2, #475569); margin-bottom: 6px;
            background: radial-gradient(circle at 35% 30%, #475569, #0f172a);
            box-shadow: 0 4px 10px rgba(0,0,0,0.55);
        }
        .player-name {
            position: relative; font-weight: bold; font-size: 0.95rem; margin-bottom: 2px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .player-team { position: relative; font-size: 0.75rem; color: #94a3b8; margin-bottom: 6px; }
        .stat-bar-container { position: relative; font-size: 0.7rem; color: #cbd5e1; text-align: right; }
        .stat-bar { height: 5px; background: #334155; border-radius: 3px; overflow: hidden; margin-top: 2px; }
        .stat-fill { height: 100%; background: linear-gradient(90deg, #22c55e, #86efac); }

        .start-btn {
            margin-top: 20px; padding: 14px 50px; font-size: 1.3rem; font-weight: bold;
            color: #ffffff; background: linear-gradient(90deg, #2563eb, #38bdf8);
            border: none; border-radius: 35px; cursor: pointer;
            box-shadow: 0 5px 25px rgba(56, 189, 248, 0.5); transition: all 0.2s;
        }
        .start-btn:hover { transform: scale(1.05); box-shadow: 0 8px 30px rgba(56, 189, 248, 0.8); }

        /* GAME SCREEN */
        #game-screen { position: relative; width: 100%; height: 100%; display: none; }

        #hud {
            position: absolute; top: 0; left: 0; right: 0; padding: 15px 30px;
            display: flex; justify-content: space-between; align-items: center;
            z-index: 15; background: linear-gradient(180deg, rgba(3, 7, 18, 0.95), transparent);
            direction: ltr;
        }
        .hud-block { display: flex; align-items: center; gap: 12px; }
        .active-player-badge {
            display: flex; align-items: center; gap: 10px; background: rgba(30, 41, 59, 0.85);
            padding: 6px 16px; border-radius: 25px; border: 1px solid #475569;
            backdrop-filter: blur(6px);
        }
        .active-player-badge img { width: 38px; height: 38px; border-radius: 50%; object-fit: cover; }
        .hud-title { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; }
        .hud-value { font-size: 1.7rem; font-weight: bold; text-shadow: 0 2px 8px rgba(0,0,0,0.7); }
        .multiplier-tag {
            background: linear-gradient(135deg, #f59e0b, #d97706); color: #000;
            padding: 4px 12px; border-radius: 10px; font-weight: 900; font-size: 1.1rem;
            box-shadow: 0 0 12px rgba(245, 158, 11, 0.5);
        }
        .hud-btn {
            background: #1e293b; border: 1px solid #475569; color: #ffffff; padding: 8px 16px;
            border-radius: 20px; font-weight: 600; font-size: 0.9rem; cursor: pointer;
            transition: all 0.2s; display: flex; align-items: center; gap: 6px;
        }
        .hud-btn:hover { background: #334155; border-color: #38bdf8; transform: translateY(-2px); }

        #falafel-mode-banner {
            display: none; position: absolute; top: 20px; left: 50%; transform: translateX(-50%);
            background: linear-gradient(135deg, #eab308, #ca8a04, #854d0e); color: #000;
            padding: 10px 40px; border-radius: 30px; font-weight: 900; font-size: 2rem;
            letter-spacing: 2px; z-index: 25; border: 4px solid #fef08a;
            box-shadow: 0 0 35px rgba(234, 179, 8, 0.8), inset 0 0 15px rgba(255, 255, 255, 0.6);
            animation: giantPulse 1s infinite alternate;
        }
        @keyframes giantPulse {
            0% { transform: translateX(-50%) scale(1); box-shadow: 0 0 25px rgba(234, 179, 8, 0.7); }
            100% { transform: translateX(-50%) scale(1.06); box-shadow: 0 0 45px rgba(250, 204, 21, 1); }
        }

        #lava-mode-banner {
            display: none; position: absolute; top: 20px; left: 50%; transform: translateX(-50%);
            background: linear-gradient(135deg, #fb923c, #dc2626, #7f1d1d); color: #fff;
            padding: 10px 40px; border-radius: 30px; font-weight: 900; font-size: 2rem;
            letter-spacing: 2px; z-index: 25; border: 4px solid #fdba74; text-shadow: 0 2px 8px rgba(0,0,0,0.6);
            box-shadow: 0 0 35px rgba(239, 68, 68, 0.85), inset 0 0 15px rgba(255, 220, 160, 0.5);
            animation: giantPulse 1s infinite alternate;
        }
        /* באנר המוד בצד שמאל כדי לא להסתיר את הניקוד */
        #falafel-mode-banner, #lava-mode-banner {
            top: 78px; left: 24px; transform: none; transform-origin: left center;
            font-size: 1.35rem; padding: 6px 22px; letter-spacing: 1px; border-width: 3px;
            animation: badgePulse 1s infinite alternate;
        }
        @keyframes badgePulse { 0% { transform: scale(1); } 100% { transform: scale(1.06); } }
        .hearts { color: #ef4444; font-size: 2rem; letter-spacing: 4px; text-shadow: 0 0 10px rgba(239,68,68,0.6); }
        canvas { display: block; }

        #meter-container {
            position: absolute; bottom: 35px; left: 50%; transform: translateX(-50%);
            width: 520px; height: 36px; background: #0f172a; border: 4px solid #38bdf8;
            border-radius: 18px; overflow: hidden;
            box-shadow: 0 0 25px rgba(56, 189, 248, 0.4), 0 10px 30px rgba(0,0,0,0.9);
            z-index: 10; transition: all 0.3s;
        }
        #meter-container::after {
            content: ''; position: absolute; inset: 0; pointer-events: none;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.35), rgba(255,255,255,0) 50%, rgba(0,0,0,0.25)),
                repeating-linear-gradient(90deg, rgba(0,0,0,0.25) 0 1px, transparent 1px 5%);
        }
        #meter-container.falafel-mode { border-color: #eab308; box-shadow: 0 0 35px #eab308, 0 10px 30px rgba(0,0,0,0.9); }
        #meter-container.lava-mode { border-color: #f97316; box-shadow: 0 0 35px #ef4444, 0 10px 30px rgba(0,0,0,0.9); }
        .meter-zone { height: 100%; position: absolute; top: 0; }
        .zone-red { background: linear-gradient(90deg, #991b1b, #ef4444, #991b1b); width: 100%; left: 0; }
        .zone-yellow { background: linear-gradient(90deg, #a16207, #eab308, #a16207); transition: all 0.2s; }
        .zone-green { background: linear-gradient(90deg, #15803d, #4ade80, #15803d); transition: all 0.2s; }
        #meter-pointer {
            position: absolute; top: 0; width: 7px; height: 100%; background: #ffffff;
            box-shadow: 0 0 12px #ffffff, 0 0 6px #ffffff; left: 0%; z-index: 2;
        }

        #shot-feedback {
            position: absolute; bottom: 90px; left: 50%; transform: translateX(-50%);
            font-size: 2rem; font-weight: 900; text-transform: uppercase; letter-spacing: 2px;
            opacity: 0; transition: opacity 0.2s ease, transform 0.2s ease;
            pointer-events: none; z-index: 10; text-shadow: 0 4px 10px rgba(0,0,0,0.9);
            white-space: nowrap;
        }
        #shot-info-banner {
            position: absolute; top: 85px; left: 50%; transform: translateX(-50%);
            background: rgba(15, 23, 42, 0.9); padding: 6px 20px; border-radius: 12px;
            border: 1px solid #334155; font-size: 1rem; color: #38bdf8; font-weight: 600; z-index: 5;
        }
        #game-over-modal {
            position: absolute; inset: 0; background: rgba(2, 6, 23, 0.94); z-index: 30;
            display: none; flex-direction: column; align-items: center; justify-content: center;
            backdrop-filter: blur(4px);
        }
        #game-over-modal h2 { font-size: 4rem; color: #ef4444; margin: 0 0 10px 0; text-shadow: 0 0 30px rgba(239,68,68,0.6); }
        #final-score { font-size: 2.3rem; margin-bottom: 10px; color: #cbd5e1; }
        #high-score-modal { font-size: 1.5rem; margin-bottom: 25px; color: #f59e0b; font-weight: bold; }
        .modal-btn-group { display: flex; gap: 15px; }
    </style>
</head>
<body>

<div id="app-container">
    <div id="falafel-mode-banner">🥙 מוד מסעדה (X3) 🥙</div>
    <div id="lava-mode-banner">🌋 מוד לבה (X3) 🌋</div>

    <div id="menu-screen">
        <h1>NBA & HAPOEL TIVON SHOOTOUT</h1>
        <p class="subtitle">בחר שחקן והתחל במשחק!</p>
        <div class="player-grid" id="player-grid"></div>
        <button class="start-btn" onclick="startGame()">התחל משחק (מסך מלא)</button>
    </div>

    <div id="game-screen">
        <div id="hud">
            <div class="hud-block">
                <div class="active-player-badge">
                    <img id="hud-player-img" src="" alt="Player" onerror="this.style.visibility='hidden'">
                    <span id="hud-player-name" style="font-weight:700"></span>
                </div>
                <button class="hud-btn" onclick="restartGame()">🔄 אתחול משחק</button>
                <button class="hud-btn" onclick="resetToMenu()">👥 בחירת שחקן</button>
            </div>
            <div class="hud-block">
                <div>
                    <div class="hud-title">שיא קליעות</div>
                    <div class="hud-value" id="high-score-display" style="color: #f59e0b;">0</div>
                </div>
                <div>
                    <div class="hud-title">נקודות</div>
                    <div class="hud-value" id="score-display">0</div>
                </div>
                <div class="multiplier-tag" id="multiplier-display">X1</div>
            </div>
            <div class="hud-block">
                <div>
                    <div class="hud-title">פסילות</div>
                    <div class="hearts" id="hearts-display">♥♥♥</div>
                </div>
            </div>
        </div>

        <div id="shot-info-banner">זריקה 1 | מרחק: רגיל</div>
        <canvas id="gameCanvas"></canvas>
        <div id="shot-feedback">PERFECT!</div>

        <div id="meter-container">
            <div class="meter-zone zone-red"></div>
            <div class="meter-zone zone-yellow" id="yellow-zone"></div>
            <div class="meter-zone zone-green" id="green-zone"></div>
            <div id="meter-pointer"></div>
        </div>
    </div>

    <div id="game-over-modal">
        <h2>GAME OVER</h2>
        <div id="final-score">תוצאה סופית: 0</div>
        <div id="high-score-modal">שיא קליעות: 0</div>
        <div class="modal-btn-group">
            <button class="start-btn" onclick="restartGame()">שחק שוב</button>
            <button class="start-btn" style="background: linear-gradient(90deg, #3b82f6, #1d428a);" onclick="resetToMenu()">תפריט ראשי</button>
        </div>
    </div>
</div>

<script>
    // ===================== עזרים =====================
    const TAU = Math.PI * 2;
    const lerp = (a, b, t) => a + (b - a) * t;
    const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
    const easeOutCubic = t => 1 - Math.pow(1 - t, 3);
    const easeOutBack = t => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); };

    function mulberry32(a) {
        return function () {
            a |= 0; a = a + 0x6D2B79F5 | 0;
            let t = Math.imul(a ^ a >>> 15, 1 | a);
            t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
            return ((t ^ t >>> 14) >>> 0) / 4294967296;
        };
    }
    function hexToRgb(h) {
        h = h.replace('#', '');
        if (h.length === 3) h = h.split('').map(c => c + c).join('');
        const n = parseInt(h, 16);
        return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
    }
    function shade(hex, amt) {
        const [r, g, b] = hexToRgb(hex);
        const f = v => Math.max(0, Math.min(255, Math.round(amt < 0 ? v * (1 + amt) : v + (255 - v) * amt)));
        return `rgb(${f(r)},${f(g)},${f(b)})`;
    }
    function rrPath(ctx, x, y, w, h, r) {
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.arcTo(x + w, y, x + w, y + h, r);
        ctx.arcTo(x + w, y + h, x, y + h, r);
        ctx.arcTo(x, y + h, x, y, r);
        ctx.arcTo(x, y, x + w, y, r);
        ctx.closePath();
    }

    // ===================== שחקנים =====================
    const PLAYERS = [
        { id: 'lotem', name: 'Lotem', team: 'פלאפל חן', primaryColor: '#111827', secondaryColor: '#eab308', skin: '#f1c27d', photo: '/lotem.png', greenWidth: 24, yellowWidth: 48, baseSpeed: 0.95, star: true, isFalafel: true },
        { id: 'peleg', name: 'Peleg Gal', team: 'Hapoel Marnin Tivon', primaryColor: '#ffffff', secondaryColor: '#2563eb', skin: '#f1c27d', photo: '/peleg.png', greenWidth: 22, yellowWidth: 46, baseSpeed: 1.0, star: true },
        { id: 'deni', name: 'Deni Avdija', team: 'POR Trail Blazers', primaryColor: '#E03A3E', secondaryColor: '#000000', skin: '#f1c27d', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/4683021.png', greenWidth: 16, yellowWidth: 40, baseSpeed: 1.2 },
        { id: 'curry', name: 'Steph Curry', team: 'GS Warriors', primaryColor: '#1D428A', secondaryColor: '#FFC72C', skin: '#d2a679', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/3975.png', greenWidth: 18, yellowWidth: 42, baseSpeed: 1.1 },
        { id: 'lebron', name: 'LeBron James', team: 'LA Lakers', primaryColor: '#552583', secondaryColor: '#FDB927', skin: '#8d5524', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/1966.png', greenWidth: 14, yellowWidth: 38, baseSpeed: 1.3 },
        { id: 'giannis', name: 'Giannis Antetokounmpo', team: 'MIL Bucks', primaryColor: '#00471B', secondaryColor: '#EEE1C6', skin: '#5c3818', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/3032977.png', greenWidth: 12, yellowWidth: 34, baseSpeed: 1.5 },
        { id: 'luka', name: 'Luka Dončić', team: 'DAL Mavericks', primaryColor: '#00538C', secondaryColor: '#002B5E', skin: '#f1c27d', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/3945274.png', greenWidth: 16, yellowWidth: 40, baseSpeed: 1.25 },
        { id: 'jokic', name: 'Nikola Jokić', team: 'DEN Nuggets', primaryColor: '#0E2240', secondaryColor: '#FEC524', skin: '#f1c27d', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/3112335.png', greenWidth: 15, yellowWidth: 38, baseSpeed: 1.2 },
        { id: 'sga', name: 'Shai Gilgeous-Alexander', team: 'OKC Thunder', primaryColor: '#007AC1', secondaryColor: '#EF3B24', skin: '#73441a', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/4278073.png', greenWidth: 17, yellowWidth: 41, baseSpeed: 1.2 },
        { id: 'tatum', name: 'Jayson Tatum', team: 'BOS Celtics', primaryColor: '#007A33', secondaryColor: '#BA9653', skin: '#a36d3f', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/4065648.png', greenWidth: 15, yellowWidth: 39, baseSpeed: 1.25 },
        { id: 'edwards', name: 'Anthony Edwards', team: 'MIN Timberwolves', primaryColor: '#0C2340', secondaryColor: '#236192', skin: '#633816', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/4594268.png', greenWidth: 14, yellowWidth: 36, baseSpeed: 1.4 },
        { id: 'wemby', name: 'Victor Wembanyama', team: 'SA Spurs', primaryColor: '#C4CED4', secondaryColor: '#000000', skin: '#a36d3f', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/5104157.png', greenWidth: 13, yellowWidth: 35, baseSpeed: 1.45 },
        { id: 'haliburton', name: 'Tyrese Haliburton', team: 'IND Pacers', primaryColor: '#002D62', secondaryColor: '#FDBB30', skin: '#a36d3f', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/4395630.png', greenWidth: 16, yellowWidth: 40, baseSpeed: 1.2 },
        { id: 'mitchell', name: 'Donovan Mitchell', team: 'CLE Cavaliers', primaryColor: '#860038', secondaryColor: '#041E42', skin: '#633816', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/3908809.png', greenWidth: 15, yellowWidth: 38, baseSpeed: 1.3 },
        { id: 'booker', name: 'Devin Booker', team: 'PHX Suns', primaryColor: '#1D1160', secondaryColor: '#E56020', skin: '#d2a679', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/3136193.png', greenWidth: 16, yellowWidth: 39, baseSpeed: 1.25 },
        { id: 'ad', name: 'Anthony Davis', team: 'LA Lakers', primaryColor: '#552583', secondaryColor: '#FDB927', skin: '#633816', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/6583.png', greenWidth: 13, yellowWidth: 35, baseSpeed: 1.4 },
        { id: 'kd', name: 'Kevin Durant', team: 'PHX Suns', primaryColor: '#1D1160', secondaryColor: '#E56020', skin: '#633816', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/3202.png', greenWidth: 17, yellowWidth: 41, baseSpeed: 1.15 },
        { id: 'brunson', name: 'Jalen Brunson', team: 'NY Knicks', primaryColor: '#006BB6', secondaryColor: '#F58426', skin: '#a36d3f', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/3934672.png', greenWidth: 15, yellowWidth: 38, baseSpeed: 1.3 },
        { id: 'trae', name: 'Trae Young', team: 'ATL Hawks', primaryColor: '#C8102E', secondaryColor: '#FDB927', skin: '#d2a679', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/4277905.png', greenWidth: 16, yellowWidth: 40, baseSpeed: 1.3 },
        { id: 'adebayo', name: 'Bam Adebayo', team: 'MIA Heat', primaryColor: '#98002E', secondaryColor: '#F9A01B', skin: '#5c3818', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/4066261.png', greenWidth: 13, yellowWidth: 34, baseSpeed: 1.4 },
        { id: 'sabonis', name: 'Domantas Sabonis', team: 'SAC Kings', primaryColor: '#5A2D82', secondaryColor: '#63727A', skin: '#f1c27d', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/3155942.png', greenWidth: 14, yellowWidth: 36, baseSpeed: 1.3 },
        { id: 'towns', name: 'Karl-Anthony Towns', team: 'NY Knicks', primaryColor: '#006BB6', secondaryColor: '#F58426', skin: '#a36d3f', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/3136195.png', greenWidth: 14, yellowWidth: 37, baseSpeed: 1.35 },
        { id: 'fox', name: 'De\'Aaron Fox', team: 'SAC Kings', primaryColor: '#5A2D82', secondaryColor: '#63727A', skin: '#633816', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/4066259.png', greenWidth: 15, yellowWidth: 38, baseSpeed: 1.35 },
        { id: 'george', name: 'Paul George', team: 'PHI 76ers', primaryColor: '#006BB6', secondaryColor: '#ED174C', skin: '#73441a', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/4251.png', greenWidth: 15, yellowWidth: 39, baseSpeed: 1.25 },
        { id: 'butler', name: 'Jimmy Butler', team: 'MIA Heat', primaryColor: '#98002E', secondaryColor: '#F9A01B', skin: '#633816', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/6430.png', greenWidth: 14, yellowWidth: 37, baseSpeed: 1.3 },
        { id: 'maxey', name: 'Tyrese Maxey', team: 'PHI 76ers', primaryColor: '#006BB6', secondaryColor: '#ED174C', skin: '#633816', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/4431678.png', greenWidth: 16, yellowWidth: 39, baseSpeed: 1.35 },
        { id: 'lillard', name: 'Damian Lillard', team: 'MIL Bucks', primaryColor: '#00471B', secondaryColor: '#EEE1C6', skin: '#73441a', photo: 'https://a.espncdn.com/i/headshots/nba/players/full/6606.png', greenWidth: 17, yellowWidth: 41, baseSpeed: 1.2 }
    ];
    const PELEG = PLAYERS.find(p => p.id === 'peleg');
    const JERSEY_NUMS = { lotem: 10, peleg: 9, deni: 8, curry: 30, lebron: 23, giannis: 34, luka: 77, jokic: 15, sga: 2, tatum: 0, edwards: 5, wemby: 1, haliburton: 0, mitchell: 45, booker: 1, ad: 3, kd: 35, brunson: 11, trae: 11, adebayo: 13, sabonis: 11, towns: 32, fox: 5, george: 8, butler: 22, maxey: 0, lillard: 0 };

    const loadedPlayerImages = {};
    PLAYERS.forEach(p => {
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.src = p.photo;
        loadedPlayerImages[p.id] = img;
    });
    const imgOk = img => img && img.complete && img.naturalWidth > 0;

    const POSITIONS = [
        { name: 'זריקת עונשין (Mid-Range)', xRatio: 0.5, yRatio: 0.68, speedMult: 1.0, widthMult: 1.0 },
        { name: 'כנף שמאל (Left Wing)', xRatio: 0.28, yRatio: 0.65, speedMult: 1.15, widthMult: 0.9 },
        { name: 'כנף ימין (Right Wing)', xRatio: 0.72, yRatio: 0.65, speedMult: 1.15, widthMult: 0.9 },
        { name: 'שלשה מרכזית (3-Pointer)', xRatio: 0.5, yRatio: 0.78, speedMult: 1.3, widthMult: 0.8 },
        { name: 'זריקת לייאפ קרובה (Layup)', xRatio: 0.45, yRatio: 0.52, speedMult: 0.85, widthMult: 1.2 },
        { name: 'שלשה רחוקה (Deep 3-PT)', xRatio: 0.30, yRatio: 0.82, speedMult: 1.5, widthMult: 0.7 }
    ];

    // ===================== מצב משחק =====================
    let selectedPlayer = PLAYERS[0];
    let score = 0, highScore = 0, multiplier = 1, consecutiveMakes = 0;
    let totalShotsCount = 0, totalSuccessfulMakes = 0, lives = 3;
    let isGameRunning = false, isShooting = false, currentPosIndex = 0, isFalafelMode = false, isLavaMode = false;
    const bonusMode = () => isFalafelMode || isLavaMode;
    let meterPos = 0, meterDirection = 1, meterAnimationId = null;

    // מצב ויזואלי
    const PLAYER_SCALE = 1.12;
    const HAND_BALL = { x: 24, y: -26 };      // כדור ביד (מקומי)
    const RELEASE_BALL = { x: 20, y: -100 };  // נקודת שחרור (מקומי)
    let playerJumpY = 0, shootBlend = 0;
    let tahiniShots = [], persistentTahiniSplashes = [], particles = [];
    let flight = { active: false, p: 0, x: 0, y: 0, r: 18, rot: 0, alpha: 1, trail: [] };
    let netSwish = 0, rimShake = 0, shake = 0;
    let gunAngle = -0.1, gunFlash = 0, gunRecoil = 0;
    let T = 0, dt = 0.016, lastT = performance.now();

    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    let W = window.innerWidth, H = window.innerHeight, DPR = 1;
    let crowd = [];

    function resizeCanvas() {
        DPR = Math.min(window.devicePixelRatio || 1, 2);
        W = window.innerWidth; H = window.innerHeight;
        canvas.width = Math.round(W * DPR);
        canvas.height = Math.round(H * DPR);
        canvas.style.width = W + 'px';
        canvas.style.height = H + 'px';
        ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        buildCrowd();
    }

    function buildCrowd() {
        const rnd = mulberry32(7);
        crowd = [];
        const rows = 6;
        const pal = ['#1e3a8a', '#b91c1c', '#f59e0b', '#e2e8f0', '#0f766e', '#7c3aed', '#334155', '#be185d'];
        const skins = ['#f1c27d', '#d2a679', '#a36d3f', '#73441a', '#e0ac69'];
        const top = H * 0.035, bot = H * 0.27;
        for (let r = 0; r < rows; r++) {
            const y = top + (bot - top) * (r / (rows - 1));
            const rad = 7 + r * 1.4, step = rad * 2.9;
            for (let x = (r % 2) * step / 2; x < W + step; x += step) {
                crowd.push({
                    x: x + rnd() * 4, y: y + rnd() * 3, r: rad,
                    shirt: pal[(rnd() * pal.length) | 0], skin: skins[(rnd() * skins.length) | 0],
                    hair: rnd() > 0.5 ? '#1b120a' : '#3d2a17', ph: rnd() * TAU, up: rnd() > 0.88
                });
            }
        }
    }

    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    // ===================== תפריט =====================
    const grid = document.getElementById('player-grid');
    PLAYERS.forEach((p, idx) => {
        const card = document.createElement('div');
        let cardClass = idx === 0 ? 'selected ' : '';
        if (p.isFalafel) cardClass += 'falafel-card';
        else if (p.star) cardClass += 'star-player';
        card.className = `player-card ${cardClass}`;
        card.style.setProperty('--c1', p.primaryColor === '#ffffff' ? '#cbd5e1' : p.primaryColor);
        card.style.setProperty('--c2', p.secondaryColor);
        card.onclick = () => selectPlayer(p, card);
        card.innerHTML = `
            <img src="${p.photo}" alt="${p.name}" onerror="this.style.visibility='hidden'">
            <div class="player-name">${p.name} ${p.isFalafel ? '🥙' : (p.star ? '⭐' : '')}</div>
            <div class="player-team">${p.team}</div>
            <div class="stat-bar-container">
                דיוק:
                <div class="stat-bar"><div class="stat-fill" style="width: ${p.greenWidth * 4.5}%"></div></div>
            </div>`;
        grid.appendChild(card);
    });

    function selectPlayer(p, cardEl) {
        selectedPlayer = p;
        document.querySelectorAll('.player-card').forEach(c => c.classList.remove('selected'));
        cardEl.classList.add('selected');
    }

    function openFullscreen() {
        const elem = document.documentElement;
        if (elem.requestFullscreen) elem.requestFullscreen().catch(err => console.log(err));
        else if (elem.webkitRequestFullscreen) elem.webkitRequestFullscreen();
        else if (elem.msRequestFullscreen) elem.msRequestFullscreen();
    }

    // ===================== מד כוח =====================
    function currentZones() {
        const pos = POSITIONS[currentPosIndex];
        const diff = Math.pow(0.9, Math.floor(totalSuccessfulMakes / 10));
        let greenW = selectedPlayer.greenWidth * pos.widthMult * diff;
        let yellowW = selectedPlayer.yellowWidth * pos.widthMult * diff;
        if (bonusMode()) { greenW *= 0.45; yellowW *= 0.6; }
        return { greenW, yellowW };
    }

    function setupMeterForCurrentShot() {
        const pos = POSITIONS[currentPosIndex];
        // כל 20 זריקות: לוטם = מוד מסעדה, כל השאר = מוד לבה
        const bonusRound = totalShotsCount > 0 && totalShotsCount % 20 === 0;
        isFalafelMode = bonusRound && !!selectedPlayer.isFalafel;
        isLavaMode = bonusRound && !selectedPlayer.isFalafel;
        const mc = document.getElementById('meter-container');
        document.getElementById('falafel-mode-banner').style.display = isFalafelMode ? 'block' : 'none';
        document.getElementById('lava-mode-banner').style.display = isLavaMode ? 'block' : 'none';
        mc.classList.toggle('falafel-mode', isFalafelMode);
        mc.classList.toggle('lava-mode', isLavaMode);
        const { greenW, yellowW } = currentZones();
        const yz = document.getElementById('yellow-zone'), gz = document.getElementById('green-zone');
        gz.style.width = greenW + '%'; gz.style.left = (50 - greenW / 2) + '%';
        yz.style.width = yellowW + '%'; yz.style.left = (50 - yellowW / 2) + '%';

        const shotTitle = selectedPlayer.isFalafel ? 'זריקת פלאפל לפיתה' : 'זריקת סל';
        document.getElementById('shot-info-banner').innerText =
            `זריקה #${totalShotsCount + 1} | מיקום: ${pos.name} (${shotTitle}) ${isFalafelMode ? '🥙 [מוד מסעדה]' : (isLavaMode ? '🌋 [מוד לבה]' : '')}`;
    }

    function resetRoundState() {
        score = 0; multiplier = 1; consecutiveMakes = 0; totalShotsCount = 0;
        totalSuccessfulMakes = 0; lives = 3; isShooting = false; isGameRunning = true;
        currentPosIndex = 0; tahiniShots = []; persistentTahiniSplashes = []; particles = [];
        flight.active = false; shootBlend = 0; playerJumpY = 0; netSwish = 0; rimShake = 0; shake = 0;
    }

    function startGame() {
        openFullscreen();
        document.getElementById('menu-screen').style.display = 'none';
        document.getElementById('game-screen').style.display = 'block';
        document.getElementById('game-over-modal').style.display = 'none';
        const hi = document.getElementById('hud-player-img');
        hi.style.visibility = 'visible';
        hi.src = selectedPlayer.photo;
        document.getElementById('hud-player-name').innerText = selectedPlayer.name;
        resetRoundState();
        resizeCanvas();
        updateHUD();
        setupMeterForCurrentShot();
        ensureLoop();
    }

    function restartGame() {
        document.getElementById('game-over-modal').style.display = 'none';
        resetRoundState();
        updateHUD();
        setupMeterForCurrentShot();
        ensureLoop();
    }

    function updateHUD() {
        document.getElementById('score-display').innerText = score;
        document.getElementById('high-score-display').innerText = highScore;
        document.getElementById('multiplier-display').innerText = `X${multiplier}`;
        let heartsStr = '';
        for (let i = 0; i < 3; i++) heartsStr += (i < lives) ? '♥' : '♡';
        document.getElementById('hearts-display').innerText = heartsStr;
    }

    // ===================== לולאה ראשית =====================
    function ensureLoop() {
        cancelAnimationFrame(meterAnimationId);
        lastT = performance.now();
        meterAnimationId = requestAnimationFrame(frame);
    }

    function frame(now) {
        dt = Math.min(0.05, Math.max(0.001, (now - lastT) / 1000));
        lastT = now; T += dt;

        if (isGameRunning && !isShooting) {
            const pos = POSITIONS[currentPosIndex];
            let spd = selectedPlayer.baseSpeed * pos.speedMult;
            if (bonusMode()) spd *= 1.4;
            meterPos += spd * meterDirection * dt * 60;
            if (meterPos >= 100) { meterPos = 100; meterDirection = -1; }
            else if (meterPos <= 0) { meterPos = 0; meterDirection = 1; }
            document.getElementById('meter-pointer').style.left = `calc(${meterPos}% - ${meterPos * 0.07}px)`;
        }
        updateEffects();
        drawScene();
        meterAnimationId = requestAnimationFrame(frame);
    }

    window.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && isGameRunning && !isShooting) { e.preventDefault(); takeShot(); }
    });
    canvas.addEventListener('click', () => { if (isGameRunning && !isShooting) takeShot(); });

    // ===================== זריקה =====================
    function takeShot() {
        isShooting = true;
        persistentTahiniSplashes = [];
        tahiniShots = [];
        const { greenW, yellowW } = currentZones();
        let result = 'bad';
        if (meterPos >= 50 - greenW / 2 && meterPos <= 50 + greenW / 2) result = 'green';
        else if (meterPos >= 50 - yellowW / 2 && meterPos <= 50 + yellowW / 2) result = 'yellow';
        showFeedback(result);
        animateShotSequence(result);
    }

    function showFeedback(result) {
        const fb = document.getElementById('shot-feedback');
        if (result === 'green') {
            fb.innerText = isFalafelMode ? '🥙 פלאפל מושלם לפיתה! 🥙' : (isLavaMode ? '🌋 מושלם! הלבה לא תפסה אותך! 🌋' : '🎯 PERFECT! (10 נק\')');
            fb.style.color = '#22c55e';
        } else if (result === 'yellow') {
            fb.innerText = selectedPlayer.isFalafel ? '⚠️ כמעט נכנס לפיתה! (0 נק\')' : '⚠️ כמעט נכנס לסל! (0 נק\')';
            fb.style.color = '#eab308';
        } else {
            fb.innerText = selectedPlayer.isFalafel ? '❌ פספוס! פלג יורה עליך טחינה!' : '❌ MISSED!';
            fb.style.color = '#ef4444';
        }
        fb.style.opacity = '1';
        fb.style.transform = 'translateX(-50%) translateY(-20px)';
        setTimeout(() => { fb.style.opacity = '0'; fb.style.transform = 'translateX(-50%) translateY(0px)'; }, 900);
    }

    function animateShotSequence(result) {
        const pos = POSITIONS[currentPosIndex];
        const s = PLAYER_SCALE;
        const pX = W * pos.xRatio, pYbase = H * pos.yRatio;
        const hoopX = W / 2, hoopY = H * 0.22;
        const dir = Math.random() > 0.5 ? 1 : -1;
        let tx = hoopX, ty = hoopY;
        if (result === 'bad') { tx = hoopX + dir * 70; ty = hoopY + 40; }
        else if (result === 'yellow') { tx = hoopX + dir * 22; ty = hoopY + 6; }

        const T1 = 1000, T2 = 520, RELEASE_P = 0.12;
        const baseR = selectedPlayer.isFalafel ? 17 : 19;
        const jumpAt = p => Math.sin(Math.min(p / 0.9, 1) * Math.PI) * 45;
        const sx = pX + RELEASE_BALL.x * s;
        const sy = pYbase - jumpAt(RELEASE_P) - (-RELEASE_BALL.y) * s;
        const arcH = clamp((sy - ty) * 0.45 + 80, 120, 380);

        let start = null, fired = false, processed = false;
        flight.active = true; flight.trail = []; flight.alpha = 1; flight.rot = 0;

        function step(ts) {
            if (start === null) start = ts;
            const el = ts - start;

            if (el <= T1) {
                const p = el / T1;
                flight.p = p;
                playerJumpY = jumpAt(p);
                shootBlend = easeOutCubic(Math.min(p / RELEASE_P, 1));
                if (p >= RELEASE_P) {
                    const u = (p - RELEASE_P) / (1 - RELEASE_P);
                    flight.x = lerp(sx, tx, u);
                    flight.y = lerp(sy, ty, u) - Math.sin(u * Math.PI) * arcH;
                    flight.r = lerp(baseR, baseR * 0.72, u);
                    flight.rot = u * TAU * 2;
                    flight.trail.push([flight.x, flight.y]);
                    if (flight.trail.length > 9) flight.trail.shift();
                }
                if (!fired && result === 'bad' && selectedPlayer.isFalafel && p >= 0.6) {
                    fired = true;
                    fireTahini(pX, pYbase - 56 * s);
                }
                requestAnimationFrame(step);
                return;
            }

            if (!processed) {
                processed = true;
                flight.p = 1;
                processShotResult(result);
            }
            const u2 = Math.min((el - T1) / T2, 1);
            playerJumpY = 0;
            shootBlend = 1 - easeOutCubic(u2);
            flight.rot += 0.12;
            if (result === 'green') {
                flight.x = tx; flight.y = ty + 10 * u2 + 150 * u2 * u2; flight.alpha = 1 - u2 * 0.85;
            } else if (result === 'yellow') {
                flight.x = tx + dir * 38 * u2 + dir * Math.sin(u2 * Math.PI * 3) * 6;
                flight.y = ty - 42 * Math.sin(u2 * Math.PI) + 240 * u2 * u2; flight.alpha = 1 - u2 * 0.5;
            } else {
                flight.x = tx + dir * 230 * u2; flight.y = ty - 270 * u2 + 540 * u2 * u2; flight.alpha = 1 - u2 * 0.6;
            }
            flight.trail.push([flight.x, flight.y]);
            if (flight.trail.length > 9) flight.trail.shift();

            if (u2 < 1) {
                requestAnimationFrame(step);
            } else {
                flight.active = false; flight.trail = [];
                shootBlend = 0;
                setTimeout(() => {
                    totalShotsCount++;
                    currentPosIndex = Math.floor(Math.random() * POSITIONS.length);
                    setupMeterForCurrentShot();
                    isShooting = false;
                }, 150);
            }
        }
        requestAnimationFrame(step);
    }

    function processShotResult(result) {
        const hoopX = W / 2, hoopY = H * 0.22;
        if (result === 'green') {
            let basePoints = 10;
            consecutiveMakes++; totalSuccessfulMakes++;
            if (consecutiveMakes > 0 && consecutiveMakes % 3 === 0) { multiplier *= 2; basePoints += 8; }
            const modeMult = bonusMode() ? 3 : 1;
            score += basePoints * multiplier * modeMult;
            if (score > highScore) highScore = score;
            netSwish = 1;
            const cols = isFalafelMode ? ['#eab308', '#f59e0b', '#fef08a', '#a16207']
                : (isLavaMode ? ['#f97316', '#fde047', '#ef4444', '#ffffff'] : [selectedPlayer.secondaryColor, selectedPlayer.primaryColor, '#ffffff', '#38bdf8']);
            spawnConfetti(hoopX, hoopY + 10, 34, cols);
            particles.push({ type: 'ring', x: hoopX, y: hoopY + 10, life: 0, max: 0.6, color: isFalafelMode ? '#fde047' : (isLavaMode ? '#fb923c' : '#4ade80') });
        } else if (result === 'yellow') {
            consecutiveMakes = 0;
            netSwish = 0.35; rimShake = 1;
            spawnSparks(hoopX, hoopY, 10);
        } else {
            lives--; consecutiveMakes = 0;
            rimShake = 1; shake = Math.max(shake, 10);
            if (isLavaMode) { const lp = POSITIONS[currentPosIndex]; spawnSparks(W * lp.xRatio, H * lp.yRatio + 70, 24); }
            if (lives <= 0) gameOver();
        }
        updateHUD();
    }

    // ===================== טחינה ורובה =====================
    const GUN_SCALE = 1.15;
    function shooterPos() { return { x: Math.max(95, W * 0.075), y: H * 0.62 }; }
    function gunPivot() {
        const sp = shooterPos(), s = 1.1;
        return { x: sp.x + 20 * s, y: sp.y - 20 * s };
    }
    function gunMuzzle() {
        const p = gunPivot(), d = 96 * GUN_SCALE;
        return { x: p.x + Math.cos(gunAngle) * d, y: p.y + Math.sin(gunAngle) * d };
    }

    function fireTahini(tx, ty) {
        const m = gunMuzzle();
        tahiniShots.push({ sx: m.x, sy: m.y, tx, ty, t: 0, dur: 0.4, trail: [], x: m.x, y: m.y });
        gunFlash = 1; gunRecoil = 14;
        spawnDrops(m.x, m.y, 12, gunAngle, 0.7, 320);
    }

    function makeSplash(x, y) {
        const r = Math.random;
        const blobs = [{ dx: 0, dy: 0, rx: 38, ry: 25, rot: r() * 1.2 - 0.6 }];
        for (let i = 0; i < 4; i++) blobs.push({ dx: (r() - 0.5) * 54, dy: (r() - 0.5) * 36, rx: 12 + r() * 14, ry: 8 + r() * 10, rot: r() * 3 });
        const drops = [];
        for (let i = 0; i < 9; i++) drops.push({ dx: (r() - 0.5) * 140, dy: (r() - 0.5) * 96, r: 2 + r() * 5 });
        const drips = [];
        for (let i = 0; i < 3; i++) drips.push({ dx: (r() - 0.5) * 54, dy: 10 + r() * 8, len0: 4, speed: 14 + r() * 14, max: 30 + r() * 42, w: 6 + r() * 4 });
        return { x, y, t: 0, blobs, drops, drips };
    }

    function spawnDrops(x, y, n, angle, spread, speed) {
        for (let i = 0; i < n; i++) {
            const a = angle + (Math.random() - 0.5) * spread * 2;
            const sp = speed * (0.35 + Math.random() * 0.65);
            particles.push({ type: 'drop', x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, life: 0, max: 0.5 + Math.random() * 0.5, size: 2 + Math.random() * 3.5 });
        }
    }
    function spawnConfetti(x, y, n, colors) {
        for (let i = 0; i < n; i++) {
            particles.push({
                type: 'conf', x, y, vx: (Math.random() - 0.5) * 460, vy: -Math.random() * 380 - 60,
                life: 0, max: 1.1 + Math.random() * 0.7, size: 4 + Math.random() * 5,
                rot: Math.random() * TAU, vr: (Math.random() - 0.5) * 14, color: colors[(Math.random() * colors.length) | 0]
            });
        }
    }
    function spawnSparks(x, y, n) {
        for (let i = 0; i < n; i++) {
            const a = Math.random() * TAU, sp = 100 + Math.random() * 180;
            particles.push({ type: 'spark', x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - 60, life: 0, max: 0.4 + Math.random() * 0.3, size: 2 + Math.random() * 2 });
        }
    }

    function updateEffects() {
        // טחינה בטיסה
        tahiniShots.forEach(s => {
            s.t += dt;
            const u = Math.min(s.t / s.dur, 1);
            s.x = lerp(s.sx, s.tx, u);
            s.y = lerp(s.sy, s.ty, u) - Math.sin(u * Math.PI) * 28;
            s.trail.push([s.x, s.y]);
            if (s.trail.length > 10) s.trail.shift();
            if (u >= 1) {
                s.done = true;
                persistentTahiniSplashes.push(makeSplash(s.tx, s.ty));
                spawnDrops(s.tx, s.ty, 24, -Math.PI / 2, Math.PI, 380);
                shake = Math.max(shake, 7);
            }
        });
        tahiniShots = tahiniShots.filter(s => !s.done);
        persistentTahiniSplashes.forEach(sp => sp.t += dt);

        // חלקיקים
        particles.forEach(p => {
            p.life += dt;
            if (p.type === 'drop') { p.vy += 760 * dt; p.x += p.vx * dt; p.y += p.vy * dt; }
            else if (p.type === 'conf') { p.vy += 620 * dt; p.vx *= (1 - 0.8 * dt); p.x += p.vx * dt; p.y += p.vy * dt; p.rot += p.vr * dt; }
            else if (p.type === 'spark') { p.vy += 500 * dt; p.x += p.vx * dt; p.y += p.vy * dt; }
            else if (p.type === 'ember') { p.x += (p.vx + Math.sin(T * 3 + p.life * 5 + p.size) * 14) * dt; p.y += p.vy * dt; }
        });
        particles = particles.filter(p => p.life < p.max);

        // מצלמות קהל
        if (isLavaMode && Math.random() < 0.6) {
            particles.push({ type: 'ember', x: Math.random() * W, y: H * (0.34 + Math.random() * 0.66), vx: (Math.random() - 0.5) * 30, vy: -(50 + Math.random() * 110), life: 0, max: 1.2 + Math.random() * 1.4, size: 1.5 + Math.random() * 2.5 });
        }
        if (!isFalafelMode && !isLavaMode && Math.random() < 0.12) {
            particles.push({ type: 'flash', x: Math.random() * W, y: H * (0.05 + Math.random() * 0.22), life: 0, max: 0.14 });
        }

        netSwish *= Math.pow(0.5, dt / 0.45);
        rimShake *= Math.pow(0.5, dt / 0.25);
        shake *= Math.pow(0.5, dt / 0.12);
        gunFlash *= Math.pow(0.5, dt / 0.08);
        gunRecoil *= Math.pow(0.5, dt / 0.09);
    }

    // ===================== ציור: כלי עזר =====================
    function drawBall(x, y, r, rot, alpha) {
        ctx.save();
        ctx.globalAlpha = alpha === undefined ? 1 : alpha;
        ctx.translate(x, y);
        ctx.shadowColor = 'rgba(0,0,0,0.45)'; ctx.shadowBlur = 8; ctx.shadowOffsetY = 3;
        let g = ctx.createRadialGradient(-r * 0.35, -r * 0.4, r * 0.1, 0, 0, r);
        g.addColorStop(0, '#ffa55a'); g.addColorStop(0.45, '#e8650f'); g.addColorStop(1, '#7c2f05');
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(0, 0, r, 0, TAU); ctx.fill();
        ctx.shadowColor = 'transparent';
        ctx.save();
        ctx.beginPath(); ctx.arc(0, 0, r, 0, TAU); ctx.clip();
        ctx.rotate(rot);
        ctx.strokeStyle = '#220e03'; ctx.lineWidth = Math.max(1.4, r * 0.09); ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(0, -r); ctx.lineTo(0, r); ctx.moveTo(-r, 0); ctx.lineTo(r, 0); ctx.stroke();
        ctx.beginPath(); ctx.arc(-r * 1.45, 0, r * 1.05, -0.9, 0.9); ctx.stroke();
        ctx.beginPath(); ctx.arc(r * 1.45, 0, r * 1.05, Math.PI - 0.9, Math.PI + 0.9); ctx.stroke();
        ctx.restore();
        let sh = ctx.createRadialGradient(0, 0, r * 0.55, 0, 0, r);
        sh.addColorStop(0, 'rgba(0,0,0,0)'); sh.addColorStop(1, 'rgba(0,0,0,0.38)');
        ctx.fillStyle = sh; ctx.beginPath(); ctx.arc(0, 0, r, 0, TAU); ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,0.42)';
        ctx.beginPath(); ctx.ellipse(-r * 0.38, -r * 0.45, r * 0.28, r * 0.15, -0.7, 0, TAU); ctx.fill();
        ctx.restore();
    }

    function drawFalafelBall(x, y, r, rot, glow, alpha) {
        ctx.save();
        ctx.globalAlpha = alpha === undefined ? 1 : alpha;
        ctx.translate(x, y);
        if (glow) { ctx.shadowColor = '#fde047'; ctx.shadowBlur = 18; }
        else { ctx.shadowColor = 'rgba(0,0,0,0.45)'; ctx.shadowBlur = 8; ctx.shadowOffsetY = 3; }
        let g = ctx.createRadialGradient(-r * 0.35, -r * 0.4, r * 0.1, 0, 0, r);
        g.addColorStop(0, '#e9b45e'); g.addColorStop(0.5, '#a8621c'); g.addColorStop(1, '#4a2208');
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(0, 0, r, 0, TAU); ctx.fill();
        ctx.shadowColor = 'transparent';
        ctx.save();
        ctx.beginPath(); ctx.arc(0, 0, r, 0, TAU); ctx.clip();
        ctx.rotate(rot);
        const rnd = mulberry32(99);
        for (let i = 0; i < 16; i++) {
            const a = rnd() * TAU, d = rnd() * r * 0.9;
            ctx.fillStyle = rnd() > 0.5 ? 'rgba(40,16,2,0.55)' : 'rgba(250,210,130,0.5)';
            ctx.beginPath(); ctx.arc(Math.cos(a) * d, Math.sin(a) * d, r * (0.07 + rnd() * 0.1), 0, TAU); ctx.fill();
        }
        ctx.fillStyle = '#fff3d0';
        for (let i = 0; i < 6; i++) {
            const a = rnd() * TAU, d = rnd() * r * 0.8;
            ctx.beginPath(); ctx.ellipse(Math.cos(a) * d, Math.sin(a) * d, r * 0.1, r * 0.06, a, 0, TAU); ctx.fill();
        }
        ctx.restore();
        let sh = ctx.createRadialGradient(0, 0, r * 0.5, 0, 0, r);
        sh.addColorStop(0, 'rgba(0,0,0,0)'); sh.addColorStop(1, 'rgba(0,0,0,0.4)');
        ctx.fillStyle = sh; ctx.beginPath(); ctx.arc(0, 0, r, 0, TAU); ctx.fill();
        ctx.fillStyle = 'rgba(255,240,200,0.35)';
        ctx.beginPath(); ctx.ellipse(-r * 0.36, -r * 0.42, r * 0.26, r * 0.14, -0.7, 0, TAU); ctx.fill();
        ctx.restore();
    }

    function drawBallOrFalafel(x, y, r, rot, alpha) {
        if (selectedPlayer.isFalafel) drawFalafelBall(x, y, r, rot, isFalafelMode, alpha);
        else drawBall(x, y, r, rot, alpha);
    }

    function limb(pts, w, skin) {
        ctx.save();
        ctx.lineCap = 'round'; ctx.lineJoin = 'round';
        ctx.beginPath();
        pts.forEach((p, i) => i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]));
        ctx.strokeStyle = 'rgba(0,0,0,0.5)'; ctx.lineWidth = w + 2.6; ctx.stroke();
        ctx.strokeStyle = skin; ctx.lineWidth = w; ctx.stroke();
        ctx.save(); ctx.translate(w * 0.2, w * 0.2);
        ctx.strokeStyle = 'rgba(0,0,0,0.17)'; ctx.lineWidth = w * 0.55; ctx.stroke(); ctx.restore();
        ctx.save(); ctx.translate(-w * 0.2, -w * 0.2);
        ctx.strokeStyle = 'rgba(255,255,255,0.2)'; ctx.lineWidth = w * 0.28; ctx.stroke(); ctx.restore();
        ctx.restore();
    }
    const lerpPts = (a, b, t) => a.map((p, i) => [lerp(p[0], b[i][0], t), lerp(p[1], b[i][1], t)]);

    function drawShoe(ax, ay, P) {
        ctx.save();
        ctx.shadowColor = 'rgba(0,0,0,0.4)'; ctx.shadowBlur = 3;
        let g = ctx.createLinearGradient(0, ay - 3, 0, ay + 8);
        g.addColorStop(0, '#ffffff'); g.addColorStop(1, '#cbd5e1');
        ctx.fillStyle = g; rrPath(ctx, ax - 9, ay - 3, 23, 10, 4); ctx.fill();
        ctx.shadowColor = 'transparent';
        ctx.fillStyle = P.secondaryColor; rrPath(ctx, ax + 5, ay - 3, 9, 10, 4); ctx.fill();
        ctx.fillStyle = '#1e293b'; ctx.fillRect(ax - 9, ay + 6, 23, 3);
        ctx.strokeStyle = 'rgba(0,0,0,0.35)'; ctx.lineWidth = 1;
        for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.moveTo(ax - 2 + i * 3, ay - 2); ctx.lineTo(ax - 2 + i * 3, ay + 1); ctx.stroke(); }
        ctx.restore();
    }

    function drawHead(cx, cy, r, P, img) {
        ctx.save();
        ctx.fillStyle = shade(P.skin, -0.28);
        rrPath(ctx, cx - 7, cy + r - 9, 14, 16, 5); ctx.fill();
        let g = ctx.createRadialGradient(cx - r * 0.3, cy - r * 0.35, r * 0.1, cx, cy, r);
        g.addColorStop(0, shade(P.skin, 0.15)); g.addColorStop(1, shade(P.skin, -0.2));
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, r, 0, TAU); ctx.fill();

        ctx.save();
        ctx.beginPath(); ctx.arc(cx, cy, r, 0, TAU); ctx.clip();
        if (imgOk(img)) {
            const iw = img.naturalWidth, ih = img.naturalHeight;
            const sc = Math.max(2 * r / iw, 2 * r / ih);
            const dw = iw * sc, dh = ih * sc;
            ctx.drawImage(img, cx - dw / 2, cy - dh * 0.44, dw, dh);
        } else {
            ctx.fillStyle = P.secondaryColor;
            ctx.font = `bold ${r}px Arial`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillText(P.name.charAt(0), cx, cy + 1);
        }
        let sg = ctx.createRadialGradient(cx - r * 0.3, cy - r * 0.35, r * 0.2, cx, cy, r * 1.05);
        sg.addColorStop(0, 'rgba(255,255,255,0.12)'); sg.addColorStop(0.7, 'rgba(0,0,0,0)'); sg.addColorStop(1, 'rgba(0,0,0,0.5)');
        ctx.fillStyle = sg; ctx.fillRect(cx - r, cy - r, 2 * r, 2 * r);
        ctx.restore();

        ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(0,0,0,0.55)';
        ctx.beginPath(); ctx.arc(cx, cy, r + 0.5, 0, TAU); ctx.stroke();
        ctx.lineWidth = 2.6; ctx.strokeStyle = P.secondaryColor;
        ctx.beginPath(); ctx.arc(cx, cy, r, 0, TAU); ctx.stroke();
        ctx.lineWidth = 1.5; ctx.strokeStyle = 'rgba(255,255,255,0.4)';
        ctx.beginPath(); ctx.arc(cx, cy, r - 2, Math.PI * 1.15, Math.PI * 1.6); ctx.stroke();
        ctx.restore();
    }

    // ציור ספורטאי (0,0 = מותניים; רגליים ב-+65)
    // o: { scale, lift, blend, ball, skipArms, imgKey }
    function drawAthlete(x, y, P, o) {
        const s = o.scale || PLAYER_SCALE, lift = o.lift || 0, b = o.blend || 0;
        const skin = P.skin;
        ctx.save();
        ctx.translate(x, y);
        ctx.scale(s, s);

        // צל על הרצפה
        const shY = 68 + lift / s;
        const sa = clamp(0.55 - lift / 150, 0.15, 0.55);
        let shg = ctx.createRadialGradient(0, shY, 2, 0, shY, 42);
        shg.addColorStop(0, `rgba(0,0,0,${sa})`); shg.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = shg; ctx.beginPath(); ctx.ellipse(0, shY, 42, 12, 0, 0, TAU); ctx.fill();

        // רגליים
        const jump = lift > 2;
        const legL = jump ? [[-11, 26], [-14, 46], [-10, 60]] : [[-11, 26], [-12, 46], [-11, 62]];
        const legR = jump ? [[11, 26], [15, 44], [13, 59]] : [[11, 26], [12, 46], [11, 62]];
        limb(legL, 9, skin); limb(legR, 9, skin);
        [legL, legR].forEach(leg => {
            const k = leg[1], a = leg[2];
            const m = [lerp(k[0], a[0], 0.45), lerp(k[1], a[1], 0.45)];
            ctx.save(); ctx.lineCap = 'butt';
            ctx.strokeStyle = '#f8fafc'; ctx.lineWidth = 9.8;
            ctx.beginPath(); ctx.moveTo(m[0], m[1]); ctx.lineTo(a[0], a[1] - 2); ctx.stroke();
            ctx.strokeStyle = P.secondaryColor; ctx.lineWidth = 2.2;
            ctx.beginPath(); ctx.moveTo(m[0] - 5, m[1] + 3); ctx.lineTo(m[0] + 5, m[1] + 3); ctx.stroke();
            ctx.restore();
        });
        drawShoe(legL[2][0] - 1, legL[2][1], P);
        drawShoe(legR[2][0] - 1, legR[2][1], P);

        // מכנסיים
        let sg = ctx.createLinearGradient(-23, 0, 23, 0);
        sg.addColorStop(0, shade(P.primaryColor, -0.18)); sg.addColorStop(0.5, shade(P.primaryColor, 0.08)); sg.addColorStop(1, shade(P.primaryColor, -0.3));
        ctx.fillStyle = sg;
        ctx.beginPath();
        ctx.moveTo(-19, 2); ctx.lineTo(19, 2); ctx.lineTo(23, 33); ctx.lineTo(3, 33);
        ctx.lineTo(0, 13); ctx.lineTo(-3, 33); ctx.lineTo(-23, 33); ctx.closePath(); ctx.fill();
        ctx.strokeStyle = 'rgba(0,0,0,0.35)'; ctx.lineWidth = 1.2; ctx.stroke();
        ctx.strokeStyle = 'rgba(0,0,0,0.2)'; ctx.lineWidth = 1.5;
        [[-12, 8, -14, 30], [12, 8, 14, 30], [-6, 10, -8, 28], [6, 10, 8, 28]].forEach(l => { ctx.beginPath(); ctx.moveTo(l[0], l[1]); ctx.lineTo(l[2], l[3]); ctx.stroke(); });
        ctx.strokeStyle = P.secondaryColor; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.moveTo(-19, 3); ctx.lineTo(-23, 33); ctx.moveTo(19, 3); ctx.lineTo(23, 33); ctx.stroke();
        ctx.fillStyle = P.secondaryColor; ctx.fillRect(-19, 0, 38, 4.5);
        ctx.fillStyle = 'rgba(255,255,255,0.7)'; ctx.fillRect(-1, 4, 2, 6);

        // כתפיים + גופיה
        ctx.fillStyle = skin;
        ctx.beginPath(); ctx.ellipse(-17, -33, 6.5, 7.5, 0, 0, TAU); ctx.ellipse(17, -33, 6.5, 7.5, 0, 0, TAU); ctx.fill();
        const jerseyPath = () => {
            ctx.beginPath();
            ctx.moveTo(-13, -39);
            ctx.quadraticCurveTo(-22, -37, -19, -24);
            ctx.lineTo(-18, 5);
            ctx.quadraticCurveTo(0, 9, 18, 5);
            ctx.lineTo(19, -24);
            ctx.quadraticCurveTo(22, -37, 13, -39);
            ctx.quadraticCurveTo(0, -28, -13, -39);
            ctx.closePath();
        };
        let jg = ctx.createLinearGradient(-19, 0, 19, 0);
        jg.addColorStop(0, shade(P.primaryColor, 0.12)); jg.addColorStop(0.5, P.primaryColor); jg.addColorStop(1, shade(P.primaryColor, -0.32));
        jerseyPath(); ctx.fillStyle = jg; ctx.fill();
        let jv = ctx.createLinearGradient(0, -39, 0, 8);
        jv.addColorStop(0, 'rgba(255,255,255,0.14)'); jv.addColorStop(1, 'rgba(0,0,0,0.22)');
        jerseyPath(); ctx.fillStyle = jv; ctx.fill();
        jerseyPath(); ctx.strokeStyle = P.secondaryColor; ctx.lineWidth = 2.6; ctx.stroke();
        ctx.save(); jerseyPath(); ctx.clip();
        ctx.strokeStyle = P.secondaryColor; ctx.lineWidth = 3.5;
        ctx.beginPath(); ctx.moveTo(-18, -22); ctx.lineTo(-18, 8); ctx.moveTo(18, -22); ctx.lineTo(18, 8); ctx.stroke();
        ctx.strokeStyle = 'rgba(0,0,0,0.16)'; ctx.lineWidth = 1.4;
        [[-8, -18, -6, 4], [7, -16, 8, 5], [-2, -6, -2, 6]].forEach(l => { ctx.beginPath(); ctx.moveTo(l[0], l[1]); ctx.lineTo(l[2], l[3]); ctx.stroke(); });
        ctx.restore();
        const num = String(JERSEY_NUMS[P.id] !== undefined ? JERSEY_NUMS[P.id] : 7);
        ctx.font = 'bold 17px Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(0,0,0,0.5)'; ctx.strokeText(num, 0, -11);
        ctx.fillStyle = P.secondaryColor; ctx.fillText(num, 0, -11);

        // ראש
        drawHead(0, -56, 25, P, loadedPlayerImages[o.imgKey || P.id]);

        // ידיים + כדור
        if (!o.skipArms) {
            const holdR = [[15, -33], [31, -14], [38, -27]], holdL = [[-15, -33], [-8, -12], [8, -24]];
            const shootR = [[15, -33], [26, -64], [24, -98]], shootL = [[-15, -33], [-24, -62], [-4, -90]];
            const aR = lerpPts(holdR, shootR, b), aL = lerpPts(holdL, shootL, b);
            limb(aL, 8, skin); limb(aR, 8, skin);
            if (o.ball) {
                const bx = lerp(HAND_BALL.x, RELEASE_BALL.x, b), by = lerp(HAND_BALL.y, RELEASE_BALL.y, b);
                drawBallOrFalafel(bx, by, selectedPlayer.isFalafel ? 15 : 17, 0.4, 1);
            }
            ctx.fillStyle = skin;
            [aL[2], aR[2]].forEach(h => { ctx.beginPath(); ctx.arc(h[0], h[1], 5, 0, TAU); ctx.fill(); ctx.strokeStyle = 'rgba(0,0,0,0.4)'; ctx.lineWidth = 1; ctx.stroke(); });
            ctx.fillStyle = P.secondaryColor;
            [aL, aR].forEach(a => { const w = a[2], e = a[1]; const px = lerp(w[0], e[0], 0.22), py = lerp(w[1], e[1], 0.22); ctx.beginPath(); ctx.arc(px, py, 4.3, 0, TAU); ctx.fill(); });
        }
        ctx.restore();
    }

    // ===================== רובה טחינה =====================
    function drawTahiniGun(px, py, angle, gs, recoil, flash) {
        ctx.save();
        ctx.translate(px, py); ctx.rotate(angle); ctx.scale(gs, gs); ctx.translate(-recoil, 0);
        ctx.lineJoin = 'round';

        // אחיזה
        ctx.beginPath();
        ctx.moveTo(-6, 4); ctx.lineTo(9, 4); ctx.lineTo(5, 31); ctx.quadraticCurveTo(-5, 35, -12, 29); ctx.closePath();
        let gg = ctx.createLinearGradient(-12, 0, 9, 0);
        gg.addColorStop(0, '#4a2c14'); gg.addColorStop(0.5, '#2b1a0c'); gg.addColorStop(1, '#150b04');
        ctx.fillStyle = gg; ctx.fill(); ctx.strokeStyle = '#080402'; ctx.lineWidth = 1.5; ctx.stroke();
        ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 1;
        for (let i = 0; i < 5; i++) { ctx.beginPath(); ctx.moveTo(-7 + i * 0.6, 11 + i * 4); ctx.lineTo(5 - i * 0.6, 11 + i * 4); ctx.stroke(); }

        // מגן הדק + הדק
        ctx.strokeStyle = '#2f3742'; ctx.lineWidth = 2.6;
        ctx.beginPath(); ctx.arc(15, 9, 8, 0.1, Math.PI - 0.1); ctx.stroke();
        ctx.strokeStyle = '#d4a017'; ctx.lineWidth = 2.4; ctx.lineCap = 'round';
        ctx.beginPath(); ctx.moveTo(14, 6); ctx.lineTo(15.5, 14); ctx.stroke();

        // מיכל טחינה (זכוכית)
        ctx.save();
        rrPath(ctx, 14, -37, 28, 29, 8); ctx.clip();
        ctx.fillStyle = 'rgba(210,235,255,0.18)'; ctx.fillRect(14, -37, 28, 29);
        const lvl = -37 + 29 * 0.28;
        let tg = ctx.createLinearGradient(14, 0, 42, 0);
        tg.addColorStop(0, '#e6d5a1'); tg.addColorStop(0.35, '#fff6d0'); tg.addColorStop(1, '#cdb877');
        ctx.fillStyle = tg;
        ctx.beginPath(); ctx.moveTo(14, lvl);
        for (let i = 0; i <= 28; i += 2) ctx.lineTo(14 + i, lvl + Math.sin(T * 3 + i * 0.4) * 1.4);
        ctx.lineTo(42, -8); ctx.lineTo(14, -8); ctx.closePath(); ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,0.5)';
        ctx.beginPath(); ctx.arc(22, -13 + Math.sin(T * 2) * 0.8, 1.6, 0, TAU); ctx.arc(34, -17, 1.2, 0, TAU); ctx.fill();
        ctx.restore();
        rrPath(ctx, 14, -37, 28, 29, 8);
        ctx.strokeStyle = 'rgba(255,255,255,0.65)'; ctx.lineWidth = 1.8; ctx.stroke();
        ctx.fillStyle = 'rgba(255,255,255,0.35)'; rrPath(ctx, 17, -34, 4, 23, 2); ctx.fill();
        ctx.strokeStyle = 'rgba(0,0,0,0.45)'; ctx.lineWidth = 1;
        for (let i = 0; i < 5; i++) { ctx.beginPath(); ctx.moveTo(38, -33 + i * 5); ctx.lineTo(42, -33 + i * 5); ctx.stroke(); }
        // מכסה
        let cg = ctx.createLinearGradient(0, -44, 0, -36);
        cg.addColorStop(0, '#f1f5f9'); cg.addColorStop(1, '#64748b');
        ctx.fillStyle = cg; rrPath(ctx, 18, -43, 20, 8, 3); ctx.fill(); ctx.strokeStyle = '#1e293b'; ctx.lineWidth = 1.2; ctx.stroke();
        ctx.fillStyle = '#b8860b'; ctx.fillRect(26, -46, 4, 4);

        // גוף
        let bg = ctx.createLinearGradient(0, -10, 0, 8);
        bg.addColorStop(0, '#aab4c3'); bg.addColorStop(0.45, '#586374'); bg.addColorStop(1, '#222a37');
        ctx.fillStyle = bg; rrPath(ctx, -17, -10, 66, 17, 6); ctx.fill();
        ctx.strokeStyle = '#0b1220'; ctx.lineWidth = 1.6; ctx.stroke();
        ctx.strokeStyle = 'rgba(255,255,255,0.45)'; ctx.lineWidth = 1.4;
        ctx.beginPath(); ctx.moveTo(-11, -8); ctx.lineTo(43, -8); ctx.stroke();
        let gold = ctx.createLinearGradient(0, -10, 0, 7);
        gold.addColorStop(0, '#fde68a'); gold.addColorStop(0.5, '#d4a017'); gold.addColorStop(1, '#7c5a07');
        ctx.fillStyle = gold; ctx.fillRect(8, -10, 5, 17); ctx.fillRect(32, -10, 3, 17);
        ctx.fillStyle = '#e5e7eb';
        [[-12, -4], [-12, 3], [44, -4], [44, 3]].forEach(r => { ctx.beginPath(); ctx.arc(r[0], r[1], 1.3, 0, TAU); ctx.fill(); });

        // מד לחץ
        ctx.save(); ctx.translate(-3, -17);
        let bz = ctx.createLinearGradient(-8, -8, 8, 8);
        bz.addColorStop(0, '#fde68a'); bz.addColorStop(1, '#7c5a07');
        ctx.fillStyle = bz; ctx.beginPath(); ctx.arc(0, 0, 8, 0, TAU); ctx.fill();
        ctx.fillStyle = '#f8fafc'; ctx.beginPath(); ctx.arc(0, 0, 6.2, 0, TAU); ctx.fill();
        ctx.strokeStyle = '#ef4444'; ctx.lineWidth = 1.8;
        ctx.beginPath(); ctx.arc(0, 0, 4.8, -0.5, 0.9); ctx.stroke();
        ctx.strokeStyle = '#111827'; ctx.lineWidth = 1.2; ctx.lineCap = 'round';
        const na = -2.3 + (0.9 + flash * 1.6) + Math.sin(T * 5) * 0.05;
        ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(na) * 5, Math.sin(na) * 5); ctx.stroke();
        ctx.fillStyle = 'rgba(255,255,255,0.45)'; ctx.beginPath(); ctx.ellipse(-2, -3, 3, 1.6, -0.6, 0, TAU); ctx.fill();
        ctx.restore();
        ctx.strokeStyle = '#334155'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(-3, -10); ctx.lineTo(-3, -9); ctx.stroke();

        // קנה
        let bar = ctx.createLinearGradient(0, -6, 0, 6);
        bar.addColorStop(0, '#e2e8f0'); bar.addColorStop(0.5, '#64748b'); bar.addColorStop(1, '#1e293b');
        ctx.fillStyle = bar; ctx.fillRect(48, -6, 38, 11);
        ctx.strokeStyle = '#0b1220'; ctx.lineWidth = 1.2; ctx.strokeRect(48, -6, 38, 11);
        ctx.fillStyle = gold; ctx.fillRect(58, -7, 4, 13); ctx.fillRect(72, -7, 4, 13);

        // זרבובית
        ctx.beginPath(); ctx.moveTo(86, -5); ctx.lineTo(98, -3); ctx.lineTo(98, 2); ctx.lineTo(86, 4); ctx.closePath();
        let ng = ctx.createLinearGradient(0, -5, 0, 4);
        ng.addColorStop(0, '#f2b077'); ng.addColorStop(1, '#7a3d12');
        ctx.fillStyle = ng; ctx.fill(); ctx.strokeStyle = '#2a1405'; ctx.lineWidth = 1.2; ctx.stroke();
        ctx.fillStyle = '#0a0a0a'; ctx.beginPath(); ctx.ellipse(98, -0.5, 1.8, 2.7, 0, 0, TAU); ctx.fill();

        // אחיזת משאבה
        let pg = ctx.createLinearGradient(0, 5, 0, 15);
        pg.addColorStop(0, '#6b4423'); pg.addColorStop(1, '#2b1a0c');
        ctx.fillStyle = pg; rrPath(ctx, 52, 5, 24, 10, 4); ctx.fill(); ctx.strokeStyle = '#0b0603'; ctx.lineWidth = 1.2; ctx.stroke();
        ctx.strokeStyle = 'rgba(255,255,255,0.14)'; ctx.lineWidth = 1;
        for (let i = 0; i < 6; i++) { ctx.beginPath(); ctx.moveTo(56 + i * 3.4, 6); ctx.lineTo(56 + i * 3.4, 14); ctx.stroke(); }

        // טיפת טחינה מהזרבובית
        if (flash < 0.1) {
            const dr = 1.8 + (Math.sin(T * 2) + 1) * 1.1;
            ctx.fillStyle = '#fff6d0'; ctx.beginPath(); ctx.ellipse(98, 4 + dr, dr * 0.8, dr * 1.2, 0, 0, TAU); ctx.fill();
        }

        // פלאש יריה
        if (flash > 0.04) {
            ctx.save(); ctx.globalCompositeOperation = 'lighter';
            const R = 38 * flash + 10;
            let fg = ctx.createRadialGradient(100, -0.5, 1, 100, -0.5, R);
            fg.addColorStop(0, 'rgba(255,248,210,0.95)'); fg.addColorStop(0.5, 'rgba(255,220,130,0.45)'); fg.addColorStop(1, 'rgba(255,200,80,0)');
            ctx.fillStyle = fg; ctx.beginPath(); ctx.arc(100, -0.5, R, 0, TAU); ctx.fill();
            ctx.restore();
        }
        ctx.restore();
    }

    function drawShooter() {
        const sp = shooterPos(), s = 1.1;
        drawAthlete(sp.x, sp.y, PELEG, { scale: s, imgKey: 'peleg', skipArms: true, lift: 0 });
        const pv = gunPivot();
        drawTahiniGun(pv.x, pv.y, gunAngle, GUN_SCALE, gunRecoil, gunFlash);
        // ידיים על הרובה
        const rot = (lx, ly) => ({ x: pv.x + (Math.cos(gunAngle) * lx - Math.sin(gunAngle) * ly) * GUN_SCALE, y: pv.y + (Math.sin(gunAngle) * lx + Math.cos(gunAngle) * ly) * GUN_SCALE });
        const handR = rot(-1 - gunRecoil, 18), handL = rot(62 - gunRecoil, 10);
        const shR = { x: sp.x + 15 * s, y: sp.y - 33 * s }, shL = { x: sp.x - 15 * s, y: sp.y - 33 * s };
        const elbow = (a, b, dx, dy) => [(a.x + b.x) / 2 + dx, (a.y + b.y) / 2 + dy];
        limb([[shR.x, shR.y], elbow(shR, handR, 4, 12), [handR.x, handR.y]], 8.5, PELEG.skin);
        limb([[shL.x, shL.y], elbow(shL, handL, -2, 14), [handL.x, handL.y]], 8.5, PELEG.skin);
        ctx.fillStyle = PELEG.skin;
        [handR, handL].forEach(h => { ctx.beginPath(); ctx.arc(h.x, h.y, 5.2, 0, TAU); ctx.fill(); ctx.strokeStyle = 'rgba(0,0,0,0.4)'; ctx.lineWidth = 1; ctx.stroke(); });
    }

    function drawTahiniProjectiles() {
        tahiniShots.forEach(s => {
            s.trail.forEach((p, i) => {
                const f = (i + 1) / s.trail.length;
                ctx.fillStyle = `rgba(255,248,215,${f * 0.5})`;
                ctx.beginPath(); ctx.arc(p[0], p[1], 3 + f * 7, 0, TAU); ctx.fill();
            });
            ctx.save();
            ctx.shadowColor = '#facc15'; ctx.shadowBlur = 14;
            let g = ctx.createRadialGradient(s.x - 3, s.y - 3, 1, s.x, s.y, 13);
            g.addColorStop(0, '#ffffff'); g.addColorStop(0.6, '#fff6d0'); g.addColorStop(1, '#d9c98a');
            ctx.fillStyle = g; ctx.beginPath(); ctx.arc(s.x, s.y, 12, 0, TAU); ctx.fill();
            ctx.restore();
        });
    }

    function drawSplash(sp) {
        const k = easeOutBack(clamp(sp.t / 0.22, 0, 1));
        ctx.save();
        ctx.translate(sp.x, sp.y); ctx.scale(k, k);
        sp.drips.forEach(d => {
            const len = Math.min(d.max, d.len0 + sp.t * d.speed);
            ctx.strokeStyle = '#f3ebc8'; ctx.lineCap = 'round'; ctx.lineWidth = d.w;
            ctx.beginPath(); ctx.moveTo(d.dx, d.dy); ctx.lineTo(d.dx, d.dy + len); ctx.stroke();
            ctx.fillStyle = '#f3ebc8'; ctx.beginPath(); ctx.arc(d.dx, d.dy + len, d.w * 0.78, 0, TAU); ctx.fill();
        });
        ctx.shadowColor = 'rgba(70,45,0,0.45)'; ctx.shadowBlur = 6; ctx.shadowOffsetY = 2;
        sp.blobs.forEach(b => {
            const gr = ctx.createRadialGradient(b.dx - b.rx * 0.3, b.dy - b.ry * 0.3, 2, b.dx, b.dy, Math.max(b.rx, b.ry));
            gr.addColorStop(0, '#fffef5'); gr.addColorStop(0.7, '#f3ecc8'); gr.addColorStop(1, '#d9cc99');
            ctx.fillStyle = gr; ctx.beginPath(); ctx.ellipse(b.dx, b.dy, b.rx, b.ry, b.rot, 0, TAU); ctx.fill();
        });
        sp.drops.forEach(d => { ctx.fillStyle = '#f6efd2'; ctx.beginPath(); ctx.arc(d.dx, d.dy, d.r, 0, TAU); ctx.fill(); });
        ctx.shadowColor = 'transparent';
        sp.blobs.slice(0, 3).forEach(b => {
            ctx.fillStyle = 'rgba(255,255,255,0.7)';
            ctx.beginPath(); ctx.ellipse(b.dx - b.rx * 0.3, b.dy - b.ry * 0.4, b.rx * 0.35, b.ry * 0.2, b.rot, 0, TAU); ctx.fill();
        });
        ctx.restore();
    }

    function drawBubble(x, y, text, stroke, pop) {
        if (pop <= 0) return;
        ctx.save();
        ctx.font = 'bold 15px "Segoe UI", Arial';
        const tw = ctx.measureText(text).width + 30, h = 34;
        const sc = easeOutBack(clamp(pop, 0, 1));
        ctx.translate(x, y); ctx.scale(sc, sc);
        ctx.shadowColor = 'rgba(0,0,0,0.5)'; ctx.shadowBlur = 10; ctx.shadowOffsetY = 3;
        ctx.fillStyle = '#ffffff'; ctx.strokeStyle = stroke; ctx.lineWidth = 2.5;
        ctx.beginPath(); ctx.moveTo(-10, -2); ctx.lineTo(0, 16); ctx.lineTo(10, -2); ctx.closePath(); ctx.fill(); ctx.stroke();
        rrPath(ctx, -tw / 2, -h, tw, h, 13); ctx.fill(); ctx.stroke();
        ctx.shadowColor = 'transparent';
        ctx.fillStyle = '#ffffff'; ctx.fillRect(-9, -4, 18, 5);
        ctx.fillStyle = '#0f172a'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(text, 0, -h / 2 + 1);
        ctx.restore();
    }

    // ===================== סל / רשת / פיתה =====================
    function drawHoopBack(cx, hoopY) {
        const ft = H * 0.30;
        ctx.save();
        // עמוד תמיכה
        let pg = ctx.createLinearGradient(cx - 9, 0, cx + 9, 0);
        pg.addColorStop(0, '#475569'); pg.addColorStop(0.5, '#cbd5e1'); pg.addColorStop(1, '#334155');
        ctx.fillStyle = pg; ctx.fillRect(cx - 9, hoopY + 8, 18, ft - hoopY);
        ctx.fillStyle = '#1e293b'; ctx.fillRect(cx - 28, ft - 2, 56, 10);
        ctx.fillStyle = 'rgba(37,99,235,0.8)'; ctx.fillRect(cx - 28, ft + 2, 56, 4);

        // לוח
        const bx = cx - 100, by = hoopY - 112, bw = 200, bh = 124;
        ctx.shadowColor = 'rgba(56,189,248,0.55)'; ctx.shadowBlur = 22;
        let gl = ctx.createLinearGradient(bx, by, bx + bw, by + bh);
        gl.addColorStop(0, 'rgba(190,225,255,0.34)'); gl.addColorStop(0.5, 'rgba(255,255,255,0.12)'); gl.addColorStop(1, 'rgba(150,200,255,0.26)');
        ctx.fillStyle = gl; rrPath(ctx, bx, by, bw, bh, 6); ctx.fill();
        ctx.shadowColor = 'transparent';
        ctx.save(); rrPath(ctx, bx, by, bw, bh, 6); ctx.clip();
        ctx.fillStyle = 'rgba(255,255,255,0.12)';
        ctx.beginPath(); ctx.moveTo(bx + 20, by); ctx.lineTo(bx + 62, by); ctx.lineTo(bx + 6, by + bh); ctx.lineTo(bx - 36, by + bh); ctx.fill();
        ctx.beginPath(); ctx.moveTo(bx + 84, by); ctx.lineTo(bx + 100, by); ctx.lineTo(bx + 44, by + bh); ctx.lineTo(bx + 28, by + bh); ctx.fill();
        ctx.restore();
        rrPath(ctx, bx, by, bw, bh, 6); ctx.lineWidth = 6; ctx.strokeStyle = '#e2e8f0'; ctx.stroke();
        rrPath(ctx, bx + 3, by + 3, bw - 6, bh - 6, 4); ctx.lineWidth = 2; ctx.strokeStyle = '#38bdf8'; ctx.stroke();
        ctx.strokeStyle = '#ef4444'; ctx.lineWidth = 3.5;
        ctx.strokeRect(cx - 36, hoopY - 52, 72, 52);
        ctx.fillStyle = '#cbd5e1';
        [[bx + 8, by + 8], [bx + bw - 8, by + 8], [bx + 8, by + bh - 8], [bx + bw - 8, by + bh - 8]].forEach(p => { ctx.beginPath(); ctx.arc(p[0], p[1], 2.6, 0, TAU); ctx.fill(); });

        // זרוע לחישוק
        let ag = ctx.createLinearGradient(0, hoopY - 6, 0, hoopY + 10);
        ag.addColorStop(0, '#94a3b8'); ag.addColorStop(1, '#334155');
        ctx.fillStyle = ag; ctx.fillRect(cx - 16, hoopY - 6, 32, 16);

        // חצי אחורי של החישוק
        ctx.translate(0, Math.sin(T * 55) * rimShake * 2.5);
        ctx.lineCap = 'round'; ctx.strokeStyle = '#9a3412'; ctx.lineWidth = 5;
        ctx.beginPath(); ctx.ellipse(cx, hoopY, 44, 13, 0, Math.PI, TAU); ctx.stroke();
        ctx.restore();
    }

    function drawNet(cx, hoopY) {
        const L = 5, N = 14, stepA = TAU / N, depth = 58 + netSwish * 14;
        const pts = [];
        for (let j = 0; j <= L; j++) {
            const f = j / L, rx = lerp(44, 24, f), ry = rx * 0.29, yy = hoopY + f * depth;
            const sway = Math.sin(T * 16 + f * 3) * netSwish * 9 * f;
            pts[j] = [];
            for (let k = 0; k < N; k++) {
                const a = (k + (j % 2 ? 0.5 : 0)) * stepA;
                pts[j].push([cx + Math.cos(a) * rx + sway, yy + Math.sin(a) * ry]);
            }
        }
        ctx.save();
        ctx.strokeStyle = 'rgba(255,255,255,0.88)'; ctx.lineWidth = 1.6; ctx.lineCap = 'round';
        ctx.shadowColor = 'rgba(0,0,0,0.35)'; ctx.shadowBlur = 2;
        ctx.beginPath();
        for (let j = 0; j < L; j++) {
            for (let k = 0; k < N; k++) {
                const a = pts[j][k], b1 = pts[j + 1][k];
                const b2 = j % 2 === 0 ? pts[j + 1][(k - 1 + N) % N] : pts[j + 1][(k + 1) % N];
                ctx.moveTo(a[0], a[1]); ctx.lineTo(b1[0], b1[1]);
                ctx.moveTo(a[0], a[1]); ctx.lineTo(b2[0], b2[1]);
            }
        }
        ctx.stroke();
        ctx.restore();
    }

    function drawHoopFront(cx, hoopY) {
        ctx.save();
        ctx.translate(0, Math.sin(T * 55) * rimShake * 2.5);
        drawNet(cx, hoopY);
        ctx.lineCap = 'round';
        let rg = ctx.createLinearGradient(0, hoopY - 4, 0, hoopY + 16);
        rg.addColorStop(0, '#ff9a4d'); rg.addColorStop(0.5, '#ea580c'); rg.addColorStop(1, '#9a3412');
        ctx.strokeStyle = rg; ctx.lineWidth = 6.5;
        ctx.beginPath(); ctx.ellipse(cx, hoopY, 44, 13, 0, 0, Math.PI); ctx.stroke();
        ctx.strokeStyle = 'rgba(255,225,190,0.75)'; ctx.lineWidth = 1.6;
        ctx.beginPath(); ctx.ellipse(cx, hoopY - 1.5, 43, 12, 0, 0.15, Math.PI - 0.15); ctx.stroke();
        ctx.restore();
    }

    function drawPitaBack(cx, hoopY) {
        const cy = hoopY + 20, R = 92;
        ctx.save();
        ctx.translate(0, Math.sin(T * 55) * rimShake * 2.5);
        if (isFalafelMode) { ctx.shadowColor = '#facc15'; ctx.shadowBlur = 28; }
        else { ctx.shadowColor = 'rgba(0,0,0,0.5)'; ctx.shadowBlur = 14; ctx.shadowOffsetY = 6; }
        let g = ctx.createRadialGradient(cx - 14, cy + 20, 10, cx, cy + 30, R + 20);
        g.addColorStop(0, '#f6dfb0'); g.addColorStop(0.6, '#dfb372'); g.addColorStop(1, '#a8743a');
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI); ctx.closePath(); ctx.fill();
        ctx.shadowColor = 'transparent';
        ctx.strokeStyle = '#8a5a28'; ctx.lineWidth = 4;
        ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI); ctx.stroke();
        // כתמי קלייה
        ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI); ctx.clip();
        const rnd = mulberry32(5);
        for (let i = 0; i < 22; i++) {
            ctx.fillStyle = `rgba(120,70,20,${0.1 + rnd() * 0.18})`;
            ctx.beginPath(); ctx.ellipse(cx + (rnd() - 0.5) * 170, cy + rnd() * 85, 4 + rnd() * 8, 3 + rnd() * 5, rnd() * 3, 0, TAU); ctx.fill();
        }
        ctx.restore();
        // פנים הכיס
        let ig = ctx.createLinearGradient(0, cy - 18, 0, cy + 18);
        ig.addColorStop(0, '#5a3a14'); ig.addColorStop(1, '#fff0c0');
        ctx.fillStyle = ig; ctx.beginPath(); ctx.ellipse(cx, cy, R - 12, 17, 0, 0, TAU); ctx.fill();
        ctx.strokeStyle = '#6b4620'; ctx.lineWidth = 3; ctx.stroke();

        // מילוי שמציץ מלמעלה
        const items = [
            { t: 'leaf', dx: -62, dy: -8 }, { t: 'ball', dx: -42, dy: -16 }, { t: 'leaf', dx: -22, dy: -10 },
            { t: 'tom', dx: -4, dy: -12 }, { t: 'ball', dx: 16, dy: -17 }, { t: 'leaf', dx: 36, dy: -10 },
            { t: 'ball', dx: 55, dy: -14 }, { t: 'leaf', dx: 68, dy: -6 }
        ];
        items.forEach(it => {
            const ix = cx + it.dx, iy = cy + it.dy;
            if (it.t === 'leaf') {
                let lg = ctx.createLinearGradient(ix - 12, iy - 10, ix + 12, iy + 10);
                lg.addColorStop(0, '#86efac'); lg.addColorStop(1, '#15803d');
                ctx.fillStyle = lg; ctx.beginPath(); ctx.ellipse(ix, iy, 13, 9, -0.4, 0, TAU); ctx.fill();
                ctx.strokeStyle = 'rgba(0,60,20,0.55)'; ctx.lineWidth = 1;
                ctx.beginPath(); ctx.moveTo(ix - 9, iy + 4); ctx.lineTo(ix + 9, iy - 4); ctx.stroke();
            } else if (it.t === 'tom') {
                let tg = ctx.createRadialGradient(ix - 3, iy - 3, 1, ix, iy, 10);
                tg.addColorStop(0, '#fca5a5'); tg.addColorStop(1, '#b91c1c');
                ctx.fillStyle = tg; ctx.beginPath(); ctx.arc(ix, iy, 9, 0, TAU); ctx.fill();
            } else {
                drawFalafelBall(ix, iy, 10, it.dx, false, 1);
            }
        });
        ctx.restore();
    }

    function drawPitaFront(cx, hoopY) {
        const cy = hoopY + 20, R = 92;
        ctx.save();
        ctx.translate(0, Math.sin(T * 55) * rimShake * 2.5);
        ctx.beginPath();
        ctx.moveTo(cx - R, cy); ctx.lineTo(cx - (R - 12), cy);
        ctx.ellipse(cx, cy, R - 12, 17, 0, Math.PI, 0, true);
        ctx.lineTo(cx + R, cy);
        ctx.arc(cx, cy, R, 0, Math.PI, false);
        ctx.closePath();
        let g = ctx.createRadialGradient(cx - 20, cy + 30, 10, cx, cy + 40, R + 10);
        g.addColorStop(0, '#fbe7bd'); g.addColorStop(0.6, '#e6bd7f'); g.addColorStop(1, '#ae7a40');
        ctx.fillStyle = g; ctx.fill();
        ctx.strokeStyle = '#8a5a28'; ctx.lineWidth = 3.5; ctx.stroke();
        ctx.save(); ctx.clip();
        const rnd = mulberry32(11);
        for (let i = 0; i < 24; i++) {
            ctx.fillStyle = `rgba(130,78,24,${0.08 + rnd() * 0.16})`;
            ctx.beginPath(); ctx.ellipse(cx + (rnd() - 0.5) * 170, cy + 14 + rnd() * 78, 3 + rnd() * 8, 2 + rnd() * 5, rnd() * 3, 0, TAU); ctx.fill();
        }
        ctx.restore();
        // טחינה זולגת על קצה הפיתה
        ctx.strokeStyle = '#fffbe6'; ctx.lineWidth = 5; ctx.lineCap = 'round';
        ctx.shadowColor = 'rgba(0,0,0,0.35)'; ctx.shadowBlur = 3;
        ctx.beginPath();
        for (let i = 0; i <= 150; i += 3) {
            const a = Math.PI * (i / 150);
            const px = cx + Math.cos(a) * (R - 12 - 2) * -1 * -1;
            const x = cx + (R - 14) * Math.cos(Math.PI - a);
            const y = cy + 17 * Math.sin(a) + 6 + Math.sin(i * 0.5) * 2;
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.stroke();
        ctx.shadowColor = 'transparent';
        ctx.fillStyle = '#fff7d6'; ctx.font = 'bold 18px "Segoe UI", Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
        ctx.shadowColor = 'rgba(0,0,0,0.8)'; ctx.shadowBlur = 6;
        ctx.fillText('פלאפל חן 🥙', cx, hoopY - 26);
        ctx.restore();
    }

    // ===================== רקעים =====================
    function drawArena() {
        const cx = W / 2, ft = H * 0.30;
        // קיר אחורי
        let g = ctx.createLinearGradient(0, 0, 0, ft);
        g.addColorStop(0, '#04060d'); g.addColorStop(1, '#111a2e');
        ctx.fillStyle = g; ctx.fillRect(0, 0, W, ft + 2);

        // קהל
        crowd.forEach(c => {
            const y = c.y + Math.sin(T * 3 + c.ph) * (c.up ? 3 : 0.8);
            ctx.fillStyle = c.shirt; ctx.beginPath(); ctx.ellipse(c.x, y + c.r * 1.7, c.r * 1.35, c.r * 1.1, 0, 0, TAU); ctx.fill();
            if (c.up) {
                ctx.strokeStyle = c.skin; ctx.lineWidth = c.r * 0.5; ctx.lineCap = 'round';
                ctx.beginPath(); ctx.moveTo(c.x - c.r, y + c.r * 1.5); ctx.lineTo(c.x - c.r * 1.3, y - c.r * 0.8);
                ctx.moveTo(c.x + c.r, y + c.r * 1.5); ctx.lineTo(c.x + c.r * 1.3, y - c.r * 0.8); ctx.stroke();
            }
            ctx.fillStyle = c.skin; ctx.beginPath(); ctx.arc(c.x, y, c.r, 0, TAU); ctx.fill();
            ctx.fillStyle = c.hair; ctx.beginPath(); ctx.arc(c.x, y - c.r * 0.12, c.r, Math.PI * 1.05, Math.PI * 1.95); ctx.fill();
        });
        let og = ctx.createLinearGradient(0, 0, 0, ft);
        og.addColorStop(0, 'rgba(3,6,14,0.55)'); og.addColorStop(1, 'rgba(3,6,14,0.78)');
        ctx.fillStyle = og; ctx.fillRect(0, 0, W, ft + 2);

        // לוח LED
        const ly = ft - 20;
        let lg = ctx.createLinearGradient(0, ly, 0, ly + 18);
        lg.addColorStop(0, '#0b1224'); lg.addColorStop(1, '#16223f');
        ctx.fillStyle = lg; ctx.fillRect(0, ly, W, 18);
        ctx.save(); ctx.beginPath(); ctx.rect(0, ly, W, 18); ctx.clip();
        ctx.font = 'bold 12px Arial'; ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
        const label = '  HAPOEL MARNIN TIVON  ★  NBA ALL-STAR SHOOTOUT  ★  ';
        const tw = ctx.measureText(label).width;
        ctx.fillStyle = '#7dd3fc';
        for (let x = -((T * 60) % tw); x < W; x += tw) ctx.fillText(label, x, ly + 10);
        ctx.restore();
        ctx.fillStyle = 'rgba(56,189,248,0.7)'; ctx.fillRect(0, ly + 18, W, 2);

        // פרקט
        let fg = ctx.createLinearGradient(0, ft, 0, H);
        fg.addColorStop(0, '#d29a58'); fg.addColorStop(0.45, '#b97a38'); fg.addColorStop(1, '#6e4118');
        ctx.fillStyle = fg; ctx.fillRect(0, ft, W, H - ft);
        const vpY = ft - H * 0.45;
        const sc = y => (y - vpY) / (H - vpY);
        const xAt = (i, y) => cx + i * W * 0.04 * sc(y);
        for (let i = -34; i < 34; i++) {
            if (i % 2 === 0) {
                ctx.fillStyle = 'rgba(60,28,4,0.07)';
                ctx.beginPath(); ctx.moveTo(xAt(i, ft), ft); ctx.lineTo(xAt(i + 1, ft), ft); ctx.lineTo(xAt(i + 1, H), H); ctx.lineTo(xAt(i, H), H); ctx.closePath(); ctx.fill();
            }
        }
        ctx.strokeStyle = 'rgba(70,35,6,0.32)'; ctx.lineWidth = 1;
        ctx.beginPath();
        for (let i = -34; i <= 34; i++) { ctx.moveTo(xAt(i, ft), ft); ctx.lineTo(xAt(i, H), H); }
        ctx.stroke();

        // סימוני מגרש
        const base = ft + 8, ftLine = H * 0.63;
        ctx.save();
        ctx.fillStyle = 'rgba(37,99,235,0.3)';
        ctx.beginPath(); ctx.moveTo(cx - 150, base); ctx.lineTo(cx + 150, base); ctx.lineTo(cx + 205, ftLine); ctx.lineTo(cx - 205, ftLine); ctx.closePath(); ctx.fill();
        ctx.strokeStyle = 'rgba(255,255,255,0.82)'; ctx.lineWidth = 3; ctx.lineJoin = 'round';
        ctx.stroke();
        ctx.beginPath(); ctx.moveTo(0, base); ctx.lineTo(W, base); ctx.stroke();
        ctx.beginPath(); ctx.ellipse(cx, ftLine, 120, 38, 0, Math.PI, TAU); ctx.stroke();
        ctx.setLineDash([10, 9]);
        ctx.beginPath(); ctx.ellipse(cx, ftLine, 120, 38, 0, 0, Math.PI); ctx.stroke();
        ctx.setLineDash([]);
        ctx.beginPath(); ctx.ellipse(cx, base + 30, 72, 52, 0, 0, Math.PI); ctx.stroke();
        ctx.beginPath(); ctx.ellipse(cx, base, W * 0.30, H * 0.60, 0, 0, Math.PI); ctx.stroke();
        ctx.save();
        ctx.translate(cx, H * 0.46); ctx.scale(1, 0.4);
        ctx.fillStyle = 'rgba(255,255,255,0.15)'; ctx.font = 'bold 54px Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText('TIVON', 0, 0);
        ctx.restore();
        ctx.restore();

        // ברק פרקט
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        let sh = ctx.createRadialGradient(cx, H * 0.55, 20, cx, H * 0.55, W * 0.5);
        sh.addColorStop(0, 'rgba(255,235,200,0.16)'); sh.addColorStop(1, 'rgba(255,235,200,0)');
        ctx.fillStyle = sh; ctx.fillRect(0, ft, W, H - ft);
        // זרקורים
        [0.2, 0.5, 0.8].forEach((fx, i) => {
            const x0 = W * fx, sw = Math.sin(T * 0.6 + i * 2) * W * 0.03;
            let cg = ctx.createLinearGradient(x0, 0, x0 + sw, H * 0.9);
            cg.addColorStop(0, 'rgba(130,180,255,0.17)'); cg.addColorStop(1, 'rgba(130,180,255,0)');
            ctx.fillStyle = cg;
            ctx.beginPath(); ctx.moveTo(x0 - 10, 0); ctx.lineTo(x0 + 10, 0); ctx.lineTo(x0 + sw + W * 0.12, H * 0.9); ctx.lineTo(x0 + sw - W * 0.12, H * 0.9); ctx.closePath(); ctx.fill();
        });
        ctx.restore();
    }

    // ===================== מוד לבה: הר געש + רצפת לבה =====================
    const LAVA_BOMBS = (() => {
        const r = mulberry32(31), a = [];
        for (let i = 0; i < 20; i++) a.push({ dx: (r() - 0.5) * 1.3, hh: 0.55 + r() * 0.8, sz: 2.5 + r() * 4, off: r(), sp: 0.22 + r() * 0.22 });
        return a;
    })();
    const LAVA_PLATES = (() => {
        const r = mulberry32(47), a = [];
        for (let i = 0; i < 70; i++) {
            const verts = [];
            for (let k = 0; k < 8; k++) verts.push(0.62 + r() * 0.5);
            a.push({ u: r(), v: Math.pow(r(), 0.85), size: 0.6 + r() * 0.9, verts, sp: 0.5 + r() * 0.7 });
        }
        a.sort((p, q) => p.v - q.v);
        return a;
    })();
    const LAVA_BUBBLES = (() => {
        const r = mulberry32(83), a = [];
        for (let i = 0; i < 18; i++) a.push({ u: r(), v: Math.pow(r(), 0.8), off: r(), sp: 0.18 + r() * 0.25 });
        return a;
    })();

    function drawVolcanoCone(vx, baseW, topY, ft, streams) {
        const craterW = baseW * 0.11, h = ft - topY;
        const cone = () => {
            ctx.beginPath();
            ctx.moveTo(vx - baseW / 2, ft);
            ctx.quadraticCurveTo(vx - baseW * 0.2, ft - h * 0.4, vx - craterW, topY);
            ctx.quadraticCurveTo(vx, topY + h * 0.06, vx + craterW, topY);
            ctx.quadraticCurveTo(vx + baseW * 0.2, ft - h * 0.4, vx + baseW / 2, ft);
            ctx.closePath();
        };
        let g = ctx.createLinearGradient(0, topY, 0, ft);
        g.addColorStop(0, '#2a0f0a'); g.addColorStop(0.5, '#1b0a07'); g.addColorStop(1, '#2d1409');
        cone(); ctx.fillStyle = g; ctx.fill();
        // טקסטורת סלע
        ctx.save(); cone(); ctx.clip();
        const rr = mulberry32(Math.floor(vx) + 5);
        for (let i = 0; i < 40; i++) {
            const t = rr(), x = vx + (rr() - 0.5) * baseW * (0.2 + t * 0.8), y = topY + t * h;
            ctx.fillStyle = rr() > 0.5 ? 'rgba(0,0,0,0.28)' : 'rgba(120,60,30,0.14)';
            ctx.beginPath(); ctx.ellipse(x, y, 10 + rr() * 26, 4 + rr() * 8, rr() * 3, 0, TAU); ctx.fill();
        }
        // תאורת קצה מהלבה
        let eg = ctx.createLinearGradient(vx - baseW / 2, 0, vx + baseW / 2, 0);
        eg.addColorStop(0, 'rgba(255,90,20,0.28)'); eg.addColorStop(0.3, 'rgba(255,90,20,0)'); eg.addColorStop(0.7, 'rgba(255,90,20,0)'); eg.addColorStop(1, 'rgba(255,90,20,0.28)');
        ctx.fillStyle = eg; ctx.fillRect(vx - baseW / 2, topY, baseW, h);

        // זרמי לבה במורד ההר
        if (streams) {
            ctx.lineCap = 'round'; ctx.lineJoin = 'round';
            [[-0.45, 0], [0.4, 1], [0.05, 2], [-0.2, 3]].forEach(st => {
                ctx.beginPath();
                for (let k = 0; k <= 14; k++) {
                    const t = k / 14, hw = craterW + (baseW / 2 - craterW) * Math.pow(t, 1.5);
                    const x = vx + st[0] * hw * 1.7 + Math.sin(t * 9 + st[1] * 2) * baseW * 0.012 * t;
                    const y = topY + 6 + t * (h - 6);
                    k ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
                }
                ctx.setLineDash([]);
                ctx.shadowColor = '#ff5a14'; ctx.shadowBlur = 12;
                ctx.strokeStyle = 'rgba(255,80,16,0.7)'; ctx.lineWidth = 4; ctx.stroke();
                ctx.shadowBlur = 0;
                ctx.setLineDash([16, 14]); ctx.lineDashOffset = -T * 46 - st[1] * 9;
                ctx.strokeStyle = '#fde047'; ctx.lineWidth = 1.8; ctx.stroke();
                ctx.setLineDash([]);
            });
        }
        ctx.restore();

        // זוהר מכתש
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        const pulse = 0.85 + Math.sin(T * 2.2 + vx) * 0.15, R = baseW * 0.42 * pulse;
        let cg = ctx.createRadialGradient(vx, topY, 2, vx, topY, R);
        cg.addColorStop(0, 'rgba(255,200,90,0.85)'); cg.addColorStop(0.25, 'rgba(255,100,20,0.45)'); cg.addColorStop(1, 'rgba(255,60,10,0)');
        ctx.fillStyle = cg; ctx.beginPath(); ctx.arc(vx, topY, R, 0, TAU); ctx.fill();
        ctx.restore();
        // לבה בפתח המכתש
        let lg = ctx.createLinearGradient(vx - craterW, 0, vx + craterW, 0);
        lg.addColorStop(0, '#ff6a10'); lg.addColorStop(0.5, '#fde047'); lg.addColorStop(1, '#ff6a10');
        ctx.fillStyle = lg; ctx.beginPath(); ctx.ellipse(vx, topY + 1, craterW * 0.95, craterW * 0.22, 0, 0, TAU); ctx.fill();
    }

    function drawEruption(vx, topY, scale) {
        const smokeCols = 10;
        // עשן אפר שעולה
        for (let i = 0; i < smokeCols; i++) {
            const ph = (T * 0.07 + i / smokeCols) % 1;
            const x = vx + Math.sin(ph * 5 + i) * W * 0.02 * scale + ph * W * 0.1 * scale;
            const y = topY - ph * H * 0.2 * scale, r = H * (0.025 + ph * 0.07) * scale;
            const a = Math.sin(Math.min(ph, 1) * Math.PI) * 0.55;
            let sg = ctx.createRadialGradient(x, y, 1, x, y, r);
            sg.addColorStop(0, `rgba(70,30,20,${a})`); sg.addColorStop(1, 'rgba(25,10,8,0)');
            ctx.fillStyle = sg; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
        }
        // פצצות לבה
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        LAVA_BOMBS.forEach(b => {
            const ph = (T * b.sp + b.off) % 1;
            const peak = H * 0.17 * b.hh * scale;
            const x = vx + b.dx * W * 0.09 * scale * ph;
            const y = topY - 4 * peak * ph * (1 - ph) + ph * ph * H * 0.05 * scale;
            const a = Math.sin(ph * Math.PI), s = b.sz * scale;
            let bg = ctx.createRadialGradient(x, y, 0, x, y, s * 3);
            bg.addColorStop(0, `rgba(255,200,90,${0.55 * a})`); bg.addColorStop(1, 'rgba(255,80,10,0)');
            ctx.fillStyle = bg; ctx.beginPath(); ctx.arc(x, y, s * 3, 0, TAU); ctx.fill();
            ctx.fillStyle = `rgba(255,235,160,${0.95 * a})`; ctx.beginPath(); ctx.arc(x, y, s * 0.8, 0, TAU); ctx.fill();
        });
        ctx.restore();
    }

    function drawLavaWorld() {
        const ft = H * 0.30;
        // שמיים
        let sky = ctx.createLinearGradient(0, 0, 0, ft);
        sky.addColorStop(0, '#12040a'); sky.addColorStop(0.5, '#4a0f0a'); sky.addColorStop(1, '#d4500c');
        ctx.fillStyle = sky; ctx.fillRect(0, 0, W, ft + 2);

        // עננים כבדים נעים
        for (let i = 0; i < 7; i++) {
            const x = ((i * W / 6 + T * (6 + i)) % (W + 500)) - 250, y = H * (0.03 + 0.045 * (i % 3)), r = H * (0.07 + (i % 2) * 0.03);
            let cg = ctx.createRadialGradient(x, y, 2, x, y, r * 2);
            cg.addColorStop(0, 'rgba(30,10,10,0.55)'); cg.addColorStop(1, 'rgba(30,10,10,0)');
            ctx.fillStyle = cg; ctx.beginPath(); ctx.ellipse(x, y, r * 2.6, r, 0, 0, TAU); ctx.fill();
        }

        // רכס הרים רחוק
        ctx.fillStyle = '#2a0d08';
        ctx.beginPath(); ctx.moveTo(0, ft);
        for (let x = 0; x <= W + 20; x += 20) ctx.lineTo(x, ft - (26 + 22 * Math.sin(x * 0.011 + 1) + 14 * Math.sin(x * 0.029 + 2)));
        ctx.lineTo(W, ft); ctx.closePath(); ctx.fill();

        // הרי געש: קטן משמאל, גדול מימין
        drawVolcanoCone(W * 0.2, W * 0.3, H * 0.1, ft, false);
        drawVolcanoCone(W * 0.76, W * 0.5, H * 0.05, ft, true);
        drawEruption(W * 0.76, H * 0.05, 1);
        drawEruption(W * 0.2, H * 0.1, 0.55);

        // אובך חם באופק
        let hz = ctx.createLinearGradient(0, ft - 44, 0, ft + 12);
        hz.addColorStop(0, 'rgba(255,120,30,0)'); hz.addColorStop(1, 'rgba(255,150,40,0.6)');
        ctx.fillStyle = hz; ctx.fillRect(0, ft - 44, W, 56);

        // ===== רצפת לבה =====
        let fg = ctx.createLinearGradient(0, ft, 0, H);
        fg.addColorStop(0, '#ffc03a'); fg.addColorStop(0.18, '#ff6a10'); fg.addColorStop(0.62, '#c2290a'); fg.addColorStop(1, '#5c0f05');
        ctx.fillStyle = fg; ctx.fillRect(0, ft, W, H - ft);

        // זרימת לבה
        ctx.lineCap = 'round';
        for (let i = 0; i < 26; i++) {
            const v = i / 26, y = ft + 6 + (H - ft) * Math.pow(v, 1.6), sc = 0.25 + v * 1.3;
            ctx.beginPath();
            for (let x = -20; x <= W + 20; x += 24) {
                const yy = y + Math.sin(x * 0.012 / sc + T * 0.9 + i * 1.7) * 5 * sc;
                x === -20 ? ctx.moveTo(x, yy) : ctx.lineTo(x, yy);
            }
            ctx.strokeStyle = `rgba(255,${190 + (i % 3) * 20},80,${0.12 + v * 0.12})`;
            ctx.lineWidth = 1.5 + sc * 2.2; ctx.stroke();
        }

        // לוחות סלע מצטננים שצפים על הלבה
        const span = W * 1.5;
        LAVA_PLATES.forEach(pl => {
            const y = ft + 14 + (H - ft - 14) * Math.pow(pl.v, 1.5), sc = 0.22 + pl.v * 1.5;
            const x = ((pl.u * span + T * 14 * pl.sp * sc) % span) - W * 0.25;
            const rx = 70 * sc * pl.size, ry = rx * 0.32, n = pl.verts.length;
            ctx.beginPath();
            for (let k = 0; k < n; k++) {
                const a = k / n * TAU, r = pl.verts[k], px = x + Math.cos(a) * rx * r, py = y + Math.sin(a) * ry * r;
                k ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
            }
            ctx.closePath(); ctx.lineJoin = 'round';
            ctx.strokeStyle = 'rgba(255,175,55,0.6)'; ctx.lineWidth = 3 + sc * 3.5; ctx.stroke();
            let pg = ctx.createLinearGradient(0, y - ry, 0, y + ry);
            pg.addColorStop(0, '#54301f'); pg.addColorStop(1, '#170a06');
            ctx.fillStyle = pg; ctx.fill();
            ctx.strokeStyle = 'rgba(0,0,0,0.55)'; ctx.lineWidth = 1.2; ctx.stroke();
            // סדק זוהר
            ctx.strokeStyle = 'rgba(255,120,30,0.65)'; ctx.lineWidth = 1 + sc * 0.8;
            ctx.beginPath(); ctx.moveTo(x - rx * 0.3, y - ry * 0.1); ctx.lineTo(x + rx * 0.05, y + ry * 0.2); ctx.lineTo(x + rx * 0.35, y - ry * 0.05); ctx.stroke();
        });

        // בועות לבה שמתפוצצות
        LAVA_BUBBLES.forEach(b => {
            const ph = (T * b.sp + b.off) % 1, y = ft + 18 + (H - ft - 18) * Math.pow(b.v, 1.5), sc = 0.25 + b.v * 1.3, x = b.u * W;
            if (ph < 0.8) {
                const r = (4 + 16 * (ph / 0.8)) * sc;
                ctx.fillStyle = 'rgba(255,140,30,0.6)'; ctx.strokeStyle = 'rgba(255,235,150,0.85)'; ctx.lineWidth = 1.6;
                ctx.beginPath(); ctx.ellipse(x, y, r, r * 0.5, 0, 0, TAU); ctx.fill(); ctx.stroke();
                ctx.fillStyle = 'rgba(255,255,220,0.7)'; ctx.beginPath(); ctx.ellipse(x - r * 0.3, y - r * 0.12, r * 0.28, r * 0.12, 0, 0, TAU); ctx.fill();
            } else {
                const q = (ph - 0.8) / 0.2;
                ctx.strokeStyle = `rgba(255,230,140,${1 - q})`; ctx.lineWidth = 2;
                ctx.beginPath(); ctx.ellipse(x, y, (20 + 30 * q) * sc, (20 + 30 * q) * sc * 0.45, 0, 0, TAU); ctx.stroke();
                ctx.fillStyle = `rgba(255,200,90,${1 - q})`;
                for (let k = 0; k < 5; k++) { const a = k * 1.3; ctx.beginPath(); ctx.arc(x + Math.cos(a) * 18 * q * sc, y - Math.sin(q * Math.PI) * 22 * sc - Math.abs(Math.sin(a)) * 6, 2 * sc, 0, TAU); ctx.fill(); }
            }
        });

        // זוהר חום מעל הכול
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        const fl = 0.9 + Math.sin(T * 7) * 0.05 + Math.sin(T * 13.3) * 0.05;
        let hg = ctx.createRadialGradient(W / 2, ft + 30, 20, W / 2, ft + 30, W * 0.65);
        hg.addColorStop(0, `rgba(255,140,40,${0.34 * fl})`); hg.addColorStop(1, 'rgba(255,100,20,0)');
        ctx.fillStyle = hg; ctx.fillRect(0, ft, W, H - ft);
        ctx.restore();
    }

    function drawRockIsland(x, y) {
        const rx = 74, ry = 19, th = 13;
        ctx.save();
        // זוהר לבה מתחת
        ctx.globalCompositeOperation = 'lighter';
        let ug = ctx.createRadialGradient(x, y + th, 6, x, y + th, rx * 1.5);
        ug.addColorStop(0, 'rgba(255,110,20,0.5)'); ug.addColorStop(1, 'rgba(255,110,20,0)');
        ctx.fillStyle = ug; ctx.beginPath(); ctx.ellipse(x, y + th, rx * 1.5, ry * 1.9, 0, 0, TAU); ctx.fill();
        ctx.globalCompositeOperation = 'source-over';
        // דופן
        let sg = ctx.createLinearGradient(x - rx, 0, x + rx, 0);
        sg.addColorStop(0, '#1a0d08'); sg.addColorStop(0.5, '#3d241a'); sg.addColorStop(1, '#120803');
        ctx.fillStyle = sg;
        ctx.beginPath(); ctx.moveTo(x - rx, y); ctx.lineTo(x - rx, y + th);
        ctx.ellipse(x, y + th, rx, ry, 0, Math.PI, 0, true);
        ctx.lineTo(x + rx, y); ctx.closePath(); ctx.fill();
        let rg = ctx.createLinearGradient(0, y, 0, y + th + ry);
        rg.addColorStop(0, 'rgba(255,100,20,0)'); rg.addColorStop(1, 'rgba(255,100,20,0.5)');
        ctx.fillStyle = rg; ctx.fill();
        // משטח עליון
        let tg = ctx.createRadialGradient(x - rx * 0.25, y - ry * 0.3, 4, x, y, rx);
        tg.addColorStop(0, '#6a4a36'); tg.addColorStop(1, '#2a1a12');
        ctx.fillStyle = tg; ctx.beginPath(); ctx.ellipse(x, y, rx, ry, 0, 0, TAU); ctx.fill();
        ctx.strokeStyle = '#150a06'; ctx.lineWidth = 2; ctx.stroke();
        ctx.save(); ctx.beginPath(); ctx.ellipse(x, y, rx - 2, ry - 1, 0, 0, TAU); ctx.clip();
        ctx.strokeStyle = 'rgba(255,125,35,0.7)'; ctx.lineWidth = 1.4; ctx.lineCap = 'round';
        [[-50, -2, -22, 4, -8, 0], [18, 6, 40, -3, 58, 4], [-12, -9, 2, -2, 14, -8]].forEach(c => {
            ctx.beginPath(); ctx.moveTo(x + c[0], y + c[1]); ctx.lineTo(x + c[2], y + c[3]); ctx.lineTo(x + c[4], y + c[5]); ctx.stroke();
        });
        ctx.restore();
        ctx.strokeStyle = 'rgba(255,170,90,0.5)'; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.ellipse(x, y, rx - 1, ry - 0.5, 0, Math.PI * 1.05, Math.PI * 1.9); ctx.stroke();
        ctx.restore();
    }

    function drawRestaurant() {
        const cx = W / 2, ft = H * 0.40;
        // קיר
        let g = ctx.createLinearGradient(0, 0, 0, ft);
        g.addColorStop(0, '#2a1206'); g.addColorStop(1, '#6a3513');
        ctx.fillStyle = g; ctx.fillRect(0, 0, W, ft + 2);
        const ts = Math.max(38, W / 42);
        for (let row = 0; row * ts < ft; row++) {
            for (let col = -1; col * ts < W; col++) {
                const x = col * ts + (row % 2) * ts / 2, y = row * ts, k = (col + row + 3) % 3;
                ctx.fillStyle = k === 0 ? 'rgba(255,190,90,0.07)' : k === 1 ? 'rgba(0,0,0,0.10)' : 'rgba(255,120,40,0.05)';
                ctx.fillRect(x + 1, y + 1, ts - 2, ts - 2);
                ctx.strokeStyle = 'rgba(255,200,120,0.05)'; ctx.lineWidth = 1;
                ctx.beginPath(); ctx.moveTo(x + ts / 2, y + 6); ctx.lineTo(x + ts - 6, y + ts / 2); ctx.lineTo(x + ts / 2, y + ts - 6); ctx.lineTo(x + 6, y + ts / 2); ctx.closePath(); ctx.stroke();
            }
        }
        // קורת עץ עליונה
        let bg = ctx.createLinearGradient(0, 0, 0, H * 0.04);
        bg.addColorStop(0, '#3b200c'); bg.addColorStop(1, '#1a0d04');
        ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H * 0.04);

        // מדפים עם צנצנות
        const jarCols = ['#e0b84c', '#6b8e23', '#c0392b', '#eadcaa', '#a0522d'];
        const rnd = mulberry32(21);
        [[0.03, 0.33, 0.2], [0.67, 0.97, 0.2], [0.03, 0.33, 0.3], [0.67, 0.97, 0.3]].forEach(sh => {
            const y = H * sh[2], x0 = W * sh[0], x1 = W * sh[1];
            for (let x = x0 + 8; x < x1 - 20; x += 30) {
                const jc = jarCols[(rnd() * jarCols.length) | 0], hh = 24 + rnd() * 10;
                let jg = ctx.createLinearGradient(x, 0, x + 22, 0);
                jg.addColorStop(0, shade(jc, -0.3)); jg.addColorStop(0.4, jc); jg.addColorStop(1, shade(jc, -0.4));
                ctx.fillStyle = jg; rrPath(ctx, x, y - hh, 22, hh, 4); ctx.fill();
                ctx.fillStyle = '#6b3d14'; ctx.fillRect(x + 2, y - hh - 4, 18, 5);
                ctx.fillStyle = 'rgba(255,255,255,0.28)'; ctx.fillRect(x + 4, y - hh + 3, 3, hh - 8);
            }
            let sg = ctx.createLinearGradient(0, y, 0, y + 7);
            sg.addColorStop(0, '#8c5830'); sg.addColorStop(1, '#3a210d');
            ctx.fillStyle = sg; ctx.fillRect(x0, y, x1 - x0, 7);
        });

        // שלט ניאון
        const fl = Math.sin(T * 37) > 0.96 ? 0.45 : 1;
        ctx.save();
        ctx.globalAlpha = fl;
        ctx.font = `bold ${Math.max(30, W * 0.026)}px "Segoe UI", Arial`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.shadowColor = '#ffb703'; ctx.shadowBlur = 28;
        ctx.fillStyle = '#fff3c4'; ctx.fillText('פלאפל חן', W * 0.2, H * 0.1);
        ctx.shadowBlur = 14; ctx.strokeStyle = '#ffb703'; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.moveTo(W * 0.2 - 90, H * 0.1 + 28); ctx.lineTo(W * 0.2 + 90, H * 0.1 + 28); ctx.stroke();
        ctx.restore();
        // לוח תפריט
        const mx = W * 0.8, my = H * 0.06;
        ctx.fillStyle = '#1b1f1c'; rrPath(ctx, mx - 90, my, 180, 108, 6); ctx.fill();
        ctx.strokeStyle = '#8c5830'; ctx.lineWidth = 5; ctx.stroke();
        ctx.fillStyle = 'rgba(255,255,255,0.85)'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.font = 'bold 15px "Segoe UI", Arial'; ctx.fillText('~ תפריט ~', mx, my + 20);
        ctx.font = '13px "Segoe UI", Arial';
        ['פלאפל בפיתה', 'חומוס מסבחה', 'טחינה בלי הגבלה'].forEach((t, i) => ctx.fillText(t, mx, my + 46 + i * 20));

        // מנורות תלויות
        const lamps = [];
        [0.12, 0.3, 0.7, 0.88].forEach((fx, i) => {
            const lx = W * fx, ly = H * 0.13 + Math.sin(T * 1.2 + i) * 3;
            ctx.strokeStyle = '#1a1a1a'; ctx.lineWidth = 2;
            ctx.beginPath(); ctx.moveTo(lx, 0); ctx.lineTo(lx, ly - 24); ctx.stroke();
            let lg = ctx.createLinearGradient(lx - 28, 0, lx + 28, 0);
            lg.addColorStop(0, '#7c5a07'); lg.addColorStop(0.45, '#fde68a'); lg.addColorStop(1, '#6b4a05');
            ctx.fillStyle = lg;
            ctx.beginPath(); ctx.moveTo(lx - 28, ly); ctx.lineTo(lx - 10, ly - 24); ctx.lineTo(lx + 10, ly - 24); ctx.lineTo(lx + 28, ly); ctx.closePath(); ctx.fill();
            ctx.fillStyle = '#fffbe0'; ctx.beginPath(); ctx.ellipse(lx, ly + 1, 14, 5, 0, 0, TAU); ctx.fill();
            lamps.push([lx, ly]);
        });

        // דלפק
        const cy0 = ft - H * 0.07;
        let tg = ctx.createLinearGradient(0, cy0, 0, cy0 + H * 0.02);
        tg.addColorStop(0, '#b97a38'); tg.addColorStop(1, '#6a3f17');
        ctx.fillStyle = tg; ctx.fillRect(0, cy0, W, H * 0.02);
        ctx.fillStyle = '#1f3a5f'; ctx.fillRect(0, cy0 + H * 0.02, W, H * 0.07);
        for (let x = 0; x < W; x += 26) {
            ctx.fillStyle = ((x / 26) | 0) % 2 ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.03)';
            ctx.fillRect(x, cy0 + H * 0.02, 26, H * 0.07);
        }
        // סירי טיגון + קיטור
        [W * 0.07, W * 0.93].forEach(px => {
            let pg = ctx.createLinearGradient(px - 28, 0, px + 28, 0);
            pg.addColorStop(0, '#6b7280'); pg.addColorStop(0.4, '#e5e7eb'); pg.addColorStop(1, '#4b5563');
            ctx.fillStyle = pg; rrPath(ctx, px - 28, cy0 - 26, 56, 26, 6); ctx.fill();
            ctx.fillStyle = '#7c4a12'; ctx.beginPath(); ctx.ellipse(px, cy0 - 26, 26, 6, 0, 0, TAU); ctx.fill();
            for (let i = 0; i < 4; i++) drawFalafelBall(px - 15 + i * 10, cy0 - 28, 6, i, false, 1);
            for (let i = 0; i < 7; i++) {
                const ph = ((T * 0.45 + i / 7) % 1);
                ctx.fillStyle = `rgba(255,255,255,${0.22 * (1 - ph)})`;
                ctx.beginPath(); ctx.arc(px + Math.sin(ph * 6 + i) * 12, cy0 - 36 - ph * 90, 6 + ph * 16, 0, TAU); ctx.fill();
            }
        });

        // ריצפת אריחים בפרספקטיבה
        let fg = ctx.createLinearGradient(0, ft, 0, H);
        fg.addColorStop(0, '#3b1d0a'); fg.addColorStop(1, '#1a0c04');
        ctx.fillStyle = fg; ctx.fillRect(0, ft, W, H - ft);
        const vpY = ft - H * 0.5, rows = 10, cols = 40, colW = W * 0.06;
        const sxx = (i, y) => cx + (i - cols / 2) * colW * ((y - vpY) / (H - vpY));
        for (let r = 0; r < rows; r++) {
            const y0 = ft + (H - ft) * Math.pow(r / rows, 1.7), y1 = ft + (H - ft) * Math.pow((r + 1) / rows, 1.7);
            for (let i = 0; i < cols; i++) {
                const x00 = sxx(i, y0), x10 = sxx(i + 1, y0), x11 = sxx(i + 1, y1), x01 = sxx(i, y1);
                if (Math.max(x10, x11) < 0 || Math.min(x00, x01) > W) continue;
                ctx.fillStyle = (i + r) % 2 ? '#4a2810' : '#2f1809';
                ctx.beginPath(); ctx.moveTo(x00, y0); ctx.lineTo(x10, y0); ctx.lineTo(x11, y1); ctx.lineTo(x01, y1); ctx.closePath(); ctx.fill();
            }
        }

        // שולחנות + לוטמים מעודדים
        const lotemImg = loadedPlayerImages['lotem'];
        const tableY = H * 0.54;
        const shirts = ['#b91c1c', '#1d4ed8', '#15803d', '#a21caf', '#c2410c', '#0e7490'];
        [0.08, 0.22, 0.36, 0.64, 0.78, 0.92].forEach((fx, i) => {
            const tx = W * fx, bob = Math.sin(T * 4 + i * 1.3) * 3;
            // כיסא + גוף
            ctx.fillStyle = shirts[i];
            ctx.beginPath(); ctx.ellipse(tx, tableY - 6 + bob, 30, 24, 0, Math.PI, TAU); ctx.fill();
            ctx.fillRect(tx - 30, tableY - 6 + bob, 60, 10);
            ctx.strokeStyle = '#f1c27d'; ctx.lineWidth = 8; ctx.lineCap = 'round';
            const armUp = Math.sin(T * 5 + i) * 6;
            ctx.beginPath(); ctx.moveTo(tx - 24, tableY - 10 + bob); ctx.lineTo(tx - 38, tableY - 44 + armUp);
            ctx.moveTo(tx + 24, tableY - 10 + bob); ctx.lineTo(tx + 38, tableY - 44 - armUp); ctx.stroke();
            // ראש
            const hy = tableY - 40 + bob;
            drawHead(tx, hy, 21, PLAYERS[0], lotemImg);
            // שלט
            const sy = hy - 52 - bob * 0.5;
            ctx.strokeStyle = '#8c5830'; ctx.lineWidth = 3;
            ctx.beginPath(); ctx.moveTo(tx, sy + 22); ctx.lineTo(tx, hy - 20); ctx.stroke();
            ctx.fillStyle = '#fef08a'; rrPath(ctx, tx - 34, sy, 68, 24, 5); ctx.fill();
            ctx.strokeStyle = '#ca8a04'; ctx.lineWidth = 2; ctx.stroke();
            ctx.fillStyle = '#000'; ctx.font = 'bold 13px Arial'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
            ctx.fillText('אלבזון!', tx, sy + 13);
            // שולחן עם מפת משבצות
            ctx.save();
            ctx.beginPath(); ctx.ellipse(tx, tableY + 4, 56, 14, 0, 0, TAU); ctx.clip();
            for (let qx = -56; qx < 56; qx += 14) for (let qy = -14; qy < 14; qy += 7) {
                ctx.fillStyle = ((qx / 14 + qy / 7) | 0) % 2 ? '#e8e8e8' : '#c0392b';
                ctx.fillRect(tx + qx, tableY + 4 + qy, 14, 7);
            }
            ctx.restore();
            let dg = ctx.createLinearGradient(0, tableY + 4, 0, tableY + 60);
            dg.addColorStop(0, '#b3382c'); dg.addColorStop(1, '#5c1a12');
            ctx.fillStyle = dg;
            ctx.beginPath(); ctx.moveTo(tx - 56, tableY + 4); ctx.quadraticCurveTo(tx, tableY + 24, tx + 56, tableY + 4); ctx.lineTo(tx + 50, tableY + 58); ctx.quadraticCurveTo(tx, tableY + 70, tx - 50, tableY + 58); ctx.closePath(); ctx.fill();
            // צלחת
            ctx.fillStyle = '#f8fafc'; ctx.beginPath(); ctx.ellipse(tx - 12, tableY + 2, 20, 6, 0, 0, TAU); ctx.fill();
            drawFalafelBall(tx - 20, tableY - 2, 5, 0, false, 1); drawFalafelBall(tx - 10, tableY - 3, 5, 1, false, 1); drawFalafelBall(tx, tableY - 2, 5, 2, false, 1);
            ctx.fillStyle = '#7dd3fc'; rrPath(ctx, tx + 24, tableY - 10, 9, 14, 2); ctx.fill();
        });

        // זוהר תאורה
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        lamps.forEach(l => {
            let lg = ctx.createRadialGradient(l[0], l[1] + 6, 4, l[0], l[1] + 6, H * 0.4);
            lg.addColorStop(0, 'rgba(255,190,90,0.38)'); lg.addColorStop(1, 'rgba(255,150,40,0)');
            ctx.fillStyle = lg; ctx.fillRect(l[0] - H * 0.4, l[1] - H * 0.2, H * 0.8, H * 0.8);
        });
        ctx.restore();
    }

    // ===================== סצנה =====================
    function drawScene() {
        ctx.save();
        if (shake > 0.3) ctx.translate((Math.random() - 0.5) * shake, (Math.random() - 0.5) * shake);

        if (isFalafelMode) drawRestaurant();
        else if (isLavaMode) drawLavaWorld();
        else drawArena();

        const cx = W / 2, hoopY = H * 0.22;
        const pita = selectedPlayer.isFalafel;
        if (pita) drawPitaBack(cx, hoopY); else drawHoopBack(cx, hoopY);

        const pos = POSITIONS[currentPosIndex];
        const pX = W * pos.xRatio, pYbase = H * pos.yRatio;
        const pY = pYbase - playerJumpY;

        // כיוון הרובה אל השחקן
        if (pita) {
            const pv = gunPivot();
            const ta = Math.atan2((pYbase - 56 * PLAYER_SCALE) - pv.y, pX - pv.x);
            gunAngle += (ta - gunAngle) * Math.min(1, dt * 10);
            drawShooter();
        }

        if (isLavaMode) drawRockIsland(pX, pYbase + 74);
        const inHand = !isShooting || (flight.active && flight.p < 0.12);
        drawAthlete(pX, pY, selectedPlayer, { scale: PLAYER_SCALE, lift: playerJumpY, blend: shootBlend, ball: inHand });

        // כדור בטיסה
        if (flight.active && flight.p >= 0.12) {
            flight.trail.forEach((p, i) => {
                const f = (i + 1) / flight.trail.length;
                ctx.fillStyle = selectedPlayer.isFalafel ? `rgba(234,179,8,${f * 0.16})` : `rgba(255,150,60,${f * 0.16})`;
                ctx.beginPath(); ctx.arc(p[0], p[1], flight.r * f * 0.9, 0, TAU); ctx.fill();
            });
            drawBallOrFalafel(flight.x, flight.y, flight.r, flight.rot, flight.alpha);
        }

        if (pita) drawPitaFront(cx, hoopY); else drawHoopFront(cx, hoopY);

        drawTahiniProjectiles();
        persistentTahiniSplashes.forEach(drawSplash);

        // בועות דיאלוג
        if (persistentTahiniSplashes.length > 0) {
            const t = persistentTahiniSplashes[0].t;
            const sp = shooterPos();
            drawBubble(sp.x + 28, sp.y - 120, 'לוטם יא נוביסט!', '#2563eb', t / 0.25);
            drawBubble(pX + 10, pYbase - 150, 'שתוק גמד!', '#eab308', (t - 0.55) / 0.25);
        }

        // חלקיקים
        particles.forEach(p => {
            const f = p.life / p.max;
            if (p.type === 'conf') {
                ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.rot); ctx.globalAlpha = 1 - f * f;
                ctx.fillStyle = p.color; ctx.fillRect(-p.size / 2, -p.size / 4, p.size, p.size / 2); ctx.restore();
            } else if (p.type === 'drop') {
                ctx.fillStyle = `rgba(250,244,215,${1 - f})`;
                ctx.beginPath(); ctx.arc(p.x, p.y, p.size, 0, TAU); ctx.fill();
            } else if (p.type === 'spark') {
                ctx.fillStyle = `rgba(255,200,80,${1 - f})`;
                ctx.beginPath(); ctx.arc(p.x, p.y, p.size, 0, TAU); ctx.fill();
            } else if (p.type === 'ember') {
                ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = (1 - f) * 0.9;
                ctx.fillStyle = f < 0.5 ? '#fdba74' : '#ef4444';
                ctx.beginPath(); ctx.arc(p.x, p.y, p.size * (1 - f * 0.5), 0, TAU); ctx.fill(); ctx.restore();
            } else if (p.type === 'ring') {
                ctx.strokeStyle = p.color; ctx.globalAlpha = 1 - f; ctx.lineWidth = 5 * (1 - f) + 1;
                ctx.beginPath(); ctx.arc(p.x, p.y, 20 + f * 120, 0, TAU); ctx.stroke(); ctx.globalAlpha = 1;
            } else if (p.type === 'flash') {
                const R = 14 * (1 - f) + 2;
                let fg = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, R);
                fg.addColorStop(0, 'rgba(255,255,255,0.95)'); fg.addColorStop(1, 'rgba(255,255,255,0)');
                ctx.fillStyle = fg; ctx.beginPath(); ctx.arc(p.x, p.y, R, 0, TAU); ctx.fill();
            }
        });

        // ויגנט
        let vg = ctx.createRadialGradient(W / 2, H * 0.5, Math.min(W, H) * 0.35, W / 2, H * 0.5, Math.max(W, H) * 0.75);
        vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, isFalafelMode ? 'rgba(25,8,0,0.65)' : (isLavaMode ? 'rgba(45,0,0,0.7)' : 'rgba(0,0,0,0.6)'));
        ctx.fillStyle = vg; ctx.fillRect(-20, -20, W + 40, H + 40);
        ctx.restore();
    }

    function gameOver() {
        isGameRunning = false;
        document.getElementById('final-score').innerText = `תוצאה סופית: ${score}`;
        document.getElementById('high-score-modal').innerText = `שיא קליעות נוכחי: ${highScore}`;
        setTimeout(() => { document.getElementById('game-over-modal').style.display = 'flex'; }, 900);
    }

    function resetToMenu() {
        isGameRunning = false;
        cancelAnimationFrame(meterAnimationId);
        document.getElementById('game-over-modal').style.display = 'none';
        document.getElementById('game-screen').style.display = 'none';
        isFalafelMode = false; isLavaMode = false;
        document.getElementById('falafel-mode-banner').style.display = 'none';
        document.getElementById('lava-mode-banner').style.display = 'none';
        document.getElementById('meter-container').classList.remove('falafel-mode', 'lava-mode');
        document.getElementById('menu-screen').style.display = 'flex';
    }
</script>
</body>
</html>
"""


class GameHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_image(self, path):
        if os.path.exists(path):
            self.send_response(200)
            content_type = "image/png" if path.lower().endswith('.png') else "image/jpeg"
            self.send_header("Content-type", content_type)
            self.send_header("Cache-Control", "max-age=3600")
            self.end_headers()
            with open(path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "Image not found")

    def do_GET(self):
        try:
            parsed_path = urllib.parse.unquote(self.path)

            if parsed_path == '/peleg.png':
                return self._send_image(PELEG_IMAGE_PATH)
            if parsed_path == '/lotem.png':
                return self._send_image(LOTEM_IMAGE_PATH)

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            pass


class ReusableServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_server():
    with ReusableServer(("", PORT), GameHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    time.sleep(1)
    webbrowser.open(f"http://localhost:{PORT}")

    print("לחץ Ctrl+C כדי לצאת.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nהשרת נסגר.")
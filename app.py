import streamlit as st
import time
from datetime import datetime

# Page config
st.set_page_config(
    page_title="BUZZR // Live Trivia",
    page_icon="🚨",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Shared server-side state across all connected users
@st.cache_resource
def get_game_state():
    return {
        "master": None,
        "players": {},       # {name: last_seen_timestamp}
        "scores": {},        # {name: int}
        "buzz_queue": [],    # [{"name": str, "time": float, "display": str}]
        "locked": True,      # Start locked until Master opens round
        "round_num": 1,
        "round_scored": False,
        "game_over": False
    }

state = get_game_state()

# ==============================================================================
# RESTORE SESSION FROM URL ON REFRESH (Prevents getting kicked out!)
# ==============================================================================
if "user_name" not in st.session_state:
    saved_name = st.query_params.get("name", "").strip()
    saved_role = st.query_params.get("role", "").strip()
    if saved_name and saved_role in ["Player (Buzzer)", "Trivia Master"]:
        # Reclaim role safely
        if saved_role == "Trivia Master":
            if state["master"] in [None, saved_name]:
                state["master"] = saved_name
                st.session_state.user_name = saved_name
                st.session_state.role = saved_role
        else:
            st.session_state.user_name = saved_name
            st.session_state.role = saved_role
            state["players"][saved_name] = time.time()
            if saved_name not in state["scores"]:
                state["scores"][saved_name] = 0

# ==============================================================================
# CUSTOM TV GAME SHOW CSS
# ==============================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stApp {
        background: radial-gradient(circle at top, #1a1f3c 0%, #0b0e1a 100%);
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }

    .block-container {
        max-width: 620px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    .app-header {
        text-align: center;
        margin-bottom: 1.2rem;
    }
    .app-title {
        font-size: clamp(28px, 6vw, 40px);
        font-weight: 900;
        letter-spacing: 2px;
        background: linear-gradient(90deg, #ff4b4b, #ff9f43, #ffd32a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        text-transform: uppercase;
    }
    .app-sub {
        color: #94a3b8;
        font-size: 14px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 2px;
    }

    .user-pill {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 14px;
        padding: 10px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
        backdrop-filter: blur(10px);
    }
    .pill-left {
        font-weight: 700;
        font-size: 15px;
        color: #f1f5f9;
    }
    .pill-badge {
        background: rgba(99, 102, 241, 0.25);
        border: 1px solid #6366f1;
        color: #c7d2fe;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        margin-left: 8px;
    }
    .round-badge {
        background: rgba(250, 204, 21, 0.15);
        border: 1px solid rgba(250, 204, 21, 0.4);
        color: #fde047;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 800;
    }

    .status-banner {
        padding: 16px;
        border-radius: 16px;
        text-align: center;
        font-weight: 800;
        font-size: clamp(16px, 3.8vw, 20px);
        letter-spacing: 0.5px;
        margin-bottom: 18px;
    }
    .status-locked {
        background: rgba(148, 163, 184, 0.1);
        border: 1px solid rgba(148, 163, 184, 0.25);
        color: #cbd5e1;
    }
    .status-live {
        background: rgba(16, 185, 129, 0.18);
        border: 2px solid #10b981;
        color: #6ee7b7;
        box-shadow: 0 0 25px rgba(16, 185, 129, 0.25);
        animation: pulseGlow 1.5s infinite;
    }
    .status-winner {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.25), rgba(234, 179, 8, 0.15));
        border: 2px solid #f59e0b;
        color: #fcd34d;
        box-shadow: 0 0 25px rgba(245, 158, 11, 0.3);
    }

    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 15px rgba(16, 185, 129, 0.2); }
        50% { box-shadow: 0 0 30px rgba(16, 185, 129, 0.45); }
    }

    /* 3D Arcade Buzzer Button */
    .buzzer-active div.stButton > button {
        height: clamp(175px, 30vh, 240px) !important;
        font-size: clamp(34px, 6.5vw, 48px) !important;
        font-weight: 900 !important;
        letter-spacing: 3px !important;
        color: #ffffff !important;
        background: linear-gradient(180deg, #ff3b3b 0%, #c91818 100%) !important;
        border: 4px solid #ff8787 !important;
        border-radius: 28px !important;
        box-shadow: 0 12px 0 #7f0909, 0 20px 35px rgba(255, 59, 59, 0.45) !important;
        transition: all 0.06s ease !important;
        touch-action: manipulation !important;
    }
    .buzzer-active div.stButton > button:active {
        transform: translateY(8px) !important;
        box-shadow: 0 4px 0 #7f0909, 0 10px 20px rgba(255, 59, 59, 0.4) !important;
    }

    .action-btn div.stButton > button {
        min-height: 50px !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        touch-action: manipulation !important;
    }

    .exit-btn div.stButton > button {
        min-height: 44px !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        background: rgba(239, 68, 68, 0.15) !important;
        border: 1px solid #ef4444 !important;
        color: #fca5a5 !important;
        border-radius: 12px !important;
    }

    .rank-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 12px 16px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .rank-card-first {
        background: linear-gradient(90deg, rgba(245, 158, 11, 0.22), rgba(255, 255, 255, 0.05));
        border: 1px solid rgba(245, 158, 11, 0.55);
    }
    .rank-left {
        display: flex;
        align-items: center;
        gap: 10px;
        font-weight: 700;
        font-size: 16px;
    }
    .rank-right {
        font-family: monospace;
        font-size: 14px;
        font-weight: 700;
        background: rgba(0, 0, 0, 0.35);
        padding: 4px 10px;
        border-radius: 8px;
        color: #e2e8f0;
    }

    .trophy-card {
        background: linear-gradient(135deg, #FDE047 0%, #F59E0B 55%, #B45309 100%);
        color: #111827;
        padding: 36px 22px;
        border-radius: 26px;
        text-align: center;
        box-shadow: 0 15px 45px rgba(245, 158, 11, 0.5);
        border: 3px solid #FEF08A;
        margin: 18px 0 24px 0;
        animation: popIn 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .trophy-icon {
        font-size: clamp(68px, 14vw, 96px);
        line-height: 1.1;
        margin-bottom: 10px;
    }
    .trophy-title {
        font-size: clamp(26px, 5.5vw, 36px);
        font-weight: 900;
        text-transform: uppercase;
        margin: 0;
        letter-spacing: 2px;
    }
    .trophy-subtitle {
        font-size: clamp(16px, 3.8vw, 20px);
        font-weight: 700;
        margin-top: 8px;
        color: #1f2937;
    }
    @keyframes popIn {
        0% { transform: scale(0.75); opacity: 0; }
        100% { transform: scale(1); opacity: 1; }
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="app-header">
        <div class="app-title">⚡ BUZZR LIVE</div>
        <div class="app-sub">Multiplayer Trivia Showdown</div>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# STEP 1: JOIN / ROLE SELECTION LOBBY
# ==============================================================================
if "user_name" not in st.session_state:
    with st.container(border=True):
        st.markdown("### 🎙️ Enter the Studio")
        name_input = st.text_input("Your Display Name", placeholder="e.g. Alex", max_chars=18).strip()

        master_taken = state["master"] is not None
        role_options = ["Player (Buzzer)"] if master_taken else ["Player (Buzzer)", "Trivia Master"]
        role = st.radio("Select Role", role_options, horizontal=True)

        if master_taken:
            st.caption(f"👑 Trivia Master in room: **{state['master']}**")
            if st.button("🔄 Clear Stuck Master / Reset Room", use_container_width=True):
                state["master"] = None
                state["players"] = {}
                state["scores"] = {}
                state["buzz_queue"] = []
                state["locked"] = True
                state["round_num"] = 1
                state["round_scored"] = False
                state["game_over"] = False
                st.rerun()

        st.markdown('<div class="action-btn">', unsafe_allow_html=True)
        if st.button("JOIN GAME →", type="primary", use_container_width=True):
            if not name_input:
                st.error("Please enter your name first.")
            elif role == "Trivia Master" and state["master"] is not None:
                st.error("Someone just claimed Trivia Master! Join as a Player.")
            elif role == "Player (Buzzer)" and name_input == state["master"]:
                st.error("That name is already used by the Trivia Master.")
            else:
                st.session_state.user_name = name_input
                st.session_state.role = role
                # Save to URL query params so browser refresh keeps them logged in!
                st.query_params["name"] = name_input
                st.query_params["role"] = role

                if role == "Trivia Master":
                    state["master"] = name_input
                else:
                    state["players"][name_input] = time.time()
                    if name_input not in state["scores"]:
                        state["scores"][name_input] = 0
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

user = st.session_state.user_name
role = st.session_state.role

# Top Exit Button (Outside fragment so it never blocks)
top_c1, top_c2 = st.columns([3.5, 1.5])
with top_c1:
    st.caption("⚡ Live Connected • Safe to refresh anytime")
with top_c2:
    st.markdown('<div class="exit-btn">', unsafe_allow_html=True)
    if st.button("🚪 Exit", use_container_width=True):
        if role == "Trivia Master" and state["master"] == user:
            state["master"] = None
        elif user in state["players"]:
            del state["players"][user]
        del st.session_state.user_name
        del st.session_state.role
        st.query_params.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# PLAYER BUZZER BUTTON (STATIC OUTSIDE FRAGMENT = INSTANT RESPONSE!)
# ==============================================================================
if role == "Player (Buzzer)" and not state["game_over"]:
    st.markdown('<div class="buzzer-active">', unsafe_allow_html=True)
    if st.button("🚨 BUZZ!", use_container_width=True):
        now = time.time()
        if state["locked"]:
            st.toast("🔒 Wait! Buzzers are currently locked by the Master.", icon="⏳")
        elif any(b["name"] == user for b in state["buzz_queue"]):
            st.toast("✅ You already buzzed in for this round!", icon="⚡")
        else:
            state["buzz_queue"].append({
                "name": user,
                "time": now,
                "display": datetime.fromtimestamp(now).strftime("%H:%M:%S.%f")[:-3]
            })
            st.toast("⚡ BUZZ REGISTERED!", icon="🚨")
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# LIVE SYNCED BOARD (PARTIAL AUTO-REFRESH EVERY 1s WITHOUT INTERRUPTING CLICKS)
# ==============================================================================
@st.fragment(run_every=1.0)
def live_game_board():
    if role == "Player (Buzzer)":
        state["players"][user] = time.time()
        if user not in state["scores"]:
            state["scores"][user] = 0

    # Player / Master Status Pill
    role_tag = "👑 MASTER" if role == "Trivia Master" else f"🎮 {state['scores'].get(user, 0)} PTS"
    st.markdown(f"""
        <div class="user-pill">
            <div class="pill-left">{user} <span class="pill-badge">{role_tag}</span></div>
            <div class="round-badge">R{state['round_num']}</div>
        </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # GAME OVER SCREEN
    # --------------------------------------------------------------------------
    if state["game_over"]:
        sorted_scores = sorted(state["scores"].items(), key=lambda x: x[1], reverse=True)
        top_score = sorted_scores[0][1] if sorted_scores else 0
        winners = [name for name, sc in sorted_scores if sc == top_score and top_score > 0]

        if user in winners:
            if not st.session_state.get("celebrated", False):
                st.balloons()
                st.session_state.celebrated = True
            st.markdown(f"""
                <div class="trophy-card">
                    <div class="trophy-icon">🏆</div>
                    <p class="trophy-title">Trivia Champion!</p>
                    <p class="trophy-subtitle">Congratulations, {user}!<br>Victory with <b>{top_score} points</b>!</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.session_state.celebrated = False
            if winners:
                winner_names = " & ".join(winners)
                st.markdown(f'<div class="status-banner status-winner">🎉 CHAMPION: {winner_names.upper()} ({top_score} PTS)</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-banner status-locked">🏁 GAME OVER — NO POINTS SCORED</div>', unsafe_allow_html=True)

        st.markdown("#### 📊 Final Standings")
        for rank, (p_name, p_score) in enumerate(sorted_scores, start=1):
            medal = "🥇" if rank == 1 and p_score > 0 else "🥈" if rank == 2 and p_score > 0 else "🥉" if rank == 3 and p_score > 0 else f"#{rank}"
            card_cls = "rank-card rank-card-first" if rank == 1 and p_score > 0 else "rank-card"
            st.markdown(f"""
                <div class="{card_cls}">
                    <div class="rank-left"><span>{medal}</span> <span>{p_name}</span></div>
                    <div class="rank-right">{p_score} pts</div>
                </div>
            """, unsafe_allow_html=True)

        if role == "Trivia Master":
            st.write("")
            st.markdown('<div class="action-btn">', unsafe_allow_html=True)
            if st.button("🔄 START NEW GAME", type="primary", use_container_width=True):
                state["scores"] = {p: 0 for p in state["players"]}
                state["buzz_queue"] = []
                state["locked"] = True
                state["round_num"] = 1
                state["round_scored"] = False
                state["game_over"] = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        return

    st.session_state.celebrated = False

    # --------------------------------------------------------------------------
    # LIVE STATUS BANNER
    # --------------------------------------------------------------------------
    if state["buzz_queue"]:
        first_player = state["buzz_queue"][0]["name"].upper()
        st.markdown(f'<div class="status-banner status-winner">⚡ {first_player} BUZZED FIRST!</div>', unsafe_allow_html=True)
    elif state["locked"]:
        st.markdown('<div class="status-banner status-locked">🔒 BUZZERS LOCKED — GET READY</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-banner status-live">🟢 BUZZERS LIVE — TAP THE RED BUTTON!</div>', unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # TRIVIA MASTER CONTROLS
    # --------------------------------------------------------------------------
    if role == "Trivia Master":
        st.markdown('<div class="action-btn">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🟢 OPEN BUZZER", type="primary", use_container_width=True, disabled=not state["locked"]):
                state["buzz_queue"] = []
                state["locked"] = False
                state["round_scored"] = False
                st.rerun(scope="fragment")
        with c2:
            if st.button("⏭️ NEXT ROUND", use_container_width=True):
                state["buzz_queue"] = []
                state["locked"] = True
                state["round_num"] += 1
                state["round_scored"] = False
                st.rerun(scope="fragment")
        st.markdown('</div>', unsafe_allow_html=True)

        all_players = list(state["scores"].keys())
        if all_players:
            with st.container(border=True):
                st.markdown("**🏅 Award Round Points**")
                buzzed_names = [b["name"] for b in state["buzz_queue"] if b["name"] in all_players]
                ordered_choices = buzzed_names + [p for p in all_players if p not in buzzed_names]

                sc1, sc2, sc3 = st.columns([2.2, 1, 1.2])
                with sc1:
                    selected_winner = st.selectbox("Player", ordered_choices, label_visibility="collapsed")
                with sc2:
                    points_to_add = st.number_input("Pts", min_value=-10, max_value=100, value=1, step=1, label_visibility="collapsed")
                with sc3:
                    if st.button("➕ Award", type="primary", use_container_width=True):
                        state["scores"][selected_winner] = state["scores"].get(selected_winner, 0) + points_to_add
                        state["locked"] = True
                        state["round_scored"] = True
                        st.rerun(scope="fragment")

                if state["round_scored"]:
                    st.caption("✅ Points added! Hit **NEXT ROUND** to continue.")

        with st.expander("🏁 End Game / Reset Room"):
            st.markdown('<div class="action-btn">', unsafe_allow_html=True)
            if st.button("🏆 Finish All Rounds & Crown Winner", type="primary", use_container_width=True):
                state["locked"] = True
                state["game_over"] = True
                st.rerun()
            if st.button("🗑️ Kick All & Reset Studio", use_container_width=True):
                state["master"] = None
                state["players"] = {}
                state["scores"] = {}
                state["buzz_queue"] = []
                state["locked"] = True
                state["round_num"] = 1
                state["round_scored"] = False
                state["game_over"] = False
                del st.session_state.user_name
                del st.session_state.role
                st.query_params.clear()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # BUZZ ORDER & LIVE SCOREBOARD
    # --------------------------------------------------------------------------
    if state["buzz_queue"]:
        st.markdown("#### ⚡ Buzz Order")
        first_time = state["buzz_queue"][0]["time"]
        for idx, entry in enumerate(state["buzz_queue"], start=1):
            diff = entry["time"] - first_time
            delay_str = "0.000s (1ST)" if idx == 1 else f"+{diff:.3f}s"
            card_cls = "rank-card rank-card-first" if idx == 1 else "rank-card"
            badge_icon = "⚡" if idx == 1 else f"#{idx}"
            st.markdown(f"""
                <div class="{card_cls}">
                    <div class="rank-left"><span>{badge_icon}</span> <span>{entry['name']}</span></div>
                    <div class="rank-right">{delay_str}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("#### 🏆 Live Scoreboard")
    if state["scores"]:
        sorted_live = sorted(state["scores"].items(), key=lambda x: x[1], reverse=True)
        for rank, (p_name, p_score) in enumerate(sorted_live, start=1):
            online_dot = "🟢" if p_name in state["players"] else "⚪"
            medal = "🥇" if rank == 1 and p_score > 0 else f"#{rank}"
            card_cls = "rank-card rank-card-first" if rank == 1 and p_score > 0 else "rank-card"
            st.markdown(f"""
                <div class="{card_cls}">
                    <div class="rank-left"><span>{online_dot} {medal}</span> <span>{p_name}</span></div>
                    <div class="rank-right">{p_score} pts</div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("Waiting for players to join the studio...")

live_game_board()

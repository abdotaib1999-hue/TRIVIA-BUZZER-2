import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time
from datetime import datetime

# Page config
st.set_page_config(page_title="Live Trivia Buzzer", page_icon="🚨", layout="centered")

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

# Auto-refresh every 500ms so all phones & PCs stay synced
st_autorefresh(interval=500, key="buzzer_sync")

# Responsive CSS for both Mobile Phones and PC screens
st.markdown("""
    <style>
    /* Constrain width nicely on PC while staying full-width on mobile */
    .block-container {
        max-width: 680px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Big Buzzer Button styling (scales smoothly between phone & desktop) */
    .buzzer-btn div.stButton > button {
        height: clamp(130px, 24vh, 210px) !important;
        font-size: clamp(26px, 5vw, 40px) !important;
        font-weight: 800 !important;
        border-radius: 22px !important;
        letter-spacing: 1px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
        transition: transform 0.08s ease;
    }
    .buzzer-btn div.stButton > button:active {
        transform: scale(0.97);
    }

    /* Standard control buttons on mobile/PC */
    .control-btn div.stButton > button {
        min-height: 52px;
        font-size: 16px !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
    }

    /* Exclusive Gold Trophy Card for the Winner */
    .trophy-card {
        background: linear-gradient(135deg, #FFD700 0%, #FDB931 50%, #D4AF37 100%);
        color: #1a1a1a;
        padding: 32px 20px;
        border-radius: 24px;
        text-align: center;
        box-shadow: 0 12px 35px rgba(255, 215, 0, 0.45);
        border: 3px solid #FFF8DC;
        margin: 20px 0;
        animation: popIn 0.6s ease-out;
    }
    .trophy-icon {
        font-size: clamp(64px, 12vw, 90px);
        line-height: 1.1;
        margin-bottom: 10px;
    }
    .trophy-title {
        font-size: clamp(24px, 5vw, 34px);
        font-weight: 900;
        text-transform: uppercase;
        margin: 0;
        letter-spacing: 1.5px;
    }
    .trophy-subtitle {
        font-size: clamp(16px, 3.5vw, 20px);
        font-weight: 600;
        margin-top: 8px;
        opacity: 0.9;
    }
    @keyframes popIn {
        0% { transform: scale(0.8); opacity: 0; }
        100% { transform: scale(1); opacity: 1; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚨 Live Trivia Buzzer")

# --- STEP 1: JOIN / ROLE SELECTION ---
if "user_name" not in st.session_state:
    st.subheader("Join the Game")
    name_input = st.text_input("Enter your name:", max_chars=20).strip()

    master_taken = state["master"] is not None
    role_options = ["Player (Buzzer)"] if master_taken else ["Player (Buzzer)", "Trivia Master"]
    role = st.radio("Choose your role:", role_options)

    if master_taken:
        st.caption(f"👑 Current Trivia Master: **{state['master']}**")

    st.markdown('<div class="control-btn">', unsafe_allow_html=True)
    if st.button("Enter Lobby", type="primary", use_container_width=True):
        if not name_input:
            st.error("Please enter your name first.")
        elif role == "Trivia Master" and state["master"] is not None:
            st.error("Someone just claimed Trivia Master! Join as a Player.")
        elif role == "Player (Buzzer)" and name_input == state["master"]:
            st.error("That name is already used by the Trivia Master.")
        else:
            st.session_state.user_name = name_input
            st.session_state.role = role
            if role == "Trivia Master":
                state["master"] = name_input
            else:
                state["players"][name_input] = time.time()
                if name_input not in state["scores"]:
                    state["scores"][name_input] = 0
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Keep active user registered
user = st.session_state.user_name
role = st.session_state.role
if role == "Player (Buzzer)":
    state["players"][user] = time.time()
    if user not in state["scores"]:
        state["scores"][user] = 0

# Header Bar
col1, col2 = st.columns([3, 1])
with col1:
    badge = "👑 Master" if role == "Trivia Master" else f"🎮 Player • {state['scores'].get(user, 0)} pts"
    st.markdown(f"**{user}** ({badge}) | **Round {state['round_num']}**")
with col2:
    if st.button("Leave", use_container_width=True):
        if role == "Trivia Master" and state["master"] == user:
            state["master"] = None
        elif user in state["players"]:
            del state["players"][user]
        del st.session_state.user_name
        del st.session_state.role
        st.rerun()

st.divider()

# ==============================================================================
# GAME OVER / FINAL PODIUM SCREEN
# ==============================================================================
if state["game_over"]:
    sorted_scores = sorted(state["scores"].items(), key=lambda x: x[1], reverse=True)
    top_score = sorted_scores[0][1] if sorted_scores else 0
    winners = [name for name, sc in sorted_scores if sc == top_score and top_score > 0]

    # Trigger exclusive celebration ONLY on the winning player's device
    if user in winners:
        if not st.session_state.get("celebrated", False):
            st.balloons()
            st.session_state.celebrated = True

        st.markdown(f"""
            <div class="trophy-card">
                <div class="trophy-icon">🏆</div>
                <p class="trophy-title">Trivia Champion!</p>
                <p class="trophy-subtitle">Congratulations, {user}!<br>You won with <b>{top_score} points</b>!</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.session_state.celebrated = False
        if winners:
            winner_names = " & ".join(winners)
            st.success(f"🎉 **GAME OVER! The Trivia Champion is {winner_names.upper()} ({top_score} pts)!**")
        else:
            st.info("🏁 **GAME OVER!** No points were scored this session.")

    # Final Leaderboard
    st.subheader("📊 Final Standings")
    if sorted_scores:
        for rank, (p_name, p_score) in enumerate(sorted_scores, start=1):
            medal = "🥇" if rank == 1 and p_score > 0 else "🥈" if rank == 2 and p_score > 0 else "🥉" if rank == 3 and p_score > 0 else f"#{rank}"
            st.write(f"**{medal} {p_name}** — `{p_score} pts`")

    st.divider()

    # Master option to start a brand-new game
    if role == "Trivia Master":
        st.markdown('<div class="control-btn">', unsafe_allow_html=True)
        if st.button("🔄 Start New Game (Keep Players)", type="primary", use_container_width=True):
            state["scores"] = {p: 0 for p in state["players"]}
            state["buzz_queue"] = []
            state["locked"] = True
            state["round_num"] = 1
            state["round_scored"] = False
            state["game_over"] = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.caption("Waiting for the Trivia Master to start a new game...")
    st.stop()

# Reset celebration flag while game is active
st.session_state.celebrated = False

# ==============================================================================
# ACTIVE GAME: TRIVIA MASTER CONTROLS
# ==============================================================================
if role == "Trivia Master":
    st.subheader("👑 Master Controls")

    st.markdown('<div class="control-btn">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🟢 OPEN BUZZER", use_container_width=True, disabled=not state["locked"]):
            state["buzz_queue"] = []
            state["locked"] = False
            state["round_scored"] = False
            st.rerun()
    with c2:
        if st.button("⏭️ NEXT ROUND", use_container_width=True):
            state["buzz_queue"] = []
            state["locked"] = True
            state["round_num"] += 1
            state["round_scored"] = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Round Winner & Point Assignment Section
    all_players = list(state["scores"].keys())
    if all_players:
        with st.container(border=True):
            st.markdown("**🏅 Award Round Points**")
            # Default selection to whoever buzzed first, if anyone buzzed
            buzzed_names = [b["name"] for b in state["buzz_queue"] if b["name"] in all_players]
            ordered_choices = buzzed_names + [p for p in all_players if p not in buzzed_names]

            sc_col1, sc_col2, sc_col3 = st.columns([2, 1, 1])
            with sc_col1:
                selected_winner = st.selectbox("Select Round Winner:", ordered_choices, label_visibility="collapsed")
            with sc_col2:
                points_to_add = st.number_input("Points", min_value=-10, max_value=100, value=1, step=1, label_visibility="collapsed")
            with sc_col3:
                if st.button("➕ Award", type="primary", use_container_width=True):
                    state["scores"][selected_winner] = state["scores"].get(selected_winner, 0) + points_to_add
                    state["locked"] = True
                    state["round_scored"] = True
                    st.rerun()

            if state["round_scored"]:
                st.caption("✅ Points awarded for this round! Click **NEXT ROUND** when ready.")

    # Finish All Rounds / End Game Button
    with st.expander("🏁 End Game / Room Settings"):
        st.markdown('<div class="control-btn">', unsafe_allow_html=True)
        if st.button("🏆 Finish All Rounds & Announce Winner", type="primary", use_container_width=True):
            state["locked"] = True
            state["game_over"] = True
            st.rerun()

        if st.button("🗑️ Reset Entire Room (Kick All)", use_container_width=True):
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
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# ACTIVE GAME: PLAYER VIEW
# ==============================================================================
else:
    already_buzzed = any(b["name"] == user for b in state["buzz_queue"])

    st.markdown('<div class="buzzer-btn">', unsafe_allow_html=True)
    if state["locked"]:
        st.warning("🔒 Buzzer is LOCKED. Wait for the Trivia Master!")
        st.button("LOCKED", disabled=True, use_container_width=True)
    elif already_buzzed:
        st.info("✅ You buzzed in! Waiting for the Master's decision...")
        st.button("BUZZED!", disabled=True, use_container_width=True)
    else:
        if st.button("🔴 BUZZ!", type="primary", use_container_width=True):
            now = time.time()
            if not any(b["name"] == user for b in state["buzz_queue"]):
                state["buzz_queue"].append({
                    "name": user,
                    "time": now,
                    "display": datetime.fromtimestamp(now).strftime("%H:%M:%S.%f")[:-3]
                })
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# ==============================================================================
# LIVE BUZZ ORDER & SCOREBOARD
# ==============================================================================
if state["buzz_queue"]:
    winner = state["buzz_queue"][0]
    st.success(f"⚡ **FIRST TO BUZZ: {winner['name'].upper()}!**")

    st.markdown("**Order of Buzzes:**")
    first_time = winner["time"]
    for idx, entry in enumerate(state["buzz_queue"], start=1):
        diff = entry["time"] - first_time
        delay_str = "0.000s (1st)" if idx == 1 else f"+{diff:.3f}s"
        st.write(f"**{idx}. {entry['name']}** — `{delay_str}`")
else:
    if state["locked"]:
        st.caption("Waiting for Trivia Master to open the buzzer...")
    else:
        st.info("🟢 **BUZZERS ARE LIVE!** Hit the button!")

# Live Scoreboard visible to all players & Master
st.subheader("🏆 Live Scoreboard")
if state["scores"]:
    sorted_live = sorted(state["scores"].items(), key=lambda x: x[1], reverse=True)
    for rank, (p_name, p_score) in enumerate(sorted_live, start=1):
        online_dot = "🟢" if p_name in state["players"] else "⚪"
        st.write(f"{online_dot} **{rank}. {p_name}** — `{p_score} pts`")
else:
    st.caption("No players have joined yet.")

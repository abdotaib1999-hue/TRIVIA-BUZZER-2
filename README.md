# TRIVIA-BUZZER-2
# ⚡ BUZZR LIVE — Multiplayer Trivia Buzzer

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://trivia-buzzer-2-j6htzkapk5ldpygiu2wfjf.streamlit.app/)

A real-time, TV game show-style multiplayer trivia buzzer built with Python and Streamlit. Designed to settle debates over who buzzed in first—whether your group is on the same Wi-Fi, mobile data, or playing remotely from anywhere.

👉 **Play Live Now:** [https://trivia-buzzer-2-j6htzkapk5ldpygiu2wfjf.streamlit.app/](https://trivia-buzzer-2-j6htzkapk5ldpygiu2wfjf.streamlit.app/)

---

## ✨ Features

* **Millisecond Buzz Precision:** Records exact server timestamps (`0.001s` accuracy) and displays the exact reaction time differences (`+0.042s`) between players.
* **Cross-Network Real-Time Sync:** Works across different Wi-Fi networks and mobile data connections using shared server state and auto-refresh polling.
* **Role-Based Views:**
  * **Trivia Master:** Controls when buzzers open/lock, advances rounds, awards points to round winners, and ends the game.
  * **Players:** Get a responsive, tactile 3D arcade buzzer button on their screen.
* **Live Scoreboard:** Automatically tracks and ranks player scores after every round.
* **Exclusive Champion Celebration:** When the Trivia Master finishes all rounds, the grand champion receives a custom Gold Trophy screen with celebratory balloons exclusively on their device.
* **Mobile & Desktop Responsive:** Optimized for both smartphone thumbs and desktop browsers.

---

## 🎮 How to Play

1. **Open the App:** Share the [live link](https://trivia-buzzer-2-j6htzkapk5ldpygiu2wfjf.streamlit.app/) with your friends.
2. **Choose Roles:**
   * One person enters their name and selects **Trivia Master**.
   * Everyone else enters their name and joins as a **Player (Buzzer)**.
3. **Start a Round:** The Trivia Master reads a question and clicks **🟢 OPEN BUZZER**.
4. **Buzz In:** Players tap **🚨 BUZZ!** as fast as possible. The app instantly locks in the order of buzzes.
5. **Award Points:** The Trivia Master selects the round winner from the dropdown (auto-defaulting to the fastest player) and awards points, then hits **⏭️ NEXT ROUND**.
6. **Crown the Winner:** Once all rounds are complete, the Trivia Master opens **🏁 End Game / Reset Room** and clicks **🏆 Finish All Rounds & Crown Winner**.

---

## 🛠️ Tech Stack & Local Setup

* **Framework:** [Streamlit](https://streamlit.io/)
* **Real-Time Sync:** `streamlit-autorefresh` & `@st.cache_resource`

### Run Locally
If you want to run or modify the app on your own machine:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git](https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git)
   cd YOUR-REPO-NAME

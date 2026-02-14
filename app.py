import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import datetime
import gspread
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials

# ==============================
# CONFIG
# ==============================
WEDDING_DATE = datetime.date(2026, 6, 23)

CAL_TARGET = 1200
PROTEIN_TARGET = 110
FAT_TARGET = 45
CARB_TARGET = 130

SPREADSHEET_ID = "1-4fTk-_YaVF5r7GWShZhYgYdAHe9DhJZV3Lxtwnxmdg"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ==============================
# PERFORMANCE: cache auth + spreadsheet
# ==============================
@st.cache_resource(show_spinner=False)
def get_gspread_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    return gspread.authorize(creds)

@st.cache_resource(show_spinner=False)
def get_spreadsheet():
    gc = get_gspread_client()
    return gc.open_by_key(SPREADSHEET_ID)

sheet = get_spreadsheet()

def ws(title: str):
    return sheet.worksheet(title)

# ==============================
# PERFORMANCE: cached reads (prevents 429)
# ==============================
@st.cache_data(ttl=60, show_spinner=False)
def read_records(ws_title: str) -> pd.DataFrame:
    records = ws(ws_title).get_all_records()
    df = pd.DataFrame(records)
    if not df.empty:
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df

def append_row(ws_title: str, row: list):
    ws(ws_title).append_row(row, value_input_option="USER_ENTERED")
    st.cache_data.clear()

# ==============================
# UI STYLE
# ==============================
st.set_page_config(page_title="Wedding Cut Tracker", layout="centered")

st.markdown(
    """
    <style>
    /* --- MAIN buttons: pink --- */
    section.main div.stButton > button {
        border-radius: 20px;
        background-color: #ffb6d9;
        color: white;
        border: none;
        padding: 0.5em 1.5em;
        font-weight: 800;
    }
    section.main div.stButton > button:hover {
        background-color: #ff9ecb;
        color: white;
    }

    /* --- SIDEBAR buttons: light blue gradient --- */
    .stSidebar div.stButton > button {
        border-radius: 16px !important;
        border: none !important;
        padding: 0.55em 1.0em !important;
        font-weight: 800 !important;
        color: #1f3c5a !important;
        background: linear-gradient(90deg, #a8d8ff, #c7eaff) !important;
        box-shadow: 0 6px 14px rgba(33, 110, 165, 0.12) !important;
    }
    .stSidebar div.stButton > button:hover {
        background: linear-gradient(90deg, #8ccfff, #b8e3ff) !important;
        color: #0f2f4a !important;
    }

    /* Progress bar color */
    div.stProgress > div > div > div { background-color: #ff9ecb; }

    h1, h2, h3 { color: #ff6fa5; }
    .block-container { padding-top: 1.5rem; }

    /* --- GAME FX --- */
    @keyframes geckoBounce {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-8px); }
    }
    @keyframes shimmer {
      0% { background-position: 0% 50%; }
      100% { background-position: 200% 50%; }
    }
    @keyframes popIn {
      0% { transform: scale(0.85); opacity: 0.0; }
      100% { transform: scale(1); opacity: 1; }
    }

    .badge-chip {
      display:inline-flex;
      align-items:center;
      gap:8px;
      border-radius:999px;
      padding:8px 14px;
      margin:6px 8px 6px 0;
      font-weight:900;
      font-size:14px;
      letter-spacing:0.2px;
      color:#fff;
      border:1px solid rgba(255,255,255,0.35);
      box-shadow: 0 6px 14px rgba(255, 111, 165, 0.18);
      animation: popIn 220ms ease-out;
      backdrop-filter: blur(6px);
      position: relative;
    }

    .badge-chip::after {
      content:"";
      position:absolute;
      inset:-2px;
      border-radius:999px;
      pointer-events:none;
      background: radial-gradient(circle at 20% 20%, rgba(255,255,255,0.45), transparent 35%),
                  radial-gradient(circle at 80% 10%, rgba(255,255,255,0.25), transparent 30%);
      opacity:0.85;
    }

    .badge-wrap {
      display:flex;
      flex-wrap:wrap;
      align-items:center;
    }

    .gecko-bounce {
      display:inline-block;
      animation: geckoBounce 900ms ease-in-out infinite;
      filter: drop-shadow(0 4px 8px rgba(255, 111, 165, 0.25));
    }

    .shimmer {
      background-size: 200% 200%;
      animation: shimmer 1600ms linear infinite;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("💍 Wedding Cut Dashboard")
st.markdown("<h4 style='color:#ff7fb0;'>🦎 Lean & Lovely Mode Activated 💗</h4>", unsafe_allow_html=True)

# ==============================
# CUTE CHART HELPERS
# ==============================
PINK = "#ff9ecb"
PINK_DARK = "#ff6fa5"
BG = "#fff6fb"

def cute_line_chart(df, x_col, y_col, title, goal=None, y_suffix=""):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode="lines+markers",
        line=dict(color=PINK_DARK, width=4, shape="spline"),
        marker=dict(size=9, color=PINK),
        name=title
    ))

    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode="lines",
        line=dict(width=0),
        fill="tozeroy",
        fillcolor="rgba(255, 158, 203, 0.18)",
        hoverinfo="skip",
        name=""
    ))

    if goal is not None:
        fig.add_hline(
            y=goal,
            line_dash="dash",
            line_color="rgba(255, 111, 165, 0.7)",
            annotation_text=f"Goal {goal}{y_suffix}",
            annotation_position="top left"
        )

    fig.update_layout(
        title=title,
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        margin=dict(l=10, r=10, t=40, b=10),
        height=320,
        font=dict(size=14, color="#4a4a4a"),
        showlegend=False
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255, 158, 203, 0.15)", zeroline=False)
    return fig

def cute_xp_card(label, value, target, emoji="🦎"):
    ratio = 0 if target == 0 else min(max(value / target, 0), 1)
    percent = int(ratio * 100)

    st.markdown(
        f"""
        <div style="
            background: #ffeaf4;
            border: 2px solid rgba(255,158,203,0.35);
            border-radius: 20px;
            padding: 14px 16px;
            margin: 8px 0;
        ">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div style="font-weight:900;color:#ff6fa5;font-size:16px;">
              {emoji} {label}
            </div>
            <div style="font-weight:800;color:#4a4a4a;">
              {value:.0f} / {target:.0f}
            </div>
          </div>
          <div style="height:14px;background:#fff6fb;border-radius:999px;overflow:hidden;margin-top:10px;">
            <div style="height:14px;width:{percent}%;background:#ff9ecb;"></div>
          </div>
          <div style="margin-top:8px;color:#ff6fa5;font-weight:800;">
            XP: {percent}%
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==============================
# EFFECTS + BADGES HELPERS
# ==============================
def confetti():
    js = """
    <canvas id="confetti" style="position:fixed;inset:0;pointer-events:none;z-index:9999;"></canvas>
    <script>
    const canvas = document.getElementById('confetti');
    const ctx = canvas.getContext('2d');
    const W = canvas.width = window.innerWidth;
    const H = canvas.height = window.innerHeight;

    const colors = ['#ff6fa5','#ff9ecb','#ffd1e8','#ffffff'];
    const pieces = Array.from({length: 140}).map(() => ({
      x: Math.random() * W,
      y: -20 - Math.random() * H * 0.3,
      r: 3 + Math.random() * 5,
      c: colors[Math.floor(Math.random()*colors.length)],
      vx: -2 + Math.random()*4,
      vy: 2 + Math.random()*5,
      a: Math.random()*Math.PI,
      va: -0.2 + Math.random()*0.4
    }));

    let t = 0;
    function draw(){
      t++;
      ctx.clearRect(0,0,W,H);
      pieces.forEach(p=>{
        p.x += p.vx;
        p.y += p.vy;
        p.a += p.va;
        p.vy += 0.02;
        ctx.save();
        ctx.translate(p.x,p.y);
        ctx.rotate(p.a);
        ctx.fillStyle = p.c;
        ctx.fillRect(-p.r, -p.r, p.r*2, p.r*2);
        ctx.restore();
      });

      if(t < 120) requestAnimationFrame(draw);
      else canvas.remove();
    }
    draw();
    </script>
    """
    components.html(js, height=0)

def play_badge_sound(enabled: bool):
    if not enabled:
        return
    audio_html = """
    <audio id="badgepop">
      <source src="data:audio/wav;base64,UklGRl4AAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YToAAAAA/////wAAAP///wAAAP///wAAAP///wAAAP///wAA" type="audio/wav">
    </audio>
    <script>
      const a = document.getElementById("badgepop");
      if (a) { a.volume = 0.6; a.play().catch(()=>{}); }
    </script>
    """
    components.html(audio_html, height=0)

def compute_daily_totals(meals: pd.DataFrame) -> pd.DataFrame:
    if meals is None or meals.empty:
        return pd.DataFrame()
    if "date" not in meals.columns:
        return pd.DataFrame()
    m = meals.copy()
    m["date"] = pd.to_datetime(m["date"], errors="coerce")
    m = m.dropna(subset=["date"])
    daily = m.groupby(m["date"].dt.date).sum(numeric_only=True)
    daily.index = pd.to_datetime(daily.index)
    return daily.sort_index()

def current_streak(daily: pd.DataFrame, condition_col: str) -> int:
    if daily.empty or condition_col not in daily.columns:
        return 0
    today = pd.to_datetime(datetime.date.today())
    streak = 0
    day = today
    while True:
        if (day in daily.index) and bool(daily.loc[day, condition_col]):
            streak += 1
            day = day - pd.Timedelta(days=1)
        else:
            break
    return streak

def render_badges(badges):
    if not badges:
        st.info("No badges yet — log meals to start! ✨")
        return

    rarity_bg = {
        "🥚 First Log": "linear-gradient(90deg,#9ad7ff,#c7eaff)",
        "🦎 Protein Boss": "linear-gradient(90deg,#ff6fa5,#ff9ecb,#ffd1e8)",
        "🌸 Perfect Day": "linear-gradient(90deg,#ff4f93,#ff9ecb,#fff2f8)",
        "🔥 3-Day Streak": "linear-gradient(90deg,#ff6a00,#ff4f93,#ff9ecb)",
        "💎 7-Day Streak": "linear-gradient(90deg,#6a5cff,#ff6fa5,#ffd1e8)",
        "👑 14-Day Streak": "linear-gradient(90deg,#f7b500,#ff6fa5,#ffd1e8)",
    }

    chips = '<div class="badge-wrap">'
    for b in badges:
        bg = rarity_bg.get(b, "linear-gradient(90deg,#ff6fa5,#ff9ecb)")
        shimmer_class = " shimmer" if any(x in b for x in ["💎", "👑", "🌸"]) else ""
        chips += f'<span class="badge-chip{shimmer_class}" style="background:{bg};">{b}</span>'
    chips += "</div>"
    st.markdown(chips, unsafe_allow_html=True)

# ==============================
# COUNTDOWN
# ==============================
days_left = (WEDDING_DATE - datetime.date.today()).days
st.subheader(f"{days_left} days until June 23, 2026")
st.progress(max(0, min(1, 1 - days_left / 365)))

# ==============================
# SIDEBAR: mascot + controls
# ==============================
st.sidebar.markdown(
    """
    <div style="text-align:center; margin-top:6px; margin-bottom:10px;">
        <img src="https://images.unsplash.com/photo-1619983081563-430f63602796?auto=format&fit=crop&w=400&q=60"
             width="150"
             style="border-radius:22px; box-shadow: 0 8px 18px rgba(0,0,0,0.12);">
        <div style="font-weight:900; color:#ff6fa5; margin-top:8px;">
            🐶 Cut Companion
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

sound_on = st.sidebar.toggle("🔊 Sound effects", value=True)

if st.sidebar.button("🔔 Enable sound (tap once)"):
    play_badge_sound(True)
    st.toast("Sound enabled 💗", icon="🔊")

if st.sidebar.button("🔄 Refresh data"):
    st.cache_data.clear()
    st.toast("Refreshed ✨")

# ==============================
# SIDEBAR NAV: categories (buttons) + pages (radio)
# ==============================
st.sidebar.markdown("## 🧭 Menu")

if "nav_group" not in st.session_state:
    st.session_state.nav_group = "Daily"

if st.sidebar.button("💗 Daily", use_container_width=True):
    st.session_state.nav_group = "Daily"
if st.sidebar.button("📊 Stats", use_container_width=True):
    st.session_state.nav_group = "Stats"
if st.sidebar.button("🧩 Body", use_container_width=True):
    st.session_state.nav_group = "Body"

group = st.session_state.nav_group

if group == "Daily":
    page = st.sidebar.radio("", ["Today Log"], label_visibility="collapsed")
elif group == "Stats":
    page = st.sidebar.radio("", ["Week Summary", "Month Summary", "Year Summary"], label_visibility="collapsed")
else:
    page = st.sidebar.radio("", ["Weight Progress", "Workouts"], label_visibility="collapsed")

# ==============================
# TODAY LOG
# ==============================
if page == "Today Log":
    today = str(datetime.date.today())

    meals_all = read_records("Meals")
    daily = compute_daily_totals(meals_all)

    st.markdown("## 🎮 Gecko Quest Status")
    st.markdown(
        '<div style="font-size:20px;margin-top:-6px;margin-bottom:10px;">'
        '<span class="gecko-bounce">🦎</span> '
        '<span style="color:#ff6fa5;font-weight:900;">Quest HUD</span> '
        '<span style="color:#ff9ecb;font-weight:800;">(streaks & rewards)</span>'
        '</div>',
        unsafe_allow_html=True
    )

    if not daily.empty:
        daily["hit_protein"] = daily.get("protein", 0) >= PROTEIN_TARGET
        daily["perfect_day"] = (daily.get("protein", 0) >= PROTEIN_TARGET) & (daily.get("calories", 0) <= CAL_TARGET)

        protein_streak = current_streak(daily, "hit_protein")
        perfect_streak = current_streak(daily, "perfect_day")

        col1, col2 = st.columns(2)
        with col1:
            cute_xp_card("Protein Streak", protein_streak, 7, "🦎")
        with col2:
            cute_xp_card("Perfect Day Streak", perfect_streak, 7, "💗")

        today_dt = pd.to_datetime(datetime.date.today())
        today_row = daily.loc[today_dt] if today_dt in daily.index else None

        unlocked = ["🥚 First Log"]

        if today_row is not None:
            if float(today_row.get("protein", 0)) >= PROTEIN_TARGET:
                unlocked.append("🦎 Protein Boss")
            if (float(today_row.get("protein", 0)) >= PROTEIN_TARGET) and (float(today_row.get("calories", 0)) <= CAL_TARGET):
                unlocked.append("🌸 Perfect Day")

        if protein_streak >= 3:
            unlocked.append("🔥 3-Day Streak")
        if protein_streak >= 7:
            unlocked.append("💎 7-Day Streak")
        if protein_streak >= 14:
            unlocked.append("👑 14-Day Streak")

        st.markdown("### 🏆 Badges Unlocked")
        render_badges(unlocked)

        key = f"badge_pop_{datetime.date.today()}"
        if "badge_pop_key" not in st.session_state:
            st.session_state["badge_pop_key"] = ""

        if unlocked and st.session_state["badge_pop_key"] != key:
            st.toast("✨ Badge unlocked!", icon="🏆")
            play_badge_sound(sound_on)

            if "🌸 Perfect Day" in unlocked:
                confetti()

            st.session_state["badge_pop_key"] = key
    else:
        st.info("Log your first meal to start streaks and unlock badges! 🦎✨")

    # Smart Food Entry
    st.subheader("🦎 Smart Food Entry")

    food_data = read_records("FoodDatabase")
    if food_data.empty or "food_name" not in food_data.columns:
        st.error("FoodDatabase is empty or headers are wrong. Column A must be 'food_name'.")
        st.stop()

    food_names = food_data["food_name"].astype(str).tolist()
    selected_food = st.selectbox("Select Food", food_names)
    grams = st.number_input("Grams", min_value=0, step=1)

    if selected_food and grams > 0:
        food_row = food_data[food_data["food_name"].astype(str) == str(selected_food)].iloc[0]
        protein = (grams / 100) * float(food_row["protein_per_100g"])
        fat = (grams / 100) * float(food_row["fat_per_100g"])
        carbs = (grams / 100) * float(food_row["carbs_per_100g"])
        calories = (grams / 100) * float(food_row["calories_per_100g"])

        st.write(f"Protein: {protein:.1f}g")
        st.write(f"Fat: {fat:.1f}g")
        st.write(f"Carbs: {carbs:.1f}g")
        st.write(f"Calories: {calories:.1f} kcal")

        if st.button("Add Smart Entry"):
            append_row("Meals", [
                today,
                str(datetime.datetime.now()),
                str(selected_food),
                round(protein, 1),
                round(fat, 1),
                round(carbs, 1),
                round(calories, 1),
                "",
                ""
            ])
            st.success("Meal added!")

    # Manual Entry
    st.subheader("🍓 Manual Entry")

    meal_name = st.text_input("Meal Name")
    protein_m = st.number_input("Protein (g)", min_value=0.0, step=1.0)
    fat_m = st.number_input("Fat (g)", min_value=0.0, step=1.0)
    carbs_m = st.number_input("Carbs (g)", min_value=0.0, step=1.0)

    calories_m = protein_m * 4 + fat_m * 9 + carbs_m * 4
    st.write(f"Calories: {calories_m:.1f} kcal")

    if st.button("Add Manual Entry"):
        append_row("Meals", [
            today,
            str(datetime.datetime.now()),
            meal_name,
            protein_m,
            fat_m,
            carbs_m,
            calories_m,
            "",
            ""
        ])
        st.success("Manual meal added!")

    # Today's Summary
    st.subheader("💗 Today's Summary")

    meals = read_records("Meals")
    if meals.empty:
        st.info("No meals yet today.")
    else:
        if "date" not in meals.columns:
            st.error("Meals sheet must have a column named 'date'.")
            st.stop()

        df_today = meals[meals["date"].astype(str) == today]
        if df_today.empty:
            st.info("No meals logged for today yet.")
        else:
            total_p = float(df_today.get("protein", 0).sum())
            total_f = float(df_today.get("fat", 0).sum())
            total_c = float(df_today.get("carbs", 0).sum())
            total_cal = float(df_today.get("calories", 0).sum())

            cute_xp_card("Protein Today", total_p, PROTEIN_TARGET, "🦎")
            cute_xp_card("Calories Today", total_cal, CAL_TARGET, "💗")

            st.write(f"Fat: {total_f:.1f} / {FAT_TARGET}  (Remaining: {max(0, FAT_TARGET-total_f):.1f} g)")
            st.write(f"Carbs: {total_c:.1f} / {CARB_TARGET}  (Remaining: {max(0, CARB_TARGET-total_c):.1f} g)")

            protein_score = min(total_p / PROTEIN_TARGET, 1)
            calorie_score = min(total_cal / CAL_TARGET, 1)
            fat_score = 1 - min(total_f / FAT_TARGET, 1)
            score = (protein_score * 0.5 + calorie_score * 0.3 + fat_score * 0.2) * 100
            st.subheader(f"✨ Today's Score: {int(score)} / 100")

# ==============================
# WEEK SUMMARY
# ==============================
elif page == "Week Summary":
    st.subheader("🦎 Weekly Summary")

    meals = read_records("Meals")
    if meals.empty:
        st.info("No meal history yet.")
    else:
        meals["date"] = pd.to_datetime(meals["date"], errors="coerce")
        meals = meals.dropna(subset=["date"])

        today_dt = pd.to_datetime(datetime.date.today())
        week_start = today_dt - pd.Timedelta(days=today_dt.weekday())
        week_data = meals[meals["date"] >= week_start]

        if week_data.empty:
            st.info("No meals logged this week yet.")
        else:
            daily = week_data.groupby("date").sum(numeric_only=True)
            cute_xp_card("Weekly Avg Calories", daily["calories"].mean(), CAL_TARGET, "💗")
            if "protein" in daily.columns:
                cute_xp_card("Weekly Avg Protein", daily["protein"].mean(), PROTEIN_TARGET, "🦎")

            d = daily.reset_index()
            d["date_str"] = pd.to_datetime(d["date"]).dt.strftime("%a %m/%d")
            st.plotly_chart(
                cute_line_chart(d, "date_str", "calories", "🌸 Weekly Calories Trail", goal=CAL_TARGET, y_suffix=" kcal"),
                use_container_width=True
            )

# ==============================
# MONTH SUMMARY
# ==============================
elif page == "Month Summary":
    st.subheader("🌸 Monthly Summary")

    meals = read_records("Meals")
    if meals.empty:
        st.info("No meal history yet.")
    else:
        meals["date"] = pd.to_datetime(meals["date"], errors="coerce")
        meals = meals.dropna(subset=["date"])

        today_dt = pd.to_datetime(datetime.date.today())
        this_month = meals[(meals["date"].dt.month == today_dt.month) & (meals["date"].dt.year == today_dt.year)]

        if this_month.empty:
            st.info("No meals logged this month yet.")
        else:
            daily = this_month.groupby("date").sum(numeric_only=True)
            cute_xp_card("Monthly Avg Calories", daily["calories"].mean(), CAL_TARGET, "💗")
            if "protein" in daily.columns:
                cute_xp_card("Monthly Avg Protein", daily["protein"].mean(), PROTEIN_TARGET, "🦎")

            d = daily.reset_index()
            d["date_str"] = pd.to_datetime(d["date"]).dt.strftime("%m/%d")
            st.plotly_chart(
                cute_line_chart(d, "date_str", "calories", "✨ Monthly Calories Map", goal=CAL_TARGET, y_suffix=" kcal"),
                use_container_width=True
            )

# ==============================
# YEAR SUMMARY
# ==============================
elif page == "Year Summary":
    st.subheader("✨ Yearly Summary")

    meals = read_records("Meals")
    if meals.empty:
        st.info("No meal history yet.")
    else:
        meals["date"] = pd.to_datetime(meals["date"], errors="coerce")
        meals = meals.dropna(subset=["date"])

        today_dt = pd.to_datetime(datetime.date.today())
        this_year = meals[meals["date"].dt.year == today_dt.year]

        if this_year.empty:
            st.info("No meals logged this year yet.")
        else:
            monthly = this_year.groupby(this_year["date"].dt.month).sum(numeric_only=True).reset_index()
            monthly.rename(columns={"date": "month"}, inplace=True)
            monthly["month_str"] = monthly["month"].apply(lambda m: f"{int(m)}月")

            st.plotly_chart(
                cute_line_chart(monthly, "month_str", "calories", "🗺️ Yearly Calories Quest"),
                use_container_width=True
            )

# ==============================
# WEIGHT
# ==============================
elif page == "Weight Progress":
    st.subheader("⚖️ Weight Progress")

    weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1)

    if st.button("Save Weight"):
        append_row("Weights", [str(datetime.date.today()), weight])
        st.success("Weight saved!")

    weights = read_records("Weights")
    if not weights.empty and "date" in weights.columns and "weight_kg" in weights.columns:
        weights["date"] = pd.to_datetime(weights["date"], errors="coerce")
        weights = weights.dropna(subset=["date"]).sort_values("date")
        w = weights.copy()
        w["date_str"] = w["date"].dt.strftime("%m/%d")

        st.plotly_chart(
            cute_line_chart(w, "date_str", "weight_kg", "⚖️ Weight Journey", y_suffix=" kg"),
            use_container_width=True
        )
    else:
        st.info("No weight history yet.")

# ==============================
# WORKOUTS
# ==============================
elif page == "Workouts":
    st.subheader("🏃 Workouts")

    workout_name = st.text_input("Workout Name")
    youtube_link = st.text_input("YouTube Link")
    notes = st.text_area("Notes")

    if st.button("Save Workout"):
        append_row("Workouts", [str(datetime.date.today()), workout_name, youtube_link, notes])
        st.success("Workout saved!")

    workouts = read_records("Workouts")
    if not workouts.empty:
        st.dataframe(workouts)
    else:
        st.info("No workouts logged yet.")

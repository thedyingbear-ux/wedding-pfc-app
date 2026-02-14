import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

# ==============================
# CONFIG
# ==============================
WEDDING_DATE = datetime.date(2026, 6, 23)

CAL_TARGET = 1200
PROTEIN_TARGET = 110
FAT_TARGET = 45
CARB_TARGET = 130

SPREADSHEET_NAME = "Wedding PFC Tracker"
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
    # worksheet objects are light; ok to fetch on demand
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
    # show new data immediately without hammering the API
    st.cache_data.clear()

# ==============================
# UI STYLE
# ==============================
st.set_page_config(page_title="Wedding Cut Tracker", layout="centered")

st.markdown("""
<style>
div.stButton > button {
    border-radius: 20px;
    background-color: #ffb6d9;
    color: white;
    border: none;
    padding: 0.5em 1.5em;
    font-weight: bold;
}
div.stButton > button:hover {
    background-color: #ff9ecb;
    color: white;
}
div.stProgress > div > div > div {
    background-color: #ff9ecb;
}
h1, h2, h3 { color: #ff6fa5; }
.block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

st.title("💍 Wedding Cut Dashboard")
st.markdown("<h4 style='color:#ff7fb0;'>🦎 Lean & Lovely Mode Activated 💗</h4>", unsafe_allow_html=True)

# Countdown
days_left = (WEDDING_DATE - datetime.date.today()).days
st.subheader(f"{days_left} days until June 23, 2026")
st.progress(max(0, min(1, 1 - days_left / 365)))

# Sidebar nav + manual refresh
page = st.sidebar.selectbox(
    "Navigation",
    ["Today Log", "Week Summary", "Month Summary", "Year Summary", "Weight Progress", "Workouts"]
)

if st.sidebar.button("🔄 Refresh data (if something looks outdated)"):
    st.cache_data.clear()
    st.toast("Refreshed ✨")

# ==============================
# TODAY LOG
# ==============================
if page == "Today Log":
    today = str(datetime.date.today())

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

    st.subheader("💗 Today's Summary")

    meals = read_records("Meals")
    if meals.empty:
        st.info("No meals yet today.")
    else:
        # normalize date column just in case
        if "date" not in meals.columns:
            st.error("Meals sheet must have a column named 'date'.")
            st.stop()

        df_today = meals[meals["date"].astype(str) == today]
        if df_today.empty:
            st.info("No meals logged for today yet.")
        else:
            total_p = float(df_today["protein"].sum())
            total_f = float(df_today["fat"].sum())
            total_c = float(df_today["carbs"].sum())
            total_cal = float(df_today["calories"].sum())

            st.write(f"Calories: {total_cal:.1f} / {CAL_TARGET}")
            st.progress(min(total_cal / CAL_TARGET, 1))

            st.write(f"Protein: {total_p:.1f} / {PROTEIN_TARGET}")
            st.write(f"Remaining: {max(0, PROTEIN_TARGET - total_p):.1f} g")

            st.write(f"Fat: {total_f:.1f} / {FAT_TARGET}")
            st.write(f"Remaining: {max(0, FAT_TARGET - total_f):.1f} g")

            st.write(f"Carbs: {total_c:.1f} / {CARB_TARGET}")
            st.write(f"Remaining: {max(0, CARB_TARGET - total_c):.1f} g")

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
            st.write("Total This Week:")
            st.write(daily.sum())
            st.write("Average Per Day:")
            st.write(daily.mean())
            st.line_chart(daily[["calories"]])

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
            st.write("Total This Month:")
            st.write(daily.sum())
            st.write("Average Per Day:")
            st.write(daily.mean())
            st.line_chart(daily[["calories"]])

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
            monthly = this_year.groupby(this_year["date"].dt.month).sum(numeric_only=True)
            st.write("Total This Year:")
            st.write(monthly.sum())
            st.line_chart(monthly[["calories"]])

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
        st.line_chart(weights.set_index("date")["weight_kg"])
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

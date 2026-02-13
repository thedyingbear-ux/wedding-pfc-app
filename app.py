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

# ==============================
# GOOGLE AUTH
# ==============================

scope = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope,
)

gc = gspread.authorize(creds)
sheet = gc.open(SPREADSHEET_NAME)

meals_sheet = sheet.worksheet("Meals")
weights_sheet = sheet.worksheet("Weights")
workouts_sheet = sheet.worksheet("Workouts")
food_sheet = sheet.worksheet("FoodDatabase")

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
h1, h2, h3 {
    color: #ff6fa5;
}
.block-container {
    padding-top: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

st.title("💍 Wedding Cut Dashboard")
st.markdown("<h4 style='color:#ff7fb0;'>🦎 Lean & Lovely Mode Activated 💗</h4>", unsafe_allow_html=True)

# ==============================
# COUNTDOWN
# ==============================

days_left = (WEDDING_DATE - datetime.date.today()).days
st.subheader(f"{days_left} days until June 23, 2026")
st.progress(max(0, min(1, 1 - days_left/365)))

# ==============================
# NAVIGATION
# ==============================

page = st.sidebar.selectbox(
    "Navigation",
    [
        "Today Log",
        "Week Summary",
        "Month Summary",
        "Year Summary",
        "Weight Progress",
        "Workouts"
    ]
)

# ==============================
# TODAY LOG
# ==============================

if page == "Today Log":

    today = str(datetime.date.today())

    # Smart Food Entry
    st.subheader("🦎 Smart Food Entry")

    food_data = pd.DataFrame(food_sheet.get_all_records())
    food_names = food_data["food_name"].tolist()

    selected_food = st.selectbox("Select Food", food_names)
    grams = st.number_input("Grams", 0)

    if selected_food and grams > 0:
        food_row = food_data[food_data["food_name"] == selected_food].iloc[0]

        protein = (grams / 100) * food_row["protein_per_100g"]
        fat = (grams / 100) * food_row["fat_per_100g"]
        carbs = (grams / 100) * food_row["carbs_per_100g"]
        calories = (grams / 100) * food_row["calories_per_100g"]

        st.write(f"Protein: {round(protein,1)}g")
        st.write(f"Fat: {round(fat,1)}g")
        st.write(f"Carbs: {round(carbs,1)}g")
        st.write(f"Calories: {round(calories,1)} kcal")

        if st.button("Add Smart Entry"):
            meals_sheet.append_row([
                today,
                str(datetime.datetime.now()),
                selected_food,
                round(protein,1),
                round(fat,1),
                round(carbs,1),
                round(calories,1),
                "",
                ""
            ])
            st.success("Meal added!")

    # Manual Entry
    st.subheader("🍓 Manual Entry")

    meal_name = st.text_input("Meal Name")
    protein_m = st.number_input("Protein (g)", 0.0)
    fat_m = st.number_input("Fat (g)", 0.0)
    carbs_m = st.number_input("Carbs (g)", 0.0)

    calories_m = protein_m * 4 + fat_m * 9 + carbs_m * 4
    st.write(f"Calories: {round(calories_m,1)} kcal")

    if st.button("Add Manual Entry"):
        meals_sheet.append_row([
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

    # Daily Summary
    st.subheader("💗 Today's Summary")

    data = pd.DataFrame(meals_sheet.get_all_records())

    if not data.empty:
        df_today = data[data["date"] == today]

        total_p = df_today["protein"].sum()
        total_f = df_today["fat"].sum()
        total_c = df_today["carbs"].sum()
        total_cal = df_today["calories"].sum()

        st.write(f"Calories: {round(total_cal,1)} / {CAL_TARGET}")
        st.progress(min(total_cal / CAL_TARGET, 1))

        st.write(f"Protein: {round(total_p,1)} / {PROTEIN_TARGET}")
        st.write(f"Remaining: {max(0, round(PROTEIN_TARGET - total_p,1))} g")

        st.write(f"Fat: {round(total_f,1)} / {FAT_TARGET}")
        st.write(f"Remaining: {max(0, round(FAT_TARGET - total_f,1))} g")

        st.write(f"Carbs: {round(total_c,1)} / {CARB_TARGET}")
        st.write(f"Remaining: {max(0, round(CARB_TARGET - total_c,1))} g")

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

    data = pd.DataFrame(meals_sheet.get_all_records())

    if not data.empty:
        data["date"] = pd.to_datetime(data["date"])
        today_dt = pd.to_datetime(datetime.date.today())
        week_start = today_dt - pd.Timedelta(days=today_dt.weekday())

        week_data = data[data["date"] >= week_start]

        if not week_data.empty:
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

    data = pd.DataFrame(meals_sheet.get_all_records())

    if not data.empty:
        data["date"] = pd.to_datetime(data["date"])
        today_dt = pd.to_datetime(datetime.date.today())

        this_month = data[
            (data["date"].dt.month == today_dt.month) &
            (data["date"].dt.year == today_dt.year)
        ]

        if not this_month.empty:
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

    data = pd.DataFrame(meals_sheet.get_all_records())

    if not data.empty:
        data["date"] = pd.to_datetime(data["date"])
        today_dt = pd.to_datetime(datetime.date.today())

        this_year = data[data["date"].dt.year == today_dt.year]

        if not this_year.empty:
            monthly = this_year.groupby(this_year["date"].dt.month).sum(numeric_only=True)

            st.write("Total This Year:")
            st.write(monthly.sum())

            st.line_chart(monthly[["calories"]])

# ==============================
# WEIGHT
# ==============================

elif page == "Weight Progress":

    weight = st.number_input("Weight (kg)", 0.0)

    if st.button("Save Weight"):
        weights_sheet.append_row([
            str(datetime.date.today()),
            weight
        ])
        st.success("Weight saved!")

    data = pd.DataFrame(weights_sheet.get_all_records())

    if not data.empty:
        data["date"] = pd.to_datetime(data["date"])
        data = data.sort_values("date")
        st.line_chart(data.set_index("date")["weight_kg"])

# ==============================
# WORKOUTS
# ==============================

elif page == "Workouts":

    workout_name = st.text_input("Workout Name")
    youtube_link = st.text_input("YouTube Link")
    notes = st.text_area("Notes")

    if st.button("Save Workout"):
        workouts_sheet.append_row([
            str(datetime.date.today()),
            workout_name,
            youtube_link,
            notes
        ])
        st.success("Workout saved!")

    data = pd.DataFrame(workouts_sheet.get_all_records())

    if not data.empty:
        st.dataframe(data)

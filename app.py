import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# ==============================
# CONFIG
# ==============================

WEDDING_DATE = datetime.date(2026, 6, 23)

CAL_TARGET = 1200
PROTEIN_TARGET = 110
FAT_TARGET = 45
CARB_TARGET = 130

SPREADSHEET_NAME = "Wedding PFC Tracker"
DRIVE_FOLDER_NAME = "Wedding Food Photos"

# ==============================
# GOOGLE AUTH
# ==============================

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope,
)

gc = gspread.authorize(creds)
drive_service = build("drive", "v3", credentials=creds)

sheet = gc.open(SPREADSHEET_NAME)
meals_sheet = sheet.worksheet("Meals")
weights_sheet = sheet.worksheet("Weights")
workouts_sheet = sheet.worksheet("Workouts")

# ==============================
# UI STYLE
# ==============================

st.set_page_config(page_title="Wedding Cut Tracker", layout="centered")

st.markdown("""
<style>
body {
    background-color: #f8f9fb;
}
h1, h2, h3 {
    color: #333333;
}
.block-container {
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

st.title("💍 Wedding Cut Dashboard")

# ==============================
# COUNTDOWN BAR
# ==============================

days_left = (WEDDING_DATE - datetime.date.today()).days
progress = 1 - (days_left / 365)

st.subheader(f"Countdown: {days_left} days left")
st.progress(min(max(progress, 0), 1))

# ==============================
# PAGE NAVIGATION
# ==============================

page = st.sidebar.selectbox(
    "Navigation",
    ["Today Log", "Photo Gallery", "Workouts", "Weight Progress"]
)

# ==============================
# TODAY LOG
# ==============================

if page == "Today Log":

    today = str(datetime.date.today())

    st.subheader("Add Meal")

    meal_name = st.text_input("Meal Name")
    protein = st.number_input("Protein (g)", 0)
    fat = st.number_input("Fat (g)", 0)
    carbs = st.number_input("Carbs (g)", 0)
    notes = st.text_area("Notes")
    image = st.file_uploader("Upload Photo")

    calories = protein * 4 + fat * 9 + carbs * 4
    st.write(f"Calories: {calories} kcal")

    image_url = ""

    if st.button("Save Meal"):

        if image:
            file_metadata = {
                'name': image.name,
                'parents': []
            }
            media = MediaIoBaseUpload(io.BytesIO(image.read()), mimetype=image.type)
            file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            image_url = f"https://drive.google.com/file/d/{file.get('id')}/view"

        meals_sheet.append_row([
            today,
            str(datetime.datetime.now()),
            meal_name,
            protein,
            fat,
            carbs,
            calories,
            notes,
            image_url
        ])

        st.success("Meal saved!")

    st.subheader("Today's Summary")

    data = meals_sheet.get_all_records()
    df = pd.DataFrame(data)

    if not df.empty:
        df_today = df[df["date"] == today]

        total_p = df_today["protein"].sum()
        total_f = df_today["fat"].sum()
        total_c = df_today["carbs"].sum()
        total_cal = df_today["calories"].sum()

        st.write(f"Calories: {total_cal}/{CAL_TARGET}")
        st.progress(min(total_cal / CAL_TARGET, 1))

        st.write(f"Protein: {total_p}/{PROTEIN_TARGET}")
        st.progress(min(total_p / PROTEIN_TARGET, 1))

        st.write(f"Fat: {total_f}/{FAT_TARGET}")
        st.progress(min(total_f / FAT_TARGET, 1))

        st.write(f"Carbs: {total_c}/{CARB_TARGET}")
        st.progress(min(total_c / CARB_TARGET, 1))

        score = (
            min(total_p / PROTEIN_TARGET, 1) * 0.4 +
            min(total_cal / CAL_TARGET, 1) * 0.3 +
            min(total_c / CARB_TARGET, 1) * 0.2 +
            (1 - min(total_f / FAT_TARGET, 1)) * 0.1
        ) * 100

        st.subheader(f"Today's Score: {int(score)} / 100")

# ==============================
# PHOTO GALLERY
# ==============================

elif page == "Photo Gallery":

    st.subheader("Food Photo Gallery")

    data = meals_sheet.get_all_records()
    df = pd.DataFrame(data)

    for index, row in df.iterrows():
        if row["image_url"]:
            st.image(row["image_url"], caption=row["meal_name"])

# ==============================
# WORKOUTS
# ==============================

elif page == "Workouts":

    st.subheader("Log Workout")

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

    st.subheader("Workout History")

    data = workouts_sheet.get_all_records()
    df = pd.DataFrame(data)

    if not df.empty:
        st.dataframe(df)

# ==============================
# WEIGHT
# ==============================

elif page == "Weight Progress":

    st.subheader("Log Weight")

    weight = st.number_input("Weight (kg)", 0.0)

    if st.button("Save Weight"):
        weights_sheet.append_row([
            str(datetime.date.today()),
            weight
        ])
        st.success("Weight saved!")

    data = weights_sheet.get_all_records()
    df = pd.DataFrame(data)

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        st.line_chart(df.set_index("date")["weight_kg"])

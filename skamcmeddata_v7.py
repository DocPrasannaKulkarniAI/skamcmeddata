"""
SKAMCSHRC | OPD Clinical Data Entry System v7.0
Sri Kalabyraveshwara Swamy Ayurvedic Medical College, Hospital & Research Centre

Conceptized by : Dr. Kiran M Goud, MD (Ay.)
Developed by   : Dr. Prasanna Kulkarni, MD (Ay.), MS (Data Science)
Storage        : Google Sheets (persistent, multi-device)
ACD Codes      : Namaste Portal (newACD.xlsx) | SAT-I Codes: WHO

─────────────────────────────────────────────────────────────────
SETUP FOR GOOGLE SHEETS (do this once):
1. Go to console.cloud.google.com → create a project
2. Enable "Google Sheets API" and "Google Drive API"
3. Create a Service Account → download JSON key
4. Share your Google Sheet with the service account email (Editor)
5. In Streamlit Cloud → Settings → Secrets, add:

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "your-sa@your-project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."

[sheet]
name = "SKAMCSHRC_OPD_Data"
─────────────────────────────────────────────────────────────────
Run : streamlit run skamcmeddata_v7.py
Place newACD.xlsx in the same folder.
"""

import streamlit as st
import pandas as pd
import re, io
from datetime import date, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG & CSS
# ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="SKAMCSHRC OPD", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif:wght@400;700&family=Inter:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
h1,h2,h3{font-family:'Noto Serif',serif;}
.main-hdr{background:linear-gradient(135deg,#1a3a2a,#2d5a3d);border-radius:10px;
  padding:14px 22px;margin-bottom:16px;border-left:5px solid #c8a96e;}
.main-hdr h2{color:#f5e6c8;margin:0;font-size:1.22rem;}
.main-hdr p{color:#a8c5a0;margin:3px 0 0;font-size:0.76rem;}
.sec{font-size:0.74rem;font-weight:600;text-transform:uppercase;letter-spacing:1.1px;
  color:#2d6a4f;border-bottom:1px solid #b7d9c5;padding-bottom:5px;margin-bottom:10px;}
.card{background:#f8faf9;border:1px solid #d1e5d8;border-radius:9px;
  padding:14px 17px;margin-bottom:11px;}
.badge{background:#e8f5e9;border:1px solid #81c784;border-radius:4px;
  padding:2px 7px;font-size:0.73rem;font-weight:600;color:#2e7d32;font-family:monospace;}
.code-big{background:#1a3a2a;color:#f5e6c8;border-radius:5px;
  padding:4px 10px;font-size:0.85rem;font-weight:700;font-family:monospace;letter-spacing:0.5px;}
.triage-u{background:#fef3c7;border:2px solid #d97706;border-radius:7px;
  padding:7px 12px;font-weight:600;color:#92400e;display:inline-block;}
.triage-r{background:#dcfce7;border:2px solid #16a34a;border-radius:7px;
  padding:7px 12px;font-weight:600;color:#14532d;display:inline-block;}
.bmi-box{background:#e3f2fd;border:1px solid #90caf9;border-radius:7px;
  padding:7px 13px;text-align:center;font-weight:600;color:#1565c0;}
.tx-summary{background:#fff8e1;border:1px solid #ffe082;border-radius:7px;
  padding:10px 14px;margin:6px 0;font-size:0.85rem;line-height:1.7;}
.proc-cmt{background:#f0fff4;border-left:3px solid #2d6a4f;
  border-radius:0 7px 7px 0;padding:6px 12px;margin:4px 0;}
.med-row{background:#faf5ff;border:1px solid #d8b4fe;border-radius:8px;
  padding:12px 15px;margin:7px 0;}
.med-num{font-weight:700;color:#6d28d9;font-size:0.9rem;margin-bottom:6px;}
.followup-box{background:#fff3cd;border:2px solid #ffc107;border-radius:9px;
  padding:14px 18px;margin:10px 0;}
.followup-box h4{color:#856404;margin:0 0 8px 0;font-size:0.95rem;}
.followup-box p{color:#533f03;margin:0;font-size:0.87rem;line-height:1.5;}
.returning-banner{background:#e8f4fd;border:2px solid #2196f3;border-radius:9px;
  padding:12px 16px;margin:8px 0;}
.returning-banner h4{color:#1565c0;margin:0 0 6px 0;font-size:0.95rem;}
.search-result{background:#f0f7f3;border:1px solid #81c784;border-radius:7px;padding:8px 12px;margin-top:4px;}
.stTabs [data-baseweb="tab-list"]{gap:4px;}
.stTabs [data-baseweb="tab"]{height:42px;background:#f0f7f3;border-radius:8px 8px 0 0;
  border:1px solid #c8dfd0;font-weight:500;color:#2d5a3d;font-size:0.86rem;}
.stTabs [aria-selected="true"]{background:#2d5a3d !important;
  color:#f5e6c8 !important;border-color:#2d5a3d !important;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# GOOGLE SHEETS INTEGRATION
# ─────────────────────────────────────────────────────────────────
SHEET_COLS = [
    "Patient_ID","Visit_Date","Visit_Time","Visit_DateTime","Visit_Year","Visit_Type",
    "Consultation_Type","Age","Gender","District","Occupation","Prakriti","Lifestyle_Risk",
    "Triage","Department","Physician","Chief_Complaints","Chief_Complaints_Modified",
    "ACD_Code_1","ACD_Meaning_1","ACD_Code_2","ACD_Meaning_2","Severity","Disease_Duration",
    "Height_cm","Weight_kg","BMI","BMI_Category","BP","Pulse_bpm","Temp_F","SpO2_pct","RR_per_min",
    "Other_Investigation","Nadi","Jihva","Agni","Mala","Mutra","Sleep","Shabda","Sparsha","Drik","Akriti",
    "Dosha","Dushya","Bala","Kala","Satva","Satmya","Vyasana","Prakriti_Confirmed",
    "Final_ACD_Code","Final_ACD_Meaning",
    "TX_Purvakarma","TX_Pradhana_Karma","TX_Pashchata_Karma",
    "TX_Comments_Purvakarma","TX_Comments_Pradhana","TX_Comments_Pashchata","TX_Custom",
    "Medicines_Summary","Lab_Tests","Instructions","Physician_Notes","Followup_Notes",
]

@st.cache_resource(show_spinner=False)
def get_sheet():
    """Connect to Google Sheet. Returns (sheet_object, error_message)."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        # Check secrets exist
        if "gcp_service_account" not in st.secrets:
            return None, "Secret [gcp_service_account] not found in Streamlit secrets."
        if "sheet" not in st.secrets:
            return None, "Secret [sheet] not found in Streamlit secrets."
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        sheet_name = st.secrets["sheet"]["name"]
        sh = client.open(sheet_name).sheet1
        return sh, None
    except Exception as e:
        return None, str(e)

def sheet_init_headers(sh):
    """Add header row if sheet is empty."""
    try:
        if not sh.row_values(1):
            sh.append_row(SHEET_COLS)
    except Exception:
        pass

def sheet_load_all(sh):
    """Load all records from sheet as list of dicts."""
    try:
        all_vals = sh.get_all_records()
        return all_vals
    except Exception:
        return []

def sheet_save_record(sh, rec):
    """Append or update record in sheet."""
    try:
        clean_rec = {k: clean(str(rec.get(k, ""))) for k in SHEET_COLS}
        row = [clean_rec.get(c, "") for c in SHEET_COLS]
        # Check if record with same Patient_ID + Visit_DateTime exists → update
        all_vals = sh.get_all_values()
        headers  = all_vals[0] if all_vals else SHEET_COLS
        try:
            pid_col  = headers.index("Patient_ID") + 1
            vdt_col  = headers.index("Visit_DateTime") + 1
        except ValueError:
            sh.append_row(row)
            return
        pid = clean_rec.get("Patient_ID", "")
        vdt = clean_rec.get("Visit_DateTime", "")
        for i, r in enumerate(all_vals[1:], start=2):
            if len(r) > max(pid_col-1, vdt_col-1):
                if r[pid_col-1] == pid and r[vdt_col-1] == vdt:
                    sh.update(f"A{i}", [row])
                    return
        sh.append_row(row)
    except Exception as e:
        st.warning(f"Google Sheets save warning: {e}")

def find_patient(all_records, patient_id):
    """Return all visits for a given patient ID, sorted by date."""
    return sorted(
        [r for r in all_records if str(r.get("Patient_ID","")) == str(patient_id)],
        key=lambda x: x.get("Visit_DateTime","")
    )

# ─────────────────────────────────────────────────────────────────
# ACD CODE LOADER — FLAT LIST FOR LIVE SEARCH
# ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_acd_flat(filepath="newACD.xlsx"):
    """Load all ACD leaf codes into a flat list for live search."""
    try:
        df = pd.read_excel(filepath)
        df.columns = ["ACD","code","condition","meaning"]
        df = df.dropna(subset=["code"])
        df["code"]      = df["code"].astype(str).str.strip()
        df["condition"] = df["condition"].fillna("").astype(str).str.strip()
        df["meaning"]   = df["meaning"].fillna("").astype(str).str.strip()
        def is_top(c): return bool(re.match(r"^[A-Z]{1,4}$", c))
        leaves = []
        for _, row in df[~df["code"].apply(is_top)].iterrows():
            leaves.append({
                "code":      row["code"],
                "condition": row["condition"],
                "meaning":   row["meaning"],
                "label":     f"{row['condition']} ({row['meaning']}) [{row['code']}]",
                "search":    f"{row['condition']} {row['meaning']} {row['code']}".lower(),
            })
        return leaves, True
    except FileNotFoundError:
        return [], False

ACD_FLAT, ACD_LOADED = load_acd_flat("newACD.xlsx")

def search_acd(query, max_results=40):
    """Search ACD codes by condition name, English meaning, or code."""
    if not query or len(query) < 2:
        return []
    q = query.lower().strip()
    # Exact code match first
    exact = [i for i in ACD_FLAT if i["code"].lower() == q]
    # Starts-with match
    starts = [i for i in ACD_FLAT if q in i["search"] and i not in exact]
    return (exact + starts)[:max_results]

def acd_search_widget(search_key, select_key, label="Search Diagnosis"):
    """
    Live search widget for ACD codes.
    Returns (label, code, meaning) tuple.
    """
    query = st.text_input(
        label,
        key=search_key,
        placeholder="Type condition name or English term (e.g. tonsil, sciatica, fever, AAB-6...)"
    )
    results = search_acd(query)
    if query and len(query) >= 2:
        if results:
            opts = ["— Select from results —"] + [r["label"] for r in results]
            sel = st.selectbox(f"Results ({len(results)} found)", opts, key=select_key)
            if sel != "— Select from results —":
                code    = sel.split("[")[-1].rstrip("]").strip()
                meaning = sel.split("(")[-1].split(")")[0].strip() if "(" in sel else ""
                st.markdown(
                    f'<span class="code-big">{code}</span>&nbsp;&nbsp;'
                    f'<span style="font-size:0.8rem;color:#555">{meaning}</span>',
                    unsafe_allow_html=True)
                return sel, code, meaning
        else:
            st.caption("No matches found. Try different keywords.")
    return "", "", ""

# ─────────────────────────────────────────────────────────────────
# STATIC DATA
# ─────────────────────────────────────────────────────────────────
DEPARTMENTS = {
    "KC":"Kaya Chikitsa (General Medicine)",
    "PK":"Panchakarma",
    "SPL":"Swasthavritta & Lifestyle (SPL)",
    "AGADA":"Agada Tantra (Toxicology & Dermatology)",
    "SHALYA":"Shalya Tantra (Surgery & Ano-Rectal)",
    "SHALAKYA":"Shalakya Tantra (Eye & ENT)",
    "KB":"Kaumarabhritya (Paediatrics under 16 yrs)",
    "PRASOOTI":"Prasooti Tantra (Obstetrics)",
    "STREE_ROGA":"Stri Roga (Gynaecology)",
    "YOGA":"Yoga & Wellness",
}
PHYSICIANS = {
    "Dr. Abdul":["KC","PK"],"Dr. Amrutha":["KC"],"Dr. Anjali":["SHALYA"],
    "Dr. Anupama":["PRASOOTI","STREE_ROGA"],"Dr. Chaitra N":["PRASOOTI","STREE_ROGA"],
    "Dr. Chetana":["PRASOOTI","STREE_ROGA"],"Dr. Elgeena":["SPL"],
    "Dr. Gopal TL":["AGADA","SPL"],"Dr. Hamsaveni":["SHALAKYA"],
    "Dr. Harshitha":["KC"],"Dr. Jambavathi":["SHALYA"],"Dr. Jyothi":["SPL"],
    "Dr. Karthik":["SPL"],"Dr. Kiran Kumar":["AGADA","SPL"],
    "Dr. Kiran M Goud":["PK"],"Dr. Lokeshwari":["KB"],"Dr. Lolashri":["PK"],
    "Dr. Mahantesh":["SPL"],"Dr. Manasa":["AGADA"],"Dr. Mangala":["KB"],
    "Dr. Manjunath":["KC","PK"],"Dr. Meera":["AGADA"],"Dr. Nayan":["KB"],
    "Dr. Nayana":["AGADA"],"Dr. Neetha":["AGADA"],"Dr. Neharu":["SHALYA"],
    "Dr. Nithyashree":["SHALAKYA"],"Dr. Padmavathi":["SHALAKYA"],
    "Dr. Papiya Jana":["PRASOOTI","STREE_ROGA"],"Dr. Pranesh":["KC"],
    "Dr. Prasanna":["SPL","YOGA"],"Dr. Prathibha":["SPL"],
    "Dr. Priyanka":["KB","SPL"],"Dr. Pushpa":["KB"],"Dr. Radhika":["AGADA"],
    "Dr. Roopini":["AGADA"],"Dr. Shailaja SV":["SHALYA"],
    "Dr. Shanthala":["SPL"],"Dr. Shashirekha":["KC","SPL","YOGA"],
    "Dr. Sheshashaye B":["SHALYA"],"Dr. Shilpa":["SPL"],
    "Dr. Shreyas":["KC","PK"],"Dr. Shridevi":["PRASOOTI","STREE_ROGA"],
    "Dr. Shubha V Hegde":["AGADA"],"Dr. Sindhura":["KC","PK"],
    "Dr. Sowmya":["PRASOOTI","STREE_ROGA"],"Dr. Sreekanth":["AGADA"],
    "Dr. Sujathamma":["SHALAKYA"],"Dr. Suma Saji":["AGADA"],
    "Dr. Sunayana":["SPL","YOGA"],"Dr. Sunitha GS":["AGADA","KC"],
    "Dr. Supreeth MJ":["KC","PK"],"Dr. Usha":["PK"],"Dr. Veena":["SHALAKYA"],
    "Dr. Venkatesh":["SHALAKYA"],"Dr. Vijayalakshmi":["KC","PK"],
    "Dr. Vinay Kumar KN":["KC","PK"],"Dr. Vishwanath":["SHALYA"],
}
DEPT_CONDITIONS = {
    "KC":["Fever / Pyrexia","Vomiting / Nausea","GIT Disorders","Tiredness / Fatigue",
          "Giddiness / Vertigo","Loss of Strength","Stroke / Hemiplegia","Facial Paralysis",
          "General Weakness","Cough / Respiratory","Cardiac Complaints","Jaundice / Liver",
          "Anaemia","Headache","Loss of Appetite","Constipation","Other"],
    "PK":["Pain - Low Back","Pain - Knee / Joint","Pain - Cervical / Neck","Pain - Shoulder",
          "Sciatica","Rheumatoid Arthritis","Osteoarthritis","Gout","Frozen Shoulder",
          "Hemiplegia (PK)","Facial Palsy (PK)","Neurological for Panchakarma","Other"],
    "SPL":["Obesity / Overweight","Diabetes Mellitus","High Cholesterol","Hypothyroidism",
           "Hyperthyroidism","Metabolic Syndrome","Hypertension (lifestyle)","Insomnia",
           "Stress / Anxiety","Chronic Fatigue","Other"],
    "AGADA":["Psoriasis","Eczema / Dermatitis","Hair Fall / Alopecia","Premature Greying",
             "Vitiligo / Leucoderma","Allergic Skin Reaction","Herpes / Spreading Eruption",
             "Acne / Pimples","Fungal Skin Infection","Toxic conditions","Other"],
    "SHALYA":["Haemorrhoids / Piles","Fistula-in-Ano","Fissure-in-Ano","Rectal Prolapse",
              "Wound / Ulcer","Fracture / Bone Injury","Abscess","Urinary complaints (Male)",
              "Urinary Incontinence","Kidney Stone","Other"],
    "SHALAKYA":["Diminished Vision","Cataract","Conjunctivitis / Red Eye","Eye Pain / Dryness",
                "Sinusitis / Rhinitis","Nasal Obstruction","Earache / Ear Discharge",
                "Hearing Loss / Tinnitus","Throat Pain / Tonsillitis","Oral / Dental Disorder","Other"],
    "KB":["Fever - Child","Diarrhoea - Child","Failure to Thrive","Juvenile Arthritis",
          "Cerebral Palsy","Childhood Asthma","Skin Disorder - Child","Worm Infestation",
          "Growth Retardation","Developmental / Behavioural Disorder","Other"],
    "PRASOOTI":["Morning Sickness","Back Pain in Pregnancy","Oedema in Pregnancy",
                "Gestational Diabetes","Gestational Hypertension","Threatened Abortion",
                "Foetal Complications","Antenatal Checkup","Post-partum Disorders",
                "Insufficient Lactation","Other"],
    "STREE_ROGA":["Menorrhagia","Irregular / Absent Periods","Dysmenorrhoea","Leucorrhoea",
                  "Infertility (Female)","PCOS / Ovarian Cyst","Uterine Fibroid",
                  "Menopausal Complaints","Pelvic Pain / PID","Vaginal Disorders","Other"],
    "YOGA":["Stress / Burnout","Insomnia","Low Immunity","Obesity (Yoga)",
            "Respiratory Wellness","General Wellness"],
}
PK_TREATMENTS = {
    "Purvakarma":[
        ("SAT-I.43","Snehana","Therapeutic Oleation (Internal / External)"),
        ("SAT-I.54","Svedana","Therapeutic Sudation / Fomentation"),
        ("SAT-I.439","Abhyanga","Therapeutic Full-body Oil Massage"),
        ("SAT-I.99","Udvartana","Dry Powder Massage (Reducing therapy)"),
        ("SAT-I.445","Sneha Pana","Internal Oleation — Ghee / Oil intake"),
    ],
    "Pradhana Karma":[
        ("SAT-I.139","Vamana Karma","Therapeutic Emesis"),
        ("SAT-I.140","Virecana Karma","Therapeutic Purgation"),
        ("SAT-I.141","Basti Karma","Therapeutic Enema (General)"),
        ("SAT-I.142","Anuvasan Basti","Unctuous / Oil Enema"),
        ("SAT-I.145","Asthapana Basti","Decoction Enema (Niruha Basti)"),
        ("SAT-I.144","Matra Basti","Small-dose Unctuous Enema"),
        ("SAT-I.155","Uttara Basti","Intra-vaginal / Urethral Basti"),
        ("SAT-I.156","Nasya","Nasal Medication (Errhine Therapy)"),
        ("SAT-I.413","Raktamokshana","Bloodletting / Leech Therapy"),
    ],
    "Pashchata Karma":[
        ("SAT-I.86","Shiro Basti","Oil Retention over Head"),
        ("SAT-I.89","Shirodhara","Oil Streaming over Head"),
        ("SAT-I.90","Takra Dhara","Buttermilk Streaming"),
        ("SAT-I.91","Kashaya Dhara","Medicated Decoction Streaming"),
        ("SAT-I.92","Manya Basti","Oil Retention — Cervical Region"),
        ("SAT-I.93","Hrid Basti","Oil Retention — Cardiac Region"),
        ("SAT-I.94","Prishtha Basti","Oil Retention — Thoraco-lumbar Region"),
        ("SAT-I.95","Kati Basti","Oil Retention — Lumbo-sacral Region"),
        ("SAT-I.96","Janu Basti","Oil Retention — Knee Region"),
        ("SAT-I.123","Pinda Sveda","Bolus Sudation / Kizhi / Pottali"),
        ("SAT-I.112","Nadi Sveda","Steam Pipe Fomentation"),
        ("SAT-I.114","Avagaha Sveda","Medicated Tub Bath Sudation"),
        ("SAT-I.241","Netra Tarpana","Eye Retention Therapy"),
        ("SAT-I.286","Karna Purana","Therapeutic Ear Oil Filling"),
        ("SAT-I.490","Kavala Dharana","Oil Pulling / Therapeutic Gargling"),
        ("SAT-I.55","Lepa","Medicated Paste Application"),
        ("SAT-I.438","Parisheka","Medicated Streaming over Body Part"),
        ("SAT-I.406","Kshara Karma","Caustic Application (Kshara Sutra)"),
        ("SAT-I.409","Agni Karma","Thermal Cauterization"),
    ],
}
DOSAGE_FORMS=["Churna (Powder)","Kashaya (Decoction)","Vati / Gutika (Tablet/Pill)",
               "Ghrita (Medicated Ghee)","Taila (Medicated Oil)","Capsule","Avaleha (Linctus)",
               "Asava / Arishta (Fermented)","Bhasma (Calcined)","Syrup","Kwatha",
               "Lepa (Topical paste)","Drops","— Custom —"]
ROUTE_OPTIONS=["Oral","External / Topical","Nasal","Rectal","Ophthalmic","Otic (Ear)",
                "Sublingual","Inhalation","— Custom —"]
DOSE_OPTIONS=["1 OD","1 BD","1 TID","2 BD","2 TID","1 HS","SOS",
               "5 ml OD","5 ml BD","5 ml TID","10 ml OD","10 ml BD","10 ml TID",
               "1 tsp OD","1 tsp BD","1 tsp TID","— Custom —"]
TIMING_OPTIONS=["Before food","After food","Between meals","At bedtime","Empty stomach","With food"]
ANUPANA_OPTIONS=["Water","Warm water","Milk","Honey","Ghee","Buttermilk","Coconut water",
                  "Ginger juice","Cold water","Fruit juice","— Custom —"]
DURATION_UNIT=["Days","Weeks","Months"]
PRAKRITI_OPT=["VataPitta","VataKapha","PittaVata","PittaKapha","KaphaVata","KaphaPitta",
               "Vata Pradhana","Pitta Pradhana","Kapha Pradhana","SamaDosha"]
NADI_OPT=["Vata Pradhana (60-80 bpm)","Pitta Pradhana (70-80 bpm)","Kapha Pradhana (60-70 bpm)",
           "Vata-Pitta","Pitta-Kapha","Vata-Kapha","Tridosha","Not recorded","Other (specify below)"]
JIHVA_OPT=["Sama / Lipta (Coated)","Nirama / Shuddha (Clean)","Ruksha (Dry)","Ardra (Moist)",
            "Shveta Lipta","Pita Lipta","Krishna Lipta","Other (specify below)"]
AGNI_OPT=["Sama Agni (Normal)","Vishama Agni (Irregular)","Tikshna Agni (Hyperacid)",
           "Manda Agni (Sluggish)","Other (specify below)"]
MALA_OPT=["Samyak (1-2/day, formed)","Vibandha (Constipated)","Atisara (Loose/Frequent)",
           "Amayukta (Mucus/Undigested)","2-3/day","3-4/day","More than 4/day","Other (specify below)"]
MUTRA_OPT=["Samyak (4-6/day, clear)","Alpa (Oliguria)","Adhika (Polyuria)",
            "Krichra (Dysuria)","4-5/day","6-8/day","Nocturia","Other (specify below)"]
SLEEP_OPT=["Samyak Nidra (6-8 hrs)","Nidranasha (Insomnia)","Atinidra (Hypersomnia)",
            "Disturbed / Fragmented","Early morning waking","Difficulty initiating","Other (specify below)"]
DOSHA_OPT=["Vata Pradhana","Pitta Pradhana","Kapha Pradhana","Vata-Pitta","Pitta-Kapha",
            "Vata-Kapha","Tridosha","Other (specify below)"]
DUSHYA_OPT=["Rasa","Rakta","Mamsa","Meda","Asthi","Majja","Shukra / Artava","Other (specify below)"]
BALA_OPT=["Pravara Bala (Strong)","Madhyama Bala (Moderate)","Avara Bala (Weak)","Other (specify below)"]
KALA_OPT=["Vasanta (Spring Mar/Apr)","Grishma (Summer May/Jun)","Varsha (Monsoon Jul/Aug)",
           "Sharad (Autumn Sep/Oct)","Hemanta (Early Winter Nov/Dec)","Shishira (Late Winter Jan/Feb)"]
SATVA_OPT=["Sattva Pradhana","Rajas Pradhana","Tamas Pradhana","Madhyama","Other (specify below)"]
SATMYA_OPT=["Sarva Satmya","Desha Satmya","Kula Satmya","Madhyama","Other (specify below)"]
SHABDA_OPT=SPARSHA_OPT=DRIK_OPT=["Prakruta (Normal)","Vikruta (Altered)","Not assessed","Other (specify below)"]
AKRITI_OPT=["Prakruta (Normal)","Vikruta (Abnormal)","Not assessed","Other (specify below)"]
VYASANA_OPT=["None (NA)","Dhumapana (Smoking)","Madyapana (Alcohol)",
              "Tambula / Gutkha","Multiple habits","Other (specify below)"]
SEVERITY_OPT=["Mridu (Mild)","Madhyama (Moderate)","Maha / Tivra (Severe)"]
DURATION_OPT=["Less than 1 month (Acute)","1 to 6 months","6 to 12 months",
               "1 to 2 years","2 to 5 years","5 to 10 years","More than 10 years (Chronic)"]
LIFESTYLE_RISK=["Musculo-Skeletal","Cardiovascular","Metabolic / Endocrine","Neurological",
                 "Respiratory","Gastrointestinal","Gynaecological / Obstetric","Paediatric",
                 "Dermatological","Renal / Urological","None identified"]
GENDER_OPT=["Male","Female","Other","Prefer not to say"]
OCCUPATION_OPT=["Business","Service / Government","Agriculture","Housewife","Student",
                 "Labour / Manual work","Professional","Retired","Other"]
DISTRICT_LIST=["Bangalore Urban","Bangalore Rural","Mysore","Tumkur","Kolar","Mandya",
                "Hassan","Shimoga","Davangere","Belagavi","Hubli-Dharwad","Bidar","Raichur",
                "Ballari","Chikkaballapur","Chikkamagaluru","Kodagu","Udupi",
                "Dakshina Kannada","Uttara Kannada","Koppal","Gadag","Vijayapura",
                "Bagalkot","Yadgir","Chamarajanagar","Ramanagara","Chitradurga",
                "Outside Karnataka","Other"]
BMI_CATS=[(0,18.5,"Underweight"),(18.5,23,"Normal (Asian)"),(23,25,"Overweight Gr.1"),
           (25,30,"Overweight Gr.2"),(30,999,"Obese")]
def bmi_cat(b):
    for lo,hi,l in BMI_CATS:
        if lo<=b<hi: return l
    return ""

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────
def section(t): st.markdown(f'<div class="sec">{t}</div>', unsafe_allow_html=True)
def dept_lbl(k): return DEPARTMENTS.get(k,k)
def get_phys(dk, onreq=False):
    if onreq: return sorted(PHYSICIANS.keys())
    return sorted([p for p,ds in PHYSICIANS.items() if dk in ds])
def xcode(s):
    if s and "[" in s: return s.split("[")[-1].rstrip("]").strip()
    return ""
def sel_other(label, opts, key, idx=0):
    v = st.selectbox(label, opts, index=idx, key=key)
    if v == "Other (specify below)":
        ov = st.text_input(f"Specify — {label}", key=f"{key}_oth", placeholder="Type here")
        return ov if ov else "Other"
    return v
def custom_sel(label, opts, key, idx=0, placeholder="Type here"):
    v = st.selectbox(label, opts, index=idx, key=key)
    if v == "— Custom —":
        cv = st.text_input(f"Custom {label}", key=f"{key}_c", placeholder=placeholder)
        return cv if cv else ""
    return v
def clean(v):
    if not isinstance(v,str): return v
    return re.sub(r'[^\x00-\x7F\u0900-\u097F\u0080-\u00FF]','',str(v)).strip()
def auto_pid():
    yr = str(date.today().year)[2:]
    return f"N{yr}{st.session_state.get('pid_counter',1):04d}"
def reset_form():
    """Clear physician tab fields for next patient."""
    keys_to_clear = [
        "TX_Purvakarma","TX_Pradhana Karma","TX_Pashchata Karma",
        "TX_comments_Purvakarma","TX_comments_Pradhana Karma","TX_comments_Pashchata Karma",
    ]
    for k in keys_to_clear:
        if k in st.session_state:
            st.session_state[k] = [] if isinstance(st.session_state[k], list) else {}
    st.session_state.med_count = 1
    st.session_state.rec = {}

# ─────────────────────────────────────────────────────────────────
# PDF ENGINE
# ─────────────────────────────────────────────────────────────────
GREEN   = colors.HexColor("#1a3a2a")
GOLD    = colors.HexColor("#c8a96e")
GREY    = colors.HexColor("#888888")
DGREY   = colors.HexColor("#444444")
BGROW1  = colors.HexColor("#f0f7f3")

def S():
    """Return style dict."""
    return {
        "hb":  ParagraphStyle("hb", fontName="Helvetica-Bold", fontSize=10,
                               alignment=TA_CENTER, textColor=GREEN, spaceAfter=1),
        "hm":  ParagraphStyle("hm", fontName="Helvetica", fontSize=7.5,
                               alignment=TA_CENTER, textColor=GREY, spaceAfter=1),
        "sec": ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=9,
                               textColor=GREEN, spaceBefore=5, spaceAfter=2),
        "n":   ParagraphStyle("n", fontName="Helvetica", fontSize=8.5,
                               spaceAfter=2, leading=12),
        "sm":  ParagraphStyle("sm", fontName="Helvetica", fontSize=7.5,
                               textColor=DGREY, leading=11),
        "bd":  ParagraphStyle("bd", fontName="Helvetica-Bold", fontSize=8.5, leading=12),
        "dx":  ParagraphStyle("dx", fontName="Helvetica-Bold", fontSize=14,
                               textColor=GREEN, spaceAfter=1, leading=17),
        "dxs": ParagraphStyle("dxs", fontName="Helvetica", fontSize=8.5,
                               textColor=DGREY, spaceAfter=4, leading=12),
        "sR":  ParagraphStyle("sR", fontName="Helvetica", fontSize=8, alignment=TA_RIGHT),
        "sL":  ParagraphStyle("sL", fontName="Helvetica", fontSize=8, alignment=TA_LEFT),
        "ft":  ParagraphStyle("ft", fontName="Helvetica", fontSize=6.5,
                               alignment=TA_CENTER, textColor=GREY),
        "ins": ParagraphStyle("ins", fontName="Helvetica", fontSize=8.5,
                               textColor=colors.HexColor("#1a237e"), leading=13, spaceAfter=2),
    }

def pdf_header(story, st_dict, W):
    story.append(Paragraph("JAI SRI GURUDEV", st_dict["hm"]))
    story.append(Paragraph(
        "Sri Kalabyraveshwara Swamy Ayurvedic Medical College, Hospital & Research Centre",
        ParagraphStyle("hb2",fontName="Helvetica-Bold",fontSize=9.5,
                       alignment=TA_CENTER,textColor=GREEN,spaceAfter=1)))
    story.append(Paragraph(
        "No.10, Pipeline Road, RPC Layout, Hampinagara, Vijayanagar 2nd Stage, Bangalore - 560104",
        st_dict["hm"]))
    story.append(Paragraph("Ph: 080-XXXXXXXX  |  Email: info@skamcshrc.edu.in  |  NABH Accredited",
                            st_dict["hm"]))
    story.append(HRFlowable(width=W,thickness=2,color=GREEN,spaceAfter=1))
    story.append(HRFlowable(width=W,thickness=0.8,color=GOLD,spaceAfter=4))

def pdf_pat_table(rec, st_dict, W):
    rows = [
        [Paragraph("<b>Patient ID</b>",st_dict["sm"]),Paragraph(str(rec.get("Patient_ID","")),st_dict["n"]),
         Paragraph("<b>Date</b>",st_dict["sm"]),Paragraph(datetime.now().strftime("%d %b %Y  %I:%M %p"),st_dict["n"])],
        [Paragraph("<b>Age / Gender</b>",st_dict["sm"]),
         Paragraph(f"{rec.get('Age','')} yrs / {rec.get('Gender','')}",st_dict["n"]),
         Paragraph("<b>Visit</b>",st_dict["sm"]),Paragraph(f"{rec.get('Visit_Type','')}  |  Visit #{rec.get('Visit_Count','1')}",st_dict["n"])],
        [Paragraph("<b>Department</b>",st_dict["sm"]),Paragraph(rec.get("Department",""),st_dict["n"]),
         Paragraph("<b>Prakriti</b>",st_dict["sm"]),Paragraph(rec.get("Prakriti",""),st_dict["n"])],
        [Paragraph("<b>Physician</b>",st_dict["sm"]),Paragraph(rec.get("Physician",""),st_dict["bd"]),
         Paragraph("<b>Triage</b>",st_dict["sm"]),Paragraph(rec.get("Triage",""),st_dict["n"])],
    ]
    t = Table(rows, colWidths=[28*mm,60*mm,28*mm,57*mm])
    t.setStyle(TableStyle([
        ("FONTSIZE",(0,0),(-1,-1),8.5),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[BGROW1,colors.white]),
        ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#cccccc")),
        ("TOPPADDING",(0,0),(-1,-1),2.5),("BOTTOMPADDING",(0,0),(-1,-1),2.5),
    ]))
    return t

def pdf_diagnosis(story, rec, st_dict, W):
    """Render diagnosis — CODE BIG, meaning small. No headers."""
    code = rec.get("Final_ACD_Code") or rec.get("ACD_Code_1","")
    mean = rec.get("Final_ACD_Meaning") or rec.get("ACD_Meaning_1","")
    if code:
        story.append(HRFlowable(width=W,thickness=0.5,color=colors.HexColor("#b7d9c5"),spaceAfter=3))
        story.append(Paragraph(code, st_dict["dx"]))
        story.append(Paragraph(mean, st_dict["dxs"]))

def pdf_medicines(story, rec, st_dict, W):
    """Render Shamana Aushadhi table."""
    meds = rec.get("Medicines",[])
    if not meds: return
    story.append(HRFlowable(width=W,thickness=0.5,color=colors.HexColor("#b7d9c5"),spaceAfter=2))
    story.append(Paragraph("Shamana Aushadhi", st_dict["sec"]))
    hdr = [[Paragraph(h,st_dict["bd"]) for h in
            ["#","Drug Name","Form","Dose","Route","Timing","Anupana","Duration","Notes"]]]
    rows=[]
    for i,m in enumerate(meds,1):
        rows.append([
            Paragraph(str(i),st_dict["sm"]),
            Paragraph(m.get("name",""),st_dict["n"]),
            Paragraph(m.get("form",""),st_dict["sm"]),
            Paragraph(m.get("dose",""),st_dict["sm"]),
            Paragraph(m.get("route","Oral"),st_dict["sm"]),
            Paragraph(m.get("timing",""),st_dict["sm"]),
            Paragraph(m.get("anupana",""),st_dict["sm"]),
            Paragraph(f"{m.get('dur_val','')} {m.get('dur_unit','')}",st_dict["sm"]),
            Paragraph(m.get("notes",""),st_dict["sm"]),
        ])
    mt = Table(hdr+rows, colWidths=[5*mm,35*mm,19*mm,12*mm,14*mm,19*mm,16*mm,13*mm,W-133*mm])
    mt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),GREEN),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTSIZE",(0,0),(-1,-1),7.5),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[BGROW1,colors.white]),
        ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#cccccc")),
        ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))
    story.append(mt)

def pdf_pk(story, rec, st_dict, W):
    """Render Panchakarma plan."""
    all_tx=[(c,rec.get(f"TX_{c}",[]),rec.get(f"TX_comments_{c}",{}))
            for c in ["Purvakarma","Pradhana Karma","Pashchata Karma"]]
    all_tx=[(c,s,cm) for c,s,cm in all_tx if s]
    if not all_tx and not rec.get("TX_Custom"): return
    story.append(HRFlowable(width=W,thickness=0.5,color=colors.HexColor("#b7d9c5"),spaceAfter=2))
    story.append(Paragraph("Panchakarma Treatment Plan", st_dict["sec"]))
    cat_bg={"Purvakarma":colors.HexColor("#e8f5e9"),
            "Pradhana Karma":colors.HexColor("#fff3e0"),
            "Pashchata Karma":colors.HexColor("#e3f2fd")}
    for cat,sel,cmt in all_tx:
        story.append(Paragraph(f"<b>{cat}</b>",st_dict["bd"]))
        rows=[[Paragraph(h,st_dict["bd"]) for h in ["Procedure","Code","Comments"]]]
        for tx in sel:
            code=xcode(tx)
            name=tx.split(" — ")[0] if " — " in tx else tx
            rows.append([
                Paragraph(name,st_dict["n"]),
                Paragraph(f"<b>{code}</b>",ParagraphStyle("pkc",fontName="Helvetica-Bold",
                                                           fontSize=8,textColor=GREEN)),
                Paragraph(cmt.get(code,""),st_dict["sm"]),
            ])
        tbl=Table(rows,colWidths=[55*mm,22*mm,W-77*mm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),GREEN),("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTSIZE",(0,0),(-1,-1),7.5),
            ("BACKGROUND",(0,1),(-1,-1),cat_bg.get(cat,BGROW1)),
            ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#cccccc")),
            ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
        ]))
        story.append(tbl)
        story.append(Spacer(1,1.5*mm))
    if rec.get("TX_Custom"):
        story.append(Paragraph(f"<b>Additional:</b>  {rec['TX_Custom']}",st_dict["sm"]))

def pdf_extras(story, rec, st_dict, W):
    """Lab tests, instructions, notes."""
    if rec.get("Lab_Tests"):
        story.append(HRFlowable(width=W,thickness=0.5,color=colors.HexColor("#b7d9c5"),spaceAfter=2))
        story.append(Paragraph("Investigations for Next Visit",st_dict["sec"]))
        story.append(Paragraph(rec["Lab_Tests"],st_dict["n"]))
    if rec.get("Instructions"):
        story.append(HRFlowable(width=W,thickness=0.5,color=colors.HexColor("#b7d9c5"),spaceAfter=2))
        story.append(Paragraph("Instructions / Pathya",st_dict["sec"]))
        for line in rec["Instructions"].split("\n"):
            if line.strip():
                story.append(Paragraph(f"  {line.strip()}",st_dict["ins"]))

def pdf_sig(story, st_dict, W, rec):
    story.append(Spacer(1,8*mm))
    story.append(HRFlowable(width=W,thickness=0.4,color=GREY,spaceAfter=3))
    sd=[
        [Paragraph("Reg. No.:  _______________________",st_dict["sL"]),
         Paragraph(f"<b>{rec.get('Physician','')}</b>",st_dict["sR"])],
        [Paragraph("Date: ________________",st_dict["sL"]),
         Paragraph("MD (Ayurveda)",st_dict["sR"])],
        [Paragraph("",st_dict["sL"]),
         Paragraph("Signature &amp; Stamp",st_dict["sR"])],
    ]
    st2=Table(sd,colWidths=[W/2,W/2])
    st2.setStyle(TableStyle([("FONTSIZE",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),2)]))
    story.append(st2)

def pdf_footer(story, st_dict, W):
    story.append(Spacer(1,4*mm))
    story.append(HRFlowable(width=W,thickness=0.8,color=GOLD,spaceAfter=1))
    story.append(HRFlowable(width=W,thickness=0.3,color=GREY,spaceAfter=2))
    story.append(Paragraph(
        "Conceptized by: Dr. Kiran M Goud, MD (Ay.)  |  "
        "Developed by: Dr. Prasanna Kulkarni, MD (Ay.), MS (Data Science)  |  "
        "ACD Codes: Namaste Portal  |  SAT-I Codes: WHO",
        st_dict["ft"]))

def make_pdf(rec, mode="both"):
    """
    mode: 'rx' = Prescription only (Diagnosis + Medicines)
          'pk' = PK Advice only (Diagnosis + PK plan)
          'both' = Full document (Diagnosis + Medicines + PK)
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             topMargin=12*mm, bottomMargin=18*mm,
                             leftMargin=18*mm, rightMargin=18*mm)
    W = A4[0]-36*mm
    styles = S()
    story = []

    pdf_header(story, styles, W)

    # Title
    title_map={"rx":"Prescription","pk":"Panchakarma Procedure Advice","both":"OPD Prescription"}
    story.append(Paragraph(title_map.get(mode,"Prescription"),
                            ParagraphStyle("tit",fontName="Helvetica-Bold",fontSize=13,
                                           alignment=TA_CENTER,textColor=GREEN,spaceAfter=2)))
    story.append(HRFlowable(width=W,thickness=0.8,color=GOLD,spaceAfter=4))

    # Patient table
    story.append(pdf_pat_table(rec, styles, W))
    story.append(Spacer(1,2*mm))

    # Vitals (compact single line)
    vit=(f"Ht: {rec.get('Height_cm','')} cm  |  Wt: {rec.get('Weight_kg','')} kg  |  "
         f"BMI: {rec.get('BMI','')} ({rec.get('BMI_Category','')})  |  "
         f"BP: {rec.get('BP','')}  |  Pulse: {rec.get('Pulse_bpm','')} bpm  |  "
         f"Temp: {rec.get('Temp_F','')} F  |  SpO2: {rec.get('SpO2_pct','')}%")
    story.append(Paragraph(vit, styles["sm"]))

    # Diagnosis — code prominent, no labels
    pdf_diagnosis(story, rec, styles, W)

    # Content based on mode
    if mode in ("rx", "both"):
        pdf_medicines(story, rec, styles, W)
    if mode in ("pk", "both"):
        pdf_pk(story, rec, styles, W)

    pdf_extras(story, rec, styles, W)
    pdf_sig(story, styles, W, rec)
    pdf_footer(story, styles, W)

    doc.build(story)
    buf.seek(0)
    return buf

# ─────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────
for k,v in [("records",[]),("rec",{}),("dept_key","KC"),
            ("pid_counter",1),("med_count",1),
            ("gs_cache",[]),("gs_cache_loaded",False)]:
    if k not in st.session_state: st.session_state[k]=v
for cat in ["Purvakarma","Pradhana Karma","Pashchata Karma"]:
    if f"TX_{cat}" not in st.session_state: st.session_state[f"TX_{cat}"]=[]
    if f"TX_comments_{cat}" not in st.session_state: st.session_state[f"TX_comments_{cat}"]={}

# ─────────────────────────────────────────────────────────────────
# GOOGLE SHEETS INIT (load existing data once per session)
# ─────────────────────────────────────────────────────────────────
sh, gs_error = get_sheet()
if sh and not st.session_state.gs_cache_loaded:
    sheet_init_headers(sh)
    existing = sheet_load_all(sh)
    if existing:
        st.session_state.gs_cache = existing
        st.session_state.records  = existing
    st.session_state.gs_cache_loaded = True

GS_AVAILABLE = sh is not None

# ─────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-hdr">
  <h2>SKAMCSHRC — OPD Clinical Data Entry System</h2>
  <p>Sri Kalabyraveshwara Swamy Ayurvedic Medical College, Hospital &amp; Research Centre, Bangalore</p>
</div>
""", unsafe_allow_html=True)

if not ACD_LOADED:
    st.warning("newACD.xlsx not found — place it in the app folder and restart.")
if not GS_AVAILABLE:
    if gs_error:
        st.error(f"Google Sheets error: {gs_error}")
    else:
        st.info("Google Sheets not configured — data saves to session only.")

m1,m2,m3,m4 = st.columns(4)
m1.metric("Date", date.today().strftime("%d %b %Y"))
m2.metric("Time", datetime.now().strftime("%I:%M %p"))
today_n = len([r for r in st.session_state.records
               if str(r.get("Visit_Date","")).startswith(str(date.today()))])
m3.metric("Today's Records", today_n)
m4.metric("Total Records", len(st.session_state.records))
st.markdown("---")

tab1, tab2 = st.tabs([
    "Tab 1  —  Reception & Screening",
    "Tab 2  —  Physician Consultation",
])

# ═══════════════════════════════════════════════════════════════
#  TAB 1 — RECEPTION
# ═══════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Reception & Screening")

    # TRIAGE
    st.markdown('<div class="card">', unsafe_allow_html=True)
    section("1  TRIAGE")
    triage=st.radio("Triage Level",["Routine","Urgent"],index=0,horizontal=True,key="triage_r")
    if triage=="Urgent":
        st.markdown('<div class="triage-u">URGENT — Attend promptly</div>',unsafe_allow_html=True)
    else:
        st.markdown('<div class="triage-r">ROUTINE — Regular OPD queue</div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

    # DEMOGRAPHICS — with auto-fill for returning patients
    st.markdown('<div class="card">', unsafe_allow_html=True)
    section("2  PATIENT DEMOGRAPHICS")

    # Patient ID input — triggers auto-fill
    pid_input = st.text_input("Patient ID (type existing ID to auto-fill)",
                               value=auto_pid(), key="pid",
                               placeholder="e.g. N260001 — type existing ID to load patient")

    # Auto-fill if returning patient
    returning_data = None
    if pid_input:
        existing_visits = find_patient(st.session_state.records, pid_input)
        if existing_visits:
            last = existing_visits[-1]
            returning_data = last
            visit_count = len(existing_visits) + 1
            st.markdown(
                f'<div class="returning-banner">'
                f'<h4>Returning Patient — Visit #{visit_count}</h4>'
                f'<b>Last visit:</b> {last.get("Visit_Date","")}  |  '
                f'<b>Dept:</b> {last.get("Department","")}  |  '
                f'<b>Diagnosis:</b> <span style="font-family:monospace;font-weight:700">'
                f'{last.get("Final_ACD_Code") or last.get("ACD_Code_1","")}</span>  '
                f'{last.get("Final_ACD_Meaning") or last.get("ACD_Meaning_1","")}'
                f'</div>',
                unsafe_allow_html=True)
        else:
            visit_count = 1

    def prefill(field, default):
        """Return value from returning patient or default."""
        if returning_data and returning_data.get(field):
            return returning_data[field]
        return default

    c1,c2,c3 = st.columns(3)
    with c1:
        vdate = st.date_input("Visit Date", value=date.today(), key="vdate")
    with c2:
        age_def = int(prefill("Age",30))
        age    = st.number_input("Age (years)",0,120,age_def,key="age")
        gender_def = prefill("Gender",GENDER_OPT[0])
        gender_idx = GENDER_OPT.index(gender_def) if gender_def in GENDER_OPT else 0
        gender = st.selectbox("Gender",GENDER_OPT,index=gender_idx,key="gender")
    with c3:
        vtype    = st.selectbox("Visit Type",["New Case","Follow Up"],
                                 index=0 if not returning_data else 1, key="vtype")
        dist_def = prefill("District",DISTRICT_LIST[0])
        dist_idx = DISTRICT_LIST.index(dist_def) if dist_def in DISTRICT_LIST else 0
        district = st.selectbox("District",DISTRICT_LIST,index=dist_idx,key="district")

    c4,c5,c6 = st.columns(3)
    with c4:
        occ_def = prefill("Occupation",OCCUPATION_OPT[0])
        occ_idx = OCCUPATION_OPT.index(occ_def) if occ_def in OCCUPATION_OPT else 0
        occ = st.selectbox("Occupation",OCCUPATION_OPT,index=occ_idx,key="occ")
    with c5:
        prak_def = prefill("Prakriti",PRAKRITI_OPT[0])
        prak_idx = PRAKRITI_OPT.index(prak_def) if prak_def in PRAKRITI_OPT else 0
        prakriti = st.selectbox("Prakriti",PRAKRITI_OPT,index=prak_idx,key="prakriti")
    with c6:
        lrisk = st.multiselect("Lifestyle Risk",LIFESTYLE_RISK,key="lrisk")
    st.markdown('</div>',unsafe_allow_html=True)

    # DEPARTMENT & PHYSICIAN
    st.markdown('<div class="card">', unsafe_allow_html=True)
    section("3  DEPARTMENT & PHYSICIAN")
    dc1,dc2 = st.columns(2)
    with dc1:
        dept_def = prefill("Department","")
        dept_keys = list(DEPARTMENTS.keys())
        # Find dept key from label if returning
        if dept_def:
            dept_key_def = next((k for k,v in DEPARTMENTS.items() if v==dept_def),
                                 st.session_state.dept_key)
        else:
            dept_key_def = st.session_state.dept_key
        dept_key = st.selectbox("Department",dept_keys,
                                 format_func=dept_lbl,
                                 index=dept_keys.index(dept_key_def) if dept_key_def in dept_keys else 0,
                                 key="dept_sel")
        st.session_state.dept_key = dept_key
    with dc2:
        on_req = st.checkbox("On Request (all physicians)",key="on_req")
    phys_list = get_phys(dept_key,on_req)
    phys_def  = prefill("Physician",phys_list[0] if phys_list else "")
    phys_idx  = phys_list.index(phys_def) if phys_def in phys_list else 0
    physician = st.selectbox("Physician",phys_list,index=phys_idx,key="phys_sel")
    if physician in PHYSICIANS:
        st.caption(f"{physician} — {' | '.join([dept_lbl(d) for d in PHYSICIANS[physician]])}")
    consult_type="On Request" if on_req else "Regular"
    st.markdown('</div>',unsafe_allow_html=True)

    # CHIEF COMPLAINTS & PROVISIONAL DIAGNOSIS
    st.markdown('<div class="card">', unsafe_allow_html=True)
    section("4  CHIEF COMPLAINTS & PROVISIONAL DIAGNOSIS")
    chief    = st.multiselect("Chief Complaints",DEPT_CONDITIONS.get(dept_key,[]),key="chief")
    other_cc = st.text_input("Additional Chief Complaint",key="other_cc")
    st.markdown("**Provisional Diagnosis 1**")
    prov_lbl1, prov_code1, prov_mean1 = acd_search_widget("prov_srch1","prov_sel1","Search Diagnosis 1")
    st.markdown("**Provisional Diagnosis 2** (optional)")
    prov_lbl2, prov_code2, prov_mean2 = acd_search_widget("prov_srch2","prov_sel2","Search Diagnosis 2")
    sc1,sc2 = st.columns(2)
    with sc1: severity = st.selectbox("Severity",SEVERITY_OPT,key="severity")
    with sc2: duration = st.selectbox("Disease Duration",DURATION_OPT,key="duration")
    st.markdown('</div>',unsafe_allow_html=True)

    # SAVE
    st.markdown('<div class="card">', unsafe_allow_html=True)
    section("5  SAVE RECEPTION RECORD")
    if st.button("Save Reception Record", type="primary", key="save_rec"):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        vc = visit_count if returning_data else 1
        rec = {
            "Patient_ID":pid_input,"Visit_Date":str(vdate),
            "Visit_Time":datetime.now().strftime("%H:%M:%S"),
            "Visit_DateTime":ts,"Visit_Year":vdate.year,"Visit_Type":vtype,
            "Consultation_Type":consult_type,"Visit_Count":vc,
            "Age":age,"Gender":gender,"District":district,"Occupation":occ,
            "Prakriti":prakriti,"Lifestyle_Risk":", ".join(lrisk) if lrisk else "",
            "Triage":triage,"Department":dept_lbl(dept_key),"Physician":physician,
            "Chief_Complaints":", ".join(chief)+(f"; {other_cc}" if other_cc else ""),
            "Chief_Complaints_Modified":"",
            "ACD_Code_1":prov_code1,"ACD_Meaning_1":prov_mean1,
            "ACD_Code_2":prov_code2,"ACD_Meaning_2":prov_mean2,
            "Severity":severity,"Disease_Duration":duration,
            "Height_cm":"","Weight_kg":"","BMI":"","BMI_Category":"",
            "BP":"","Pulse_bpm":"","Temp_F":"","SpO2_pct":"","RR_per_min":"",
            "Other_Investigation":"","Nadi":"","Jihva":"","Agni":"","Mala":"",
            "Mutra":"","Sleep":"","Shabda":"","Sparsha":"","Drik":"","Akriti":"",
            "Dosha":"","Dushya":"","Bala":"","Kala":"","Satva":"","Satmya":"",
            "Vyasana":"","Prakriti_Confirmed":"",
            "Final_ACD_Code":"","Final_ACD_Meaning":"",
            "TX_Purvakarma":"","TX_Pradhana_Karma":"","TX_Pashchata_Karma":"",
            "TX_Comments_Purvakarma":"","TX_Comments_Pradhana":"","TX_Comments_Pashchata":"",
            "TX_Custom":"","Medicines_Summary":"","Lab_Tests":"",
            "Instructions":"","Physician_Notes":"","Followup_Notes":"",
        }
        st.session_state.rec = rec
        st.session_state.records.append(rec)
        if sh: sheet_save_record(sh, rec)
        # Auto-increment PID for next patient
        if not returning_data:
            st.session_state.pid_counter += 1
        # Reset treatment/medicine fields for fresh start
        reset_form()
        st.success(f"Saved — {pid_input} (Visit #{vc}). Proceed to Tab 2 for physician consultation.")
    st.markdown('</div>',unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  TAB 2 — PHYSICIAN CONSULTATION
# ═══════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Physician Consultation")
    rec = st.session_state.rec

    if not rec:
        st.info("No active patient. Complete Tab 1 first, or enter Patient ID below.")
        lid = st.text_input("Load Patient by ID",key="load_id")
        if lid:
            found = sorted([r for r in st.session_state.records if r.get("Patient_ID")==lid],
                           key=lambda x: x.get("Visit_DateTime",""))
            if found:
                st.session_state.rec = found[-1]; st.rerun()
            else:
                st.warning(f"Not found: {lid}")
    else:
        # ── FOLLOW-UP NOTES FROM PREVIOUS VISIT ─────────────────
        same_pid_prev = sorted(
            [r for r in st.session_state.records
             if r.get("Patient_ID")==rec.get("Patient_ID")
             and r.get("Visit_DateTime") != rec.get("Visit_DateTime")
             and str(r.get("Followup_Notes","")).strip()],
            key=lambda x: x.get("Visit_DateTime",""))
        if same_pid_prev:
            last = same_pid_prev[-1]
            st.markdown(
                f'<div class="followup-box">'
                f'<h4>Follow-up Notes from Visit on {last.get("Visit_Date","")} '
                f'(Dx: {last.get("Final_ACD_Code") or last.get("ACD_Code_1","")})</h4>'
                f'<p>{str(last.get("Followup_Notes","")).replace(chr(10),"<br>")}</p>'
                f'</div>', unsafe_allow_html=True)

        # ── PATIENT BANNER ───────────────────────────────────────
        with st.expander("Patient Summary (from Reception)", expanded=True):
            b1,b2,b3,b4,b5 = st.columns(5)
            b1.metric("Patient ID",  rec.get("Patient_ID",""))
            b2.metric("Age/Gender",  f"{rec.get('Age','')} / {rec.get('Gender','')}")
            b3.metric("Department",  rec.get("Department",""))
            b4.metric("Physician",   rec.get("Physician",""))
            b5.metric("Triage",      rec.get("Triage",""))
            st.write(f"**Chief Complaints:** {rec.get('Chief_Complaints','—')}")
            if rec.get("ACD_Code_1"):
                st.markdown(f'**Provisional:** <span class="code-big">{rec["ACD_Code_1"]}</span>  {rec.get("ACD_Meaning_1","")}',
                            unsafe_allow_html=True)

        # ── MODIFY COMPLAINTS & DIAGNOSIS ───────────────────────
        with st.expander("Modify Chief Complaints & Diagnosis (Physician Override)", expanded=False):
            mod_cc = st.text_area("Modified Chief Complaints",
                                   value=rec.get("Chief_Complaints",""),
                                   key="mod_cc", height=55)
            st.markdown("**Modified / Corrected Provisional Diagnosis**")
            _, mod_code1, mod_mean1 = acd_search_widget("mod_srch","mod_sel","Search Corrected Diagnosis")
            if not mod_code1:
                mod_code1 = rec.get("ACD_Code_1","")
                mod_mean1 = rec.get("ACD_Meaning_1","")

        # ── VITALS ───────────────────────────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        section("1  VITALS & ANTHROPOMETRY")
        v1,v2,v3 = st.columns(3)
        with v1:
            height=st.number_input("Height (cm)",50.0,250.0,160.0,step=1.0,key="height")
            weight=st.number_input("Weight (kg)",1.0,300.0,50.0,step=0.5,key="weight")
            bmi_v=weight/((height/100)**2) if height>0 else 0
            bmi_c=bmi_cat(bmi_v)
            st.markdown(f'<div class="bmi-box">BMI: {bmi_v:.1f} — {bmi_c}</div>',unsafe_allow_html=True)
        with v2:
            bp_s=st.number_input("BP Systolic",60,250,120,step=1,key="bps")
            bp_d=st.number_input("BP Diastolic",40,160,80,step=1,key="bpd")
        with v3:
            pulse=st.number_input("Pulse (bpm)",30,220,76,step=1,key="pulse")
            temp =st.number_input("Temperature (F)",90.0,108.0,98.6,step=0.1,key="temp")
        vv4,vv5=st.columns(2)
        with vv4: spo2=st.number_input("SpO2 (%)",50,100,98,step=1,key="spo2")
        with vv5: rr  =st.number_input("Resp. Rate (/min)",5,60,16,step=1,key="rr")
        other_inv=st.text_area("Other Investigations / Lab Reports",key="other_inv",height=50,
                                placeholder="e.g. Hb 11.2; FBS 126; X-ray: Disc prolapse L4-L5")
        st.markdown('</div>',unsafe_allow_html=True)

        # ── ASHTAVIDHA PARIKSHA ──────────────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        section("2  ASHTAVIDHA PARIKSHA")
        a1,a2,a3,a4=st.columns(4)
        with a1:
            nadi   =sel_other("Nadi (Pulse)",   NADI_OPT,   "nadi")
            jihva  =sel_other("Jihva (Tongue)",  JIHVA_OPT,  "jihva")
        with a2:
            agni   =sel_other("Agni",            AGNI_OPT,   "agni")
            mala   =sel_other("Mala (Stool)",    MALA_OPT,   "mala")
        with a3:
            mutra  =sel_other("Mutra (Urine)",   MUTRA_OPT,  "mutra")
            sleep  =sel_other("Nidra (Sleep)",   SLEEP_OPT,  "sleep")
        with a4:
            shabda =sel_other("Shabda",          SHABDA_OPT, "shabda")
            sparsha=sel_other("Sparsha",         SPARSHA_OPT,"sparsha")
        aa5,aa6=st.columns(2)
        with aa5: drik  =sel_other("Drik (Vision)",  DRIK_OPT,  "drik")
        with aa6: akriti=sel_other("Akriti (Appear)",AKRITI_OPT,"akriti")
        st.markdown('</div>',unsafe_allow_html=True)

        # ── DASHAVIDHA PARIKSHA ──────────────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        section("3  DASHAVIDHA ATURA PARIKSHA")
        d1,d2,d3=st.columns(3)
        with d1:
            dosha =sel_other("Dosha (Dominant)", DOSHA_OPT, "dosha")
            dushya=st.multiselect("Dushya (Dhatu/Mala)",DUSHYA_OPT,key="dushya")
            bala  =sel_other("Bala (Strength)",  BALA_OPT,  "bala")
        with d2:
            kala  =st.selectbox("Kala (Season)", KALA_OPT,  key="kala")
            satva =sel_other("Satva",            SATVA_OPT, "satva")
            satmya=sel_other("Satmya",           SATMYA_OPT,"satmya")
        with d3:
            vyasana=sel_other("Vyasana (Habits)",VYASANA_OPT,"vyasana")
            cprak  =st.selectbox("Prakriti (confirm)",PRAKRITI_OPT,
                                  index=PRAKRITI_OPT.index(rec.get("Prakriti",PRAKRITI_OPT[0]))
                                        if rec.get("Prakriti") in PRAKRITI_OPT else 0,
                                  key="cprak")
        st.markdown('</div>',unsafe_allow_html=True)

        # ── FINAL DIAGNOSIS (live search) ────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        section("4  FINAL DIAGNOSIS")
        if mod_code1:
            st.markdown(f"Provisional: <span class='code-big'>{mod_code1}</span> — {mod_mean1}",
                        unsafe_allow_html=True)
        elif rec.get("ACD_Code_1"):
            st.markdown(f"Provisional: <span class='code-big'>{rec['ACD_Code_1']}</span> — {rec.get('ACD_Meaning_1','')}",
                        unsafe_allow_html=True)

        fd_lbl, fd_code, fd_mean = acd_search_widget("fd_srch","fd_sel","Search Final Diagnosis")
        use_prov=st.checkbox("Same as Provisional",key="use_prov")
        if use_prov:
            fd_code = mod_code1 or rec.get("ACD_Code_1","")
            fd_mean = mod_mean1 or rec.get("ACD_Meaning_1","")
            if fd_code:
                st.markdown(f'<span class="code-big">{fd_code}</span>  {fd_mean}',
                            unsafe_allow_html=True)
        st.markdown('</div>',unsafe_allow_html=True)

        # ── PANCHAKARMA TREATMENT PLAN ───────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        section("5  PANCHAKARMA TREATMENT PLAN (SAT-I Codes)")

        # Running summary
        summary_parts=[]
        for cat in ["Purvakarma","Pradhana Karma","Pashchata Karma"]:
            s=st.session_state.get(f"TX_{cat}",[])
            if s:
                names=", ".join([x.split(" — ")[0] for x in s])
                summary_parts.append(f"<b>{cat}:</b> {names}")
        if summary_parts:
            st.markdown('<div class="tx-summary">'+"<br>".join(summary_parts)+"</div>",
                        unsafe_allow_html=True)

        tx_tabs=st.tabs(["Purvakarma","Pradhana Karma","Pashchata Karma"])
        for cat,ttab in zip(["Purvakarma","Pradhana Karma","Pashchata Karma"],tx_tabs):
            with ttab:
                opts=[f"{nm} — {desc} [{cd}]" for cd,nm,desc in PK_TREATMENTS[cat]]
                cur=[c for c in st.session_state.get(f"TX_{cat}",[]) if c in opts]
                chosen=st.multiselect(f"Select {cat} procedures",
                                       options=opts,default=cur,key=f"TX_ms_{cat}")
                st.session_state[f"TX_{cat}"]=chosen
                if chosen:
                    st.markdown("**Procedure-wise Comments / Details:**")
                    ex_cmts=st.session_state.get(f"TX_comments_{cat}",{})
                    new_cmts={}
                    for tx in chosen:
                        code=xcode(tx); name=tx.split(" — ")[0] if " — " in tx else tx
                        prev=ex_cmts.get(code,"")
                        st.markdown('<div class="proc-cmt">',unsafe_allow_html=True)
                        cmt=st.text_input(f"{name}  [{code}]",value=prev,
                                           key=f"cmt_{cat}_{code}",
                                           placeholder="e.g. with Dhanwantaram taila 45 min | Trivrit lehya 60g at 7am")
                        st.markdown('</div>',unsafe_allow_html=True)
                        new_cmts[code]=cmt
                    st.session_state[f"TX_comments_{cat}"]=new_cmts
                    st.markdown("  ".join([f'<span class="badge">{xcode(t)}</span>' for t in chosen]),
                                unsafe_allow_html=True)

        tx_custom=st.text_input("Additional / Yoga / Pathya / Custom",key="tx_custom",
                                 placeholder="e.g. Pathya Ahara, Yoga Nidra")
        st.markdown('</div>',unsafe_allow_html=True)

        # ── SHAMANA AUSHADHI ─────────────────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        section("6  SHAMANA AUSHADHI (Internal Medications)")
        ac,rc,_=st.columns([1,1,5])
        with ac:
            if st.button("+ Add Medicine",key="add_med"):
                st.session_state.med_count+=1; st.rerun()
        with rc:
            if st.session_state.med_count>1 and st.button("- Remove Last",key="rem_med"):
                st.session_state.med_count-=1; st.rerun()

        medicines=[]
        for i in range(1,st.session_state.med_count+1):
            st.markdown(f'<div class="med-row"><div class="med-num">Medicine {i}</div>',
                        unsafe_allow_html=True)
            r1a,r1b,r1c=st.columns([3,2,2])
            with r1a:
                mname=st.text_input(f"Drug Name {i}",key=f"mn_{i}",
                                     placeholder="e.g. Triphala Churna, Ashwagandha Vati")
            with r1b:
                mform=custom_sel(f"Dosage Form {i}",DOSAGE_FORMS,f"mf_{i}",
                                  placeholder="Type dosage form")
            with r1c:
                # Route — default Oral (index 0)
                mroute=custom_sel(f"Route {i}",ROUTE_OPTIONS,f"mr_{i}",idx=0,
                                   placeholder="Type route")

            r2a,r2b,r2c,r2d,r2e=st.columns([2,2,2,1,1])
            with r2a:
                mdose=custom_sel(f"Dose {i}",DOSE_OPTIONS,f"md_{i}",
                                  placeholder="e.g. 5g BD, 15ml TID")
            with r2b:
                mtiming=st.selectbox(f"Timing {i}",TIMING_OPTIONS,key=f"mt_{i}")
            with r2c:
                manupana=custom_sel(f"Anupana {i}",ANUPANA_OPTIONS,f"ma_{i}",idx=0,
                                     placeholder="Specify anupana")
            with r2d:
                mdur_val=st.number_input(f"Duration {i}",min_value=1,max_value=999,
                                          value=15,step=1,key=f"mdv_{i}")
            with r2e:
                mdur_unit=st.selectbox(f"Unit {i}",DURATION_UNIT,index=0,key=f"mdu_{i}")

            mnotes=st.text_input(f"Additional notes {i} (optional)",key=f"mno_{i}",
                                  placeholder="e.g. avoid in pregnancy, take warm")
            st.markdown('</div>',unsafe_allow_html=True)
            if mname.strip():
                medicines.append({"name":mname,"form":mform,"route":mroute,"dose":mdose,
                                   "timing":mtiming,"anupana":manupana,
                                   "dur_val":mdur_val,"dur_unit":mdur_unit,"notes":mnotes})
        st.markdown('</div>',unsafe_allow_html=True)

        # ── LAB TESTS ────────────────────────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        section("7  LAB TESTS FOR NEXT VISIT")
        lab_tests=st.text_area("Investigations required before next visit",key="lab_tests",height=50,
                                placeholder="e.g. CBC, FBS, HbA1c, Lipid profile, X-ray LS spine")
        st.markdown('</div>',unsafe_allow_html=True)

        # ── INSTRUCTIONS ─────────────────────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        section("8  INSTRUCTIONS / PATHYA")
        instructions=st.text_area("Patient Instructions (optional)",key="instructions",height=75,
                                   placeholder="e.g. Avoid cold food\nDrink warm water\nFollow-up after 15 days")
        st.markdown('</div>',unsafe_allow_html=True)

        # ── PHYSICIAN NOTES ──────────────────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        section("9  PHYSICIAN NOTES (for Records)")
        phys_notes=st.text_area("Clinical observations / referrals",key="phys_notes",height=50,
                                 placeholder="Special instructions, referrals, clinical observations...")
        st.markdown('</div>',unsafe_allow_html=True)

        # ── FOLLOW-UP NOTES ──────────────────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        section("10  FOLLOW-UP NOTES (Shown at Next Visit)")
        followup_notes=st.text_area("Notes for review at next visit",key="followup_notes",height=65,
                                     placeholder="e.g. Monitor BP\nCheck HbA1c improvement\nReview Sneha Pana response before Virechana")
        st.markdown('</div>',unsafe_allow_html=True)

        # ── SAVE & PDF GENERATION ────────────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        section("11  SAVE & GENERATE PRESCRIPTIONS")

        def build_full_rec():
            """Assemble complete record for PDF or saving."""
            tx_pur=st.session_state.get("TX_Purvakarma",[])
            tx_pra=st.session_state.get("TX_Pradhana Karma",[])
            tx_pas=st.session_state.get("TX_Pashchata Karma",[])
            cmt_pur=st.session_state.get("TX_comments_Purvakarma",{})
            cmt_pra=st.session_state.get("TX_comments_Pradhana Karma",{})
            cmt_pas=st.session_state.get("TX_comments_Pashchata Karma",{})
            r=dict(rec)
            r["TX_Purvakarma"]=tx_pur
            r["TX_Pradhana Karma"]=tx_pra
            r["TX_Pashchata Karma"]=tx_pas
            r["TX_comments_Purvakarma"]=cmt_pur
            r["TX_comments_Pradhana Karma"]=cmt_pra
            r["TX_comments_Pashchata Karma"]=cmt_pas
            r["TX_Custom"]=st.session_state.get("tx_custom","")
            r["Medicines"]=medicines
            r["Lab_Tests"]=st.session_state.get("lab_tests","")
            r["Instructions"]=st.session_state.get("instructions","")
            r["Physician_Notes"]=st.session_state.get("phys_notes","")
            r["Followup_Notes"]=st.session_state.get("followup_notes","")
            r["Height_cm"]=st.session_state.get("height",0)
            r["Weight_kg"]=st.session_state.get("weight",0)
            r["BMI"]=round(bmi_v,1); r["BMI_Category"]=bmi_c
            r["BP"]=f"{st.session_state.get('bps',120)}/{st.session_state.get('bpd',80)}"
            r["Pulse_bpm"]=st.session_state.get("pulse",76)
            r["Temp_F"]=st.session_state.get("temp",98.6)
            r["SpO2_pct"]=st.session_state.get("spo2",98)
            r["Chief_Complaints_Modified"]=st.session_state.get("mod_cc","")
            r["ACD_Code_1"]=mod_code1 or rec.get("ACD_Code_1","")
            r["ACD_Meaning_1"]=mod_mean1 or rec.get("ACD_Meaning_1","")
            if use_prov:
                r["Final_ACD_Code"]=r["ACD_Code_1"]; r["Final_ACD_Meaning"]=r["ACD_Meaning_1"]
            elif fd_code:
                r["Final_ACD_Code"]=fd_code; r["Final_ACD_Meaning"]=fd_mean
            return r

        def cmt_flat(sel,cmt):
            return "; ".join([f"{xcode(t)}: {cmt.get(xcode(t),'')}"
                              for t in sel if cmt.get(xcode(t))])

        # Row 1: Save + 3 PDF buttons
        s_col, rx_col, pk_col, both_col = st.columns(4)

        with s_col:
            if st.button("Save Consultation", type="primary", key="save_phys"):
                r=build_full_rec()
                tx_pur=st.session_state.get("TX_Purvakarma",[])
                tx_pra=st.session_state.get("TX_Pradhana Karma",[])
                tx_pas=st.session_state.get("TX_Pashchata Karma",[])
                cmt_pur=st.session_state.get("TX_comments_Purvakarma",{})
                cmt_pra=st.session_state.get("TX_comments_Pradhana Karma",{})
                cmt_pas=st.session_state.get("TX_comments_Pashchata Karma",{})
                med_sum="; ".join([
                    f"{m['name']} {m['form']} {m['route']} {m['dose']} {m['timing']} "
                    f"x{m['dur_val']} {m['dur_unit']} Anupana:{m['anupana']}"
                    for m in medicines])
                update={
                    "Height_cm":r["Height_cm"],"Weight_kg":r["Weight_kg"],
                    "BMI":r["BMI"],"BMI_Category":r["BMI_Category"],
                    "BP":r["BP"],"Pulse_bpm":r["Pulse_bpm"],
                    "Temp_F":r["Temp_F"],"SpO2_pct":r["SpO2_pct"],
                    "RR_per_min":st.session_state.get("rr",16),
                    "Other_Investigation":st.session_state.get("other_inv",""),
                    "Nadi":nadi,"Jihva":jihva,"Agni":agni,"Mala":mala,
                    "Mutra":mutra,"Sleep":sleep,"Shabda":shabda,"Sparsha":sparsha,
                    "Drik":drik,"Akriti":akriti,"Dosha":dosha,
                    "Dushya":", ".join(dushya) if dushya else "",
                    "Bala":bala,"Kala":kala,"Satva":satva,"Satmya":satmya,
                    "Vyasana":vyasana,"Prakriti_Confirmed":cprak,
                    "Chief_Complaints_Modified":st.session_state.get("mod_cc",""),
                    "ACD_Code_1":r["ACD_Code_1"],"ACD_Meaning_1":r["ACD_Meaning_1"],
                    "Final_ACD_Code":r.get("Final_ACD_Code",""),
                    "Final_ACD_Meaning":r.get("Final_ACD_Meaning",""),
                    "TX_Purvakarma":    "; ".join([s.split(" — ")[0] for s in tx_pur]),
                    "TX_Pradhana_Karma":"; ".join([s.split(" — ")[0] for s in tx_pra]),
                    "TX_Pashchata_Karma":"; ".join([s.split(" — ")[0] for s in tx_pas]),
                    "TX_Comments_Purvakarma":cmt_flat(tx_pur,cmt_pur),
                    "TX_Comments_Pradhana":  cmt_flat(tx_pra,cmt_pra),
                    "TX_Comments_Pashchata": cmt_flat(tx_pas,cmt_pas),
                    "TX_Custom":st.session_state.get("tx_custom",""),
                    "Medicines_Summary":med_sum,
                    "Lab_Tests":st.session_state.get("lab_tests",""),
                    "Instructions":st.session_state.get("instructions",""),
                    "Physician_Notes":st.session_state.get("phys_notes",""),
                    "Followup_Notes":st.session_state.get("followup_notes",""),
                }
                rec.update(update)
                for idx,r2 in enumerate(st.session_state.records):
                    if (r2.get("Patient_ID")==rec.get("Patient_ID") and
                        r2.get("Visit_DateTime")==rec.get("Visit_DateTime")):
                        st.session_state.records[idx]=rec; break
                if sh: sheet_save_record(sh, rec)
                st.success(f"Saved — {rec.get('Patient_ID')} | Final: {update.get('Final_ACD_Code','(not set)')}")
                # ── Auto-reset for next patient ──
                reset_form()
                st.session_state.pid_counter+=1
                st.rerun()

        with rx_col:
            r_rx=build_full_rec()
            pdf_rx=make_pdf(r_rx, mode="rx")
            st.download_button("Prescription Only",data=pdf_rx,
                                file_name=f"Rx_{rec.get('Patient_ID','PT')}_{date.today()}.pdf",
                                mime="application/pdf",key="dl_rx")

        with pk_col:
            has_pk=any(st.session_state.get(f"TX_{c}",[])
                       for c in ["Purvakarma","Pradhana Karma","Pashchata Karma"])
            if has_pk:
                r_pk=build_full_rec()
                pdf_pk_buf=make_pdf(r_pk, mode="pk")
                st.download_button("PK Advice Only",data=pdf_pk_buf,
                                    file_name=f"PK_{rec.get('Patient_ID','PT')}_{date.today()}.pdf",
                                    mime="application/pdf",key="dl_pk")
            else:
                st.caption("Select PK procedures to enable.")

        with both_col:
            r_both=build_full_rec()
            pdf_both=make_pdf(r_both, mode="both")
            st.download_button("Full Document",data=pdf_both,
                                file_name=f"Full_{rec.get('Patient_ID','PT')}_{date.today()}.pdf",
                                mime="application/pdf",key="dl_both")

        st.markdown('</div>',unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# SIDEBAR — RECORDS, EXPORT, SEARCH
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### SKAMCSHRC OPD v7.0")
    st.markdown(
        "**Conceptized by:** Dr. Kiran M Goud, MD (Ay.)  \n"
        "**Developed by:** Dr. Prasanna Kulkarni, MD (Ay.), MS (Data Science)  \n"
        "ACD: Namaste Portal | SAT-I: WHO"
    )
    if GS_AVAILABLE:
        st.success("Google Sheets connected")
    else:
        if gs_error:
            st.error(f"GS Error: {gs_error[:120]}")
        else:
            st.warning("Google Sheets not configured")
    st.markdown("---")

    # Patient search
    st.markdown("### Search Patient")
    search_pid = st.text_input("Search by Patient ID", key="search_pid_sb")
    if search_pid:
        found = find_patient(st.session_state.records, search_pid)
        if found:
            st.success(f"Found {len(found)} visit(s)")
            for v in found[-3:]:  # Show last 3 visits
                st.markdown(
                    f"**{v.get('Visit_Date','')}** — "
                    f"`{v.get('Final_ACD_Code') or v.get('ACD_Code_1','')}`  "
                    f"{v.get('Department','')}")
        else:
            st.info("No records found.")

    st.markdown("---")
    st.markdown("### Records & Export")
    st.write(f"**Total: {len(st.session_state.records)} records**")
    if st.session_state.records:
        disp_cols=["Patient_ID","Visit_Date","Visit_Time","Department","Physician",
                   "ACD_Code_1","Final_ACD_Code"]
        disp_cols=[c for c in disp_cols if c in (st.session_state.records[0] or {})]
        df_d=pd.DataFrame(st.session_state.records)[disp_cols]
        st.dataframe(df_d,use_container_width=True,height=160)

        skip={"TX_Purvakarma","TX_Pradhana Karma","TX_Pashchata Karma",
              "TX_comments_Purvakarma","TX_comments_Pradhana Karma","TX_comments_Pashchata Karma",
              "Medicines"}
        ecols=[c for c in SHEET_COLS if c not in skip]
        df_exp=pd.DataFrame([{k:clean(str(r.get(k,""))) for k in ecols}
                              for r in st.session_state.records])
        buf=io.BytesIO()
        with pd.ExcelWriter(buf,engine="openpyxl") as w:
            df_exp.to_excel(w,index=False,sheet_name="OPD_Records")
        buf.seek(0)
        st.download_button("Download Excel",data=buf,
                            file_name=f"SKAMCSHRC_OPD_{date.today()}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        csv_d=df_exp.to_csv(index=False).encode("utf-8-sig")
        st.download_button("Download CSV",data=csv_d,
                            file_name=f"SKAMCSHRC_OPD_{date.today()}.csv",mime="text/csv")
        if st.button("Clear Session Cache"):
            st.session_state.records=[]; st.session_state.rec={}
            st.session_state.gs_cache_loaded=False; st.rerun()

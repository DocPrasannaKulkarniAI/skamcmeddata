"""
SKAMCSHRC OPD v10.0 — Clean Rebuild
Sri Kalabyraveshwara Swamy Ayurvedic Medical College, Hospital & Research Centre

Conceptized by : Dr. Kiran M Goud, MD (Ay.)
Developed by   : Dr. Prasanna Kulkarni, MD (Ay.), MS (Data Science)

DEFAULT PINS:
  Admin (Dr. Prasanna)  : 9999
  Reception Desk        : 0000
  All Physicians        : 1234  (must change on first login)

GOOGLE SHEETS (optional):
  Add secrets in Streamlit Cloud → Settings → Secrets
  Without secrets the app works in session-only mode.

Run: streamlit run skamcmeddata_v10.py
Place newACD.xlsx in the same folder.
"""

import streamlit as st
import pandas as pd
import hashlib, re, io
from datetime import date, datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="SKAMCSHRC OPD", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif:wght@400;700&family=Inter:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.hdr{background:linear-gradient(135deg,#1a3a2a,#2d5a3d);border-radius:10px;
     padding:14px 24px;margin-bottom:16px;border-left:5px solid #c8a96e;}
.hdr h2{color:#f5e6c8;margin:0;font-size:1.2rem;}
.hdr p{color:#a8c5a0;margin:3px 0 0;font-size:0.78rem;}
.login-wrap{max-width:400px;margin:50px auto;background:#fff;
  border:1px solid #d1e5d8;border-radius:14px;padding:36px 38px;
  box-shadow:0 4px 20px rgba(0,0,0,0.07);}
.login-title{font-family:'Noto Serif',serif;font-size:1.25rem;font-weight:700;
  color:#1a3a2a;text-align:center;margin-bottom:4px;}
.login-sub{color:#888;font-size:0.78rem;text-align:center;margin-bottom:22px;}
.sec{font-size:0.73rem;font-weight:600;text-transform:uppercase;letter-spacing:1px;
  color:#2d6a4f;border-bottom:1px solid #b7d9c5;padding-bottom:5px;margin-bottom:10px;}
.card{background:#f8faf9;border:1px solid #d1e5d8;border-radius:9px;
  padding:14px 17px;margin-bottom:11px;}
.code-tag{background:#1a3a2a;color:#f5e6c8;border-radius:4px;
  padding:3px 9px;font-size:0.82rem;font-weight:700;font-family:monospace;}
.triage-u{background:#fef3c7;border:2px solid #d97706;border-radius:6px;
  padding:6px 12px;font-weight:600;color:#92400e;display:inline-block;}
.triage-r{background:#dcfce7;border:2px solid #16a34a;border-radius:6px;
  padding:6px 12px;font-weight:600;color:#14532d;display:inline-block;}
.bmi{background:#e3f2fd;border:1px solid #90caf9;border-radius:6px;
  padding:7px;text-align:center;font-weight:600;color:#1565c0;}
.tx-box{background:#fff8e1;border:1px solid #ffe082;border-radius:7px;
  padding:10px 14px;margin:6px 0;font-size:0.85rem;line-height:1.7;}
.med-box{background:#faf5ff;border:1px solid #d8b4fe;border-radius:8px;
  padding:12px 15px;margin:7px 0;}
.fu-box{background:#fff3cd;border:2px solid #ffc107;border-radius:8px;
  padding:12px 16px;margin:8px 0;}
.fu-box h4{color:#856404;margin:0 0 6px 0;font-size:0.92rem;}
.q-urgent{background:#fef3c7;border-left:4px solid #d97706;
  border-radius:6px;padding:8px 12px;margin:4px 0;}
.q-wait{background:#f0f7f3;border-left:4px solid #2d6a4f;
  border-radius:6px;padding:8px 12px;margin:4px 0;}
.q-done{background:#f5f5f5;border-left:4px solid #aaa;
  border-radius:6px;padding:8px 12px;margin:4px 0;opacity:0.75;}
.pin-box{background:#fff8e1;border:2px solid #ffc107;border-radius:9px;
  padding:22px;margin:10px 0;}
.rb-admin{background:#1a3a2a;color:#f5e6c8;border-radius:5px;
  padding:3px 10px;font-size:0.78rem;font-weight:700;}
.rb-phys{background:#1565c0;color:white;border-radius:5px;
  padding:3px 10px;font-size:0.78rem;font-weight:700;}
.rb-recep{background:#2e7d32;color:white;border-radius:5px;
  padding:3px 10px;font-size:0.78rem;font-weight:700;}
.stTabs [data-baseweb="tab"]{height:42px;background:#f0f7f3;
  border-radius:8px 8px 0 0;border:1px solid #c8dfd0;font-weight:500;
  color:#2d5a3d;font-size:0.87rem;}
.stTabs [aria-selected="true"]{background:#2d5a3d !important;
  color:#f5e6c8 !important;border-color:#2d5a3d !important;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────
ADMIN_NAME    = "Dr. Prasanna"
ADMIN_PIN     = "9999"
RECEP_NAME    = "Reception Desk"
RECEP_PIN     = "0000"
DEFAULT_PHYS_PIN = "1234"
SESSION_HRS   = 8

def hp(p): return hashlib.sha256(str(p).encode()).hexdigest()

# ─────────────────────────────────────────────────────────────────
# MASTER PHYSICIAN LIST
# Single source of truth — used in login dropdown AND reception dropdown
# ─────────────────────────────────────────────────────────────────
MASTER_PHYSICIANS = [
    ("Dr. Abdul",          ["KC","PK"]),
    ("Dr. Amrutha",        ["KC"]),
    ("Dr. Anjali",         ["SHALYA"]),
    ("Dr. Anupama",        ["PRASOOTI","STREE_ROGA"]),
    ("Dr. Chaitra N",      ["PRASOOTI","STREE_ROGA"]),
    ("Dr. Chetana",        ["PRASOOTI","STREE_ROGA"]),
    ("Dr. Elgeena",        ["SPL"]),
    ("Dr. Gopal TL",       ["AGADA","SPL"]),
    ("Dr. Hamsaveni",      ["SHALAKYA"]),
    ("Dr. Harshitha",      ["KC"]),
    ("Dr. Jambavathi",     ["SHALYA"]),
    ("Dr. Jyothi",         ["SPL"]),
    ("Dr. Karthik",        ["SPL"]),
    ("Dr. Kiran Kumar",    ["AGADA","SPL"]),
    ("Dr. Kiran M Goud",   ["PK"]),
    ("Dr. Lokeshwari",     ["KB"]),
    ("Dr. Lolashri",       ["PK"]),
    ("Dr. Mahantesh",      ["SPL"]),
    ("Dr. Manasa",         ["AGADA"]),
    ("Dr. Mangala",        ["KB"]),
    ("Dr. Manjunath",      ["KC","PK"]),
    ("Dr. Meera",          ["AGADA"]),
    ("Dr. Nayan",          ["KB"]),
    ("Dr. Nayana",         ["AGADA"]),
    ("Dr. Neetha",         ["AGADA"]),
    ("Dr. Neharu",         ["SHALYA"]),
    ("Dr. Nithyashree",    ["SHALAKYA"]),
    ("Dr. Padmavathi",     ["SHALAKYA"]),
    ("Dr. Papiya Jana",    ["PRASOOTI","STREE_ROGA"]),
    ("Dr. Pranesh",        ["KC"]),
    ("Dr. Prasanna",       ["SPL","YOGA"]),
    ("Dr. Prathibha",      ["SPL"]),
    ("Dr. Priyanka",       ["KB","SPL"]),
    ("Dr. Pushpa",         ["KB"]),
    ("Dr. Radhika",        ["AGADA"]),
    ("Dr. Roopini",        ["AGADA"]),
    ("Dr. Shailaja SV",    ["SHALYA"]),
    ("Dr. Shanthala",      ["SPL"]),
    ("Dr. Shashirekha",    ["KC","SPL","YOGA"]),
    ("Dr. Sheshashaye B",  ["SHALYA"]),
    ("Dr. Shilpa",         ["SPL"]),
    ("Dr. Shreyas",        ["KC","PK"]),
    ("Dr. Shridevi",       ["PRASOOTI","STREE_ROGA"]),
    ("Dr. Shubha V Hegde", ["AGADA"]),
    ("Dr. Sindhura",       ["KC","PK"]),
    ("Dr. Sowmya",         ["PRASOOTI","STREE_ROGA"]),
    ("Dr. Sreekanth",      ["AGADA"]),
    ("Dr. Sujathamma",     ["SHALAKYA"]),
    ("Dr. Suma Saji",      ["AGADA"]),
    ("Dr. Sunayana",       ["SPL","YOGA"]),
    ("Dr. Sunitha GS",     ["AGADA","KC"]),
    ("Dr. Supreeth MJ",    ["KC","PK"]),
    ("Dr. Usha",           ["PK"]),
    ("Dr. Veena",          ["SHALAKYA"]),
    ("Dr. Venkatesh",      ["SHALAKYA"]),
    ("Dr. Vijayalakshmi",  ["KC","PK"]),
    ("Dr. Vinay Kumar KN", ["KC","PK"]),
    ("Dr. Vishwanath",     ["SHALYA"]),
]

# Name → departments dict for fast lookup
PHYS_DEPTS = {name: depts for name, depts in MASTER_PHYSICIANS}
ALL_PHYS_NAMES = [name for name, _ in MASTER_PHYSICIANS]

# ─────────────────────────────────────────────────────────────────
# GOOGLE SHEETS (optional — app works without it)
# ─────────────────────────────────────────────────────────────────
OPD_COLS = [
    "Patient_ID","Patient_Name","Mobile","Token_No","Visit_Date","Visit_Time",
    "Visit_DateTime","Visit_Count","Visit_Type","Age","Gender","District",
    "Occupation","Prakriti","Lifestyle_Risk","Triage","Department","Physician",
    "Status","Consent","Chief_Complaints","ACD_Code_1","ACD_Meaning_1",
    "ACD_Code_2","ACD_Meaning_2","Severity","Disease_Duration",
    "Height_cm","Weight_kg","BMI","BMI_Category","BP","Pulse_bpm",
    "Temp_F","SpO2_pct","RR_per_min","Other_Investigation",
    "Nadi","Jihva","Agni","Mala","Mutra","Sleep","Shabda","Sparsha","Drik","Akriti",
    "Dosha","Dushya","Bala","Kala","Satva","Satmya","Vyasana","Prakriti_Confirmed",
    "Final_ACD_Code","Final_ACD_Meaning","Treatment_Response",
    "TX_Purvakarma","TX_Pradhana_Karma","TX_Pashchata_Karma",
    "TX_Comments_Purvakarma","TX_Comments_Pradhana","TX_Comments_Pashchata",
    "TX_Custom","Medicines_Summary","Lab_Tests","Followup_Date",
    "Instructions","Physician_Notes","Followup_Notes",
]
PHYS_COLS = ["Name","PIN_Hash","PIN_Set","Added_Date","Active","Extra_Depts"]

@st.cache_resource(show_spinner=False)
def connect_sheets():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        if "gcp_service_account" not in st.secrets: return None, None, "Secrets not configured"
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive"])
        gc = gspread.authorize(creds)
        wb = gc.open(st.secrets["sheet"]["name"])
        # Get or create sheets
        def get_ws(title, headers):
            try: ws = wb.worksheet(title)
            except:
                ws = wb.add_worksheet(title=title, rows=5000, cols=len(headers))
                ws.append_row(headers)
            if not ws.row_values(1): ws.append_row(headers)
            return ws
        ws_opd  = get_ws("OPD_Records", OPD_COLS)
        ws_phys = get_ws("Physicians",  PHYS_COLS)
        return ws_opd, ws_phys, None
    except Exception as e:
        return None, None, str(e)

def gs_load(ws):
    try: return ws.get_all_records() if ws else []
    except: return []

def gs_upsert(ws, row_dict, keys):
    if not ws: return
    try:
        cols = list(row_dict.keys())
        row  = [clean(str(row_dict.get(c,""))) for c in cols]
        all_v = ws.get_all_values()
        if not all_v: ws.append_row(row); return
        hdrs = all_v[0]
        kidx = {k: hdrs.index(k) for k in keys if k in hdrs}
        for i,r in enumerate(all_v[1:], start=2):
            if all(len(r)>kidx[k] and r[kidx[k]]==clean(str(row_dict.get(k,""))) for k in kidx):
                full = [clean(str(row_dict.get(h,""))) for h in hdrs]
                ws.update(f"A{i}", [full]); return
        ws.append_row(row)
    except Exception as e:
        st.toast(f"Sheet sync: {e}", icon="⚠️")

# ─────────────────────────────────────────────────────────────────
# ACD CODES — FLAT SEARCH
# ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_acd(fp="newACD.xlsx"):
    try:
        df = pd.read_excel(fp)
        df.columns = ["ACD","code","condition","meaning"]
        df = df.dropna(subset=["code"])
        df["code"]      = df["code"].astype(str).str.strip()
        df["condition"] = df["condition"].fillna("").astype(str).str.strip()
        df["meaning"]   = df["meaning"].fillna("").astype(str).str.strip()
        is_top = lambda c: bool(re.match(r"^[A-Z]{1,4}$", c))
        leaves = []
        for _, r in df[~df["code"].apply(is_top)].iterrows():
            leaves.append({
                "code": r["code"], "condition": r["condition"], "meaning": r["meaning"],
                "label": f"{r['condition']} ({r['meaning']}) [{r['code']}]",
                "search": f"{r['condition']} {r['meaning']} {r['code']}".lower(),
            })
        return leaves, True
    except FileNotFoundError:
        return [], False

ACD_FLAT, ACD_OK = load_acd("newACD.xlsx")

def acd_search(q, n=40):
    if not q or len(q) < 2: return []
    ql = q.lower().strip()
    exact = [i for i in ACD_FLAT if i["code"].lower() == ql]
    rest  = [i for i in ACD_FLAT if ql in i["search"] and i not in exact]
    return (exact + rest)[:n]

def acd_widget(sk, selk, label="Search Diagnosis"):
    q = st.text_input(label, key=sk,
                      placeholder="Type any term — e.g. tonsil, sciatica, fever, AAB-6 ...")
    res = acd_search(q)
    if q and len(q) >= 2:
        if res:
            opts = ["— Select —"] + [r["label"] for r in res]
            sel  = st.selectbox(f"Matching conditions ({len(res)} found)", opts, key=selk)
            if sel != "— Select —":
                code = sel.split("[")[-1].rstrip("]").strip()
                mean = sel.split("(")[-1].split(")")[0].strip() if "(" in sel else ""
                st.markdown(f'<span class="code-tag">{code}</span>&nbsp;&nbsp;'
                            f'<span style="color:#555;font-size:0.82rem">{mean}</span>',
                            unsafe_allow_html=True)
                return sel, code, mean
        else:
            st.caption("No matches — try different keywords")
    return "", "", ""

# ─────────────────────────────────────────────────────────────────
# STATIC DROPDOWN DATA
# ─────────────────────────────────────────────────────────────────
DEPARTMENTS = {
    "KC":"Kaya Chikitsa (General Medicine)", "PK":"Panchakarma",
    "SPL":"Swasthavritta & Lifestyle",       "AGADA":"Agada Tantra",
    "SHALYA":"Shalya Tantra",                "SHALAKYA":"Shalakya Tantra",
    "KB":"Kaumarabhritya (Paediatrics)",      "PRASOOTI":"Prasooti Tantra",
    "STREE_ROGA":"Stri Roga",                "YOGA":"Yoga & Wellness",
}
DEPT_CONDITIONS = {
    "KC":["Fever","Vomiting / Nausea","GIT Disorders","Fatigue","Giddiness",
          "Loss of Strength","Stroke / Hemiplegia","Facial Paralysis","Weakness",
          "Cough / Respiratory","Cardiac Complaints","Jaundice","Anaemia",
          "Headache","Loss of Appetite","Constipation","Other"],
    "PK":["Low Back Pain","Knee / Joint Pain","Cervical / Neck Pain","Shoulder Pain",
          "Sciatica","Rheumatoid Arthritis","Osteoarthritis","Gout","Frozen Shoulder",
          "Hemiplegia (PK)","Facial Palsy (PK)","Neurological disorder","Other"],
    "SPL":["Obesity","Diabetes Mellitus","High Cholesterol","Hypothyroidism",
           "Hyperthyroidism","Metabolic Syndrome","Hypertension","Insomnia",
           "Stress / Anxiety","Chronic Fatigue","Other"],
    "AGADA":["Psoriasis","Eczema / Dermatitis","Hair Fall","Premature Greying",
             "Vitiligo","Allergic Skin Reaction","Herpes / Skin Eruption","Acne",
             "Fungal Infection","Toxic conditions","Other"],
    "SHALYA":["Haemorrhoids / Piles","Fistula-in-Ano","Fissure-in-Ano",
              "Rectal Prolapse","Wound / Ulcer","Fracture","Abscess",
              "Urinary complaints","Urinary Incontinence","Kidney Stone","Other"],
    "SHALAKYA":["Diminished Vision","Cataract","Conjunctivitis","Eye Pain",
                "Sinusitis","Nasal Obstruction","Earache / Ear Discharge",
                "Hearing Loss","Throat Pain / Tonsillitis","Dental Disorder","Other"],
    "KB":["Fever (Child)","Diarrhoea (Child)","Failure to Thrive","Juvenile Arthritis",
          "Cerebral Palsy","Childhood Asthma","Skin Disorder (Child)","Worm Infestation",
          "Growth Retardation","Developmental Disorder","Other"],
    "PRASOOTI":["Morning Sickness","Back Pain in Pregnancy","Oedema in Pregnancy",
                "Gestational Diabetes","Gestational Hypertension","Threatened Abortion",
                "Antenatal Checkup","Post-partum Disorders","Insufficient Lactation","Other"],
    "STREE_ROGA":["Menorrhagia","Irregular Periods","Dysmenorrhoea","Leucorrhoea",
                  "Infertility (Female)","PCOS / Ovarian Cyst","Uterine Fibroid",
                  "Menopausal Complaints","Pelvic Pain / PID","Other"],
    "YOGA":["Stress / Burnout","Insomnia","Low Immunity","Obesity (Yoga)",
            "Respiratory Wellness","General Wellness"],
}
PK_TX = {
    "Purvakarma":[
        ("SAT-I.43","Snehana","Therapeutic Oleation"),
        ("SAT-I.54","Svedana","Therapeutic Sudation"),
        ("SAT-I.439","Abhyanga","Full-body Oil Massage"),
        ("SAT-I.99","Udvartana","Dry Powder Massage"),
        ("SAT-I.445","Sneha Pana","Internal Oleation"),
    ],
    "Pradhana Karma":[
        ("SAT-I.139","Vamana Karma","Therapeutic Emesis"),
        ("SAT-I.140","Virecana Karma","Therapeutic Purgation"),
        ("SAT-I.141","Basti Karma","Therapeutic Enema"),
        ("SAT-I.142","Anuvasan Basti","Unctuous Enema"),
        ("SAT-I.145","Asthapana Basti","Decoction Enema"),
        ("SAT-I.144","Matra Basti","Small-dose Enema"),
        ("SAT-I.155","Uttara Basti","Intra-vaginal / Urethral Basti"),
        ("SAT-I.156","Nasya","Nasal Medication"),
        ("SAT-I.413","Raktamokshana","Bloodletting / Leech Therapy"),
    ],
    "Pashchata Karma":[
        ("SAT-I.86","Shiro Basti","Oil Retention over Head"),
        ("SAT-I.89","Shirodhara","Oil Streaming over Head"),
        ("SAT-I.90","Takra Dhara","Buttermilk Streaming"),
        ("SAT-I.91","Kashaya Dhara","Decoction Streaming"),
        ("SAT-I.92","Manya Basti","Cervical Oil Retention"),
        ("SAT-I.93","Hrid Basti","Cardiac Oil Retention"),
        ("SAT-I.94","Prishtha Basti","Thoraco-lumbar Oil Retention"),
        ("SAT-I.95","Kati Basti","Lumbo-sacral Oil Retention"),
        ("SAT-I.96","Janu Basti","Knee Oil Retention"),
        ("SAT-I.123","Pinda Sveda","Bolus Sudation / Kizhi"),
        ("SAT-I.112","Nadi Sveda","Steam Pipe Fomentation"),
        ("SAT-I.114","Avagaha Sveda","Medicated Tub Bath"),
        ("SAT-I.241","Netra Tarpana","Eye Retention Therapy"),
        ("SAT-I.286","Karna Purana","Ear Oil Filling"),
        ("SAT-I.490","Kavala Dharana","Oil Pulling / Gargling"),
        ("SAT-I.55","Lepa","Medicated Paste"),
        ("SAT-I.438","Parisheka","Medicated Streaming"),
        ("SAT-I.406","Kshara Karma","Caustic Application"),
        ("SAT-I.409","Agni Karma","Thermal Cauterization"),
    ],
}
DOSAGE_FORMS=["Churna (Powder)","Kashaya (Decoction)","Vati / Gutika (Tablet/Pill)",
               "Ghrita (Medicated Ghee)","Taila (Medicated Oil)","Capsule","Avaleha (Linctus)",
               "Asava / Arishta (Fermented)","Bhasma (Calcined)","Syrup","Drops","— Custom —"]
ROUTE_OPTIONS=["Oral","External / Topical","Nasal","Rectal","Ophthalmic","Otic (Ear)","— Custom —"]
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
JIHVA_OPT=["Sama/Lipta (Coated)","Nirama/Shuddha (Clean)","Ruksha (Dry)","Ardra (Moist)",
            "Shveta Lipta","Pita Lipta","Krishna Lipta","Other (specify below)"]
AGNI_OPT=["Sama Agni (Normal)","Vishama Agni (Irregular)","Tikshna Agni (Hyperacid)",
           "Manda Agni (Sluggish)","Other (specify below)"]
MALA_OPT=["Samyak (1-2/day, formed)","Vibandha (Constipated)","Atisara (Loose/Frequent)",
           "Amayukta (Mucus/Undigested)","Other (specify below)"]
MUTRA_OPT=["Samyak (4-6/day, clear)","Alpa (Oliguria)","Adhika (Polyuria)",
            "Krichra (Dysuria)","Nocturia","Other (specify below)"]
SLEEP_OPT=["Samyak Nidra (6-8 hrs)","Nidranasha (Insomnia)","Atinidra (Hypersomnia)",
            "Disturbed / Fragmented","Other (specify below)"]
DOSHA_OPT=["Vata Pradhana","Pitta Pradhana","Kapha Pradhana","Vata-Pitta","Pitta-Kapha",
            "Vata-Kapha","Tridosha","Other (specify below)"]
DUSHYA_OPT=["Rasa","Rakta","Mamsa","Meda","Asthi","Majja","Shukra / Artava","Other (specify below)"]
BALA_OPT=["Pravara Bala (Strong)","Madhyama Bala (Moderate)","Avara Bala (Weak)","Other (specify below)"]
KALA_OPT=["Vasanta (Spring)","Grishma (Summer)","Varsha (Monsoon)",
           "Sharad (Autumn)","Hemanta (Early Winter)","Shishira (Late Winter)"]
SATVA_OPT=["Sattva Pradhana","Rajas Pradhana","Tamas Pradhana","Madhyama","Other (specify below)"]
SATMYA_OPT=["Sarva Satmya","Desha Satmya","Kula Satmya","Madhyama","Other (specify below)"]
AKRITI_OPT=SHABDA_OPT=SPARSHA_OPT=DRIK_OPT=["Prakruta (Normal)","Vikruta (Altered)","Not assessed","Other (specify below)"]
VYASANA_OPT=["None (NA)","Dhumapana (Smoking)","Madyapana (Alcohol)",
              "Tambula / Gutkha","Multiple habits","Other (specify below)"]
SEVERITY_OPT=["Mridu (Mild)","Madhyama (Moderate)","Maha / Tivra (Severe)"]
DURATION_OPT=["Less than 1 month (Acute)","1-6 months","6-12 months",
               "1-2 years","2-5 years","5-10 years","More than 10 years (Chronic)"]
LIFESTYLE_RISK=["Musculo-Skeletal","Cardiovascular","Metabolic / Endocrine","Neurological",
                 "Respiratory","Gastrointestinal","Gynaecological","Paediatric",
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
TREATMENT_RESPONSE=["Not yet assessed","Excellent — complete relief",
                     "Good — significant improvement","Partial — moderate improvement",
                     "Minimal — slight improvement","No response","Worsened"]
BMI_CATS=[(0,18.5,"Underweight"),(18.5,23,"Normal (Asian)"),(23,25,"Overweight Gr.1"),
           (25,30,"Overweight Gr.2"),(30,999,"Obese")]

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────
def bmi_cat(b):
    for lo,hi,l in BMI_CATS:
        if lo<=b<hi: return l
    return ""

def sec(t): st.markdown(f'<div class="sec">{t}</div>', unsafe_allow_html=True)
def dlbl(k): return DEPARTMENTS.get(k, k)
def xcode(s): return s.split("[")[-1].rstrip("]").strip() if s and "[" in s else ""
def clean(v): return re.sub(r'[^\x00-\x7F\u0900-\u097F\u0080-\u00FF]','',str(v)).strip()

def sel_other(label, opts, key, idx=0):
    v = st.selectbox(label, opts, index=idx, key=key)
    if v == "Other (specify below)":
        ov = st.text_input(f"Specify — {label}", key=f"{key}_o", placeholder="Type here")
        return ov if ov else "Other"
    return v

def csel(label, opts, key, idx=0):
    v = st.selectbox(label, opts, index=idx, key=key)
    if v == "— Custom —":
        cv = st.text_input(f"Custom", key=f"{key}_c", placeholder="Type here")
        return cv if cv else ""
    return v

def validate_mobile(m): return bool(re.match(r"^\d{10}$", str(m).strip()))

def auto_pid():
    yr = str(date.today().year)[2:]
    n  = st.session_state.get("pid_counter", 1)
    return f"N{yr}{n:04d}"

def next_token(records):
    today = str(date.today())
    nums  = []
    for r in records:
        if str(r.get("Visit_Date","")).startswith(today) and "-" in str(r.get("Token_No","")):
            try: nums.append(int(str(r["Token_No"]).split("-")[-1]))
            except: pass
    return f"{today}-{(max(nums)+1 if nums else 1):03d}"

def find_patient(records, pid=None, mobile=None):
    out = []
    for r in records:
        if pid    and str(r.get("Patient_ID","")).strip() == str(pid).strip():    out.append(r)
        elif mobile and str(r.get("Mobile","")).strip()     == str(mobile).strip(): out.append(r)
    return sorted(out, key=lambda x: x.get("Visit_DateTime",""))

def reset_form():
    for cat in ["Purvakarma","Pradhana Karma","Pashchata Karma"]:
        st.session_state[f"tx_{cat}"] = []
        st.session_state[f"tc_{cat}"] = {}
    st.session_state.med_count  = 1
    st.session_state.active_rec = {}
    st.session_state.pop("ret_patient", None)
    st.session_state.pop("ret_vc",      None)

# ─────────────────────────────────────────────────────────────────
# PIN MANAGEMENT
# Uses session-based pin store: {name: {"hash": ..., "set": bool}}
# ─────────────────────────────────────────────────────────────────
def init_pins():
    """Build default pin store from master list if not already done."""
    if "pin_store" not in st.session_state:
        store = {}
        # Admin
        store[ADMIN_NAME] = {"hash": hp(ADMIN_PIN), "set": True}
        # Reception
        store[RECEP_NAME] = {"hash": hp(RECEP_PIN), "set": True}
        # All physicians — default 1234
        for name, _ in MASTER_PHYSICIANS:
            if name != ADMIN_NAME:
                store[name] = {"hash": hp(DEFAULT_PHYS_PIN), "set": False}
        st.session_state.pin_store = store

    # Overlay with anything saved in Google Sheets Physicians tab
    # Admin and Reception PINs are ALWAYS from code constants — never overridden by sheet
    if st.session_state.get("gs_phys_loaded") is False:
        ws_phys = st.session_state.get("ws_phys")
        if ws_phys:
            rows = gs_load(ws_phys)
            for row in rows:
                name = str(row.get("Name","")).strip()
                if name in (ADMIN_NAME, RECEP_NAME):
                    continue  # never override hardcoded admin/reception
                if name and row.get("PIN_Hash",""):
                    st.session_state.pin_store[name] = {
                        "hash": str(row["PIN_Hash"]),
                        "set":  str(row.get("PIN_Set","No")) == "Yes",
                    }
        st.session_state.gs_phys_loaded = True

def check_pin(name, pin_entered):
    """Returns (ok, needs_change)."""
    store = st.session_state.get("pin_store", {})
    entry = store.get(name)
    if not entry: return False, False
    if hp(pin_entered) == entry["hash"]:
        return True, not entry["set"]
    return False, False

def save_new_pin(name, new_pin):
    store = st.session_state.get("pin_store", {})
    store[name] = {"hash": hp(new_pin), "set": True}
    st.session_state.pin_store = store
    # Persist to sheet
    ws_phys = st.session_state.get("ws_phys")
    if ws_phys:
        gs_upsert(ws_phys,
                  {"Name": name, "PIN_Hash": hp(new_pin), "PIN_Set": "Yes",
                   "Added_Date": str(date.today()), "Active": "Yes", "Extra_Depts": ""},
                  ["Name"])

def get_role(name):
    if name == ADMIN_NAME:    return "Admin"
    if name == RECEP_NAME:    return "Receptionist"
    return "Physician"

# ─────────────────────────────────────────────────────────────────
# DOSE TRANSLATION
# ─────────────────────────────────────────────────────────────────
def dose_to_text(dose, form):
    fm = (form or "").lower()
    if any(x in fm for x in ["vati","gutika","tablet","capsule","cap"]): unit="tablet(s)"
    elif any(x in fm for x in ["churna","powder","bhasma"]):             unit="gram(s)"
    elif any(x in fm for x in ["kashaya","syrup","asava","arishta","taila","ghrita","avaleha","kwatha"]): unit="ml"
    elif "drop" in fm:  unit="drop(s)"
    else:               unit="dose"
    M={"1 OD":f"Take 1 {unit} once daily","1 BD":f"Take 1 {unit} twice daily",
       "1 TID":f"Take 1 {unit} thrice daily","2 BD":f"Take 2 {unit} twice daily",
       "2 TID":f"Take 2 {unit} thrice daily","1 HS":f"Take 1 {unit} at bedtime",
       "SOS":f"Take as needed (SOS)","5 ml OD":"Take 5 ml once daily",
       "5 ml BD":"Take 5 ml twice daily","5 ml TID":"Take 5 ml thrice daily",
       "10 ml OD":"Take 10 ml once daily","10 ml BD":"Take 10 ml twice daily",
       "10 ml TID":"Take 10 ml thrice daily","1 tsp OD":"Take 1 tsp (5ml) once daily",
       "1 tsp BD":"Take 1 tsp (5ml) twice daily","1 tsp TID":"Take 1 tsp (5ml) thrice daily"}
    return M.get(dose, dose or "")

def timing_txt(t):
    M={"Before food":"before meals","After food":"after meals","Between meals":"between meals",
       "At bedtime":"at bedtime","Empty stomach":"on empty stomach","With food":"with meals"}
    return M.get(t, t.lower() if t else "")

def anupana_txt(a):
    M={"Water":"with water","Warm water":"with warm water","Milk":"with milk",
       "Honey":"with honey","Ghee":"with ghee","Buttermilk":"with buttermilk",
       "Coconut water":"with coconut water","Ginger juice":"with ginger juice"}
    return M.get(a, f"with {a.lower()}" if a else "")

def med_instruction(m):
    parts = [dose_to_text(m.get("dose",""), m.get("form",""))]
    if m.get("timing"):  parts.append(timing_txt(m["timing"]))
    if m.get("anupana"): parts.append(anupana_txt(m["anupana"]))
    if m.get("dur_val"): parts.append(f"for {m['dur_val']} {m.get('dur_unit','Days').lower()}")
    if m.get("notes"):   parts.append(f"({m['notes']})")
    return ", ".join(p for p in parts if p)

# ─────────────────────────────────────────────────────────────────
# PDF ENGINE
# ─────────────────────────────────────────────────────────────────
G=colors.HexColor("#1a3a2a"); GOLD=colors.HexColor("#c8a96e")
GY=colors.HexColor("#888"); DGY=colors.HexColor("#444"); BG=colors.HexColor("#f0f7f3")

def Ps():
    return {
        "hm":  ParagraphStyle("hm",fontName="Helvetica",fontSize=7.5,alignment=TA_CENTER,textColor=GY,spaceAfter=1),
        "sec": ParagraphStyle("sec",fontName="Helvetica-Bold",fontSize=9,textColor=G,spaceBefore=5,spaceAfter=2),
        "n":   ParagraphStyle("n",fontName="Helvetica",fontSize=8.5,spaceAfter=2,leading=12),
        "sm":  ParagraphStyle("sm",fontName="Helvetica",fontSize=7.5,textColor=DGY,leading=11),
        "bd":  ParagraphStyle("bd",fontName="Helvetica-Bold",fontSize=8.5,leading=12),
        "dx":  ParagraphStyle("dx",fontName="Helvetica-Bold",fontSize=15,textColor=G,spaceAfter=1),
        "dxs": ParagraphStyle("dxs",fontName="Helvetica",fontSize=9,textColor=DGY,spaceAfter=4),
        "ptn": ParagraphStyle("ptn",fontName="Helvetica-Bold",fontSize=11,textColor=G),
        "mi":  ParagraphStyle("mi",fontName="Helvetica",fontSize=8,textColor=colors.HexColor("#1a237e"),leading=11),
        "ins": ParagraphStyle("ins",fontName="Helvetica",fontSize=8.5,textColor=colors.HexColor("#1a237e"),leading=13,spaceAfter=2),
        "sR":  ParagraphStyle("sR",fontName="Helvetica",fontSize=8,alignment=TA_RIGHT),
        "sL":  ParagraphStyle("sL",fontName="Helvetica",fontSize=8,alignment=TA_LEFT),
        "ft":  ParagraphStyle("ft",fontName="Helvetica",fontSize=6.5,alignment=TA_CENTER,textColor=GY),
    }

def pdf_hdr(story, S, W):
    story.append(Paragraph("JAI SRI GURUDEV", S["hm"]))
    story.append(Paragraph("Sri Kalabyraveshwara Swamy Ayurvedic Medical College, Hospital & Research Centre",
                            ParagraphStyle("hb",fontName="Helvetica-Bold",fontSize=9.5,alignment=TA_CENTER,textColor=G,spaceAfter=1)))
    story.append(Paragraph("No.10, Pipeline Road, RPC Layout, Hampinagara, Vijayanagar 2nd Stage, Bangalore - 560104",S["hm"]))
    story.append(Paragraph("Ph: 080-XXXXXXXX  |  info@skamcshrc.edu.in  |  NABH Accredited",S["hm"]))
    story.append(HRFlowable(width=W,thickness=2,color=G,spaceAfter=1))
    story.append(HRFlowable(width=W,thickness=0.8,color=GOLD,spaceAfter=3))

def pdf_pat(rec, S, W):
    rows=[
        [Paragraph(f"<b>{rec.get('Patient_Name','—')}</b>",S["ptn"]),
         Paragraph("",S["n"]),
         Paragraph(f"<b>Token: {rec.get('Token_No','')}</b>",
                   ParagraphStyle("tok",fontName="Helvetica-Bold",fontSize=10,textColor=G,alignment=TA_RIGHT)),
         Paragraph(datetime.now().strftime("%d %b %Y  %I:%M %p"),
                   ParagraphStyle("dt",fontName="Helvetica",fontSize=8,alignment=TA_RIGHT))],
        [Paragraph(f"<b>ID:</b> {rec.get('Patient_ID','')}  |  <b>Mobile:</b> {rec.get('Mobile','')}",S["n"]),
         Paragraph("",S["n"]),
         Paragraph(f"<b>Age / Gender:</b> {rec.get('Age','')} yrs / {rec.get('Gender','')}",S["n"]),
         Paragraph(f"<b>Visit #{rec.get('Visit_Count','1')}</b>  |  {rec.get('Visit_Type','')}",
                   ParagraphStyle("vs",fontName="Helvetica",fontSize=8.5,alignment=TA_RIGHT))],
        [Paragraph(f"<b>Dept:</b> {rec.get('Department','')}  |  <b>Prakriti:</b> {rec.get('Prakriti','')}",S["n"]),
         Paragraph("",S["n"]),Paragraph("",S["n"]),
         Paragraph(f"<b>{rec.get('Physician','')}</b>",
                   ParagraphStyle("ph",fontName="Helvetica-Bold",fontSize=8.5,alignment=TA_RIGHT))],
    ]
    t=Table(rows,colWidths=[60*mm,10*mm,55*mm,48*mm])
    t.setStyle(TableStyle([("FONTSIZE",(0,0),(-1,-1),8.5),
                            ("ROWBACKGROUNDS",(0,0),(-1,-1),[BG,colors.white,BG]),
                            ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#cccccc")),
                            ("TOPPADDING",(0,0),(-1,-1),2.5),("BOTTOMPADDING",(0,0),(-1,-1),2.5),
                            ("SPAN",(0,0),(1,0)),("SPAN",(2,0),(3,0)),
                            ("SPAN",(0,1),(1,1)),("SPAN",(0,2),(1,2))]))
    return t

def make_pdf(rec, mode="both"):
    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,topMargin=12*mm,bottomMargin=18*mm,
                           leftMargin=18*mm,rightMargin=18*mm)
    W=A4[0]-36*mm; S=Ps(); story=[]
    pdf_hdr(story,S,W)
    title={"rx":"Prescription","pk":"Panchakarma Advice","both":"OPD Prescription"}.get(mode,"Prescription")
    story.append(Paragraph(title,ParagraphStyle("tit",fontName="Helvetica-Bold",fontSize=13,
                                                 alignment=TA_CENTER,textColor=G,spaceAfter=2)))
    story.append(HRFlowable(width=W,thickness=0.8,color=GOLD,spaceAfter=3))
    story.append(pdf_pat(rec,S,W)); story.append(Spacer(1,1*mm))
    vit=(f"Ht:{rec.get('Height_cm','')}cm  Wt:{rec.get('Weight_kg','')}kg  "
         f"BMI:{rec.get('BMI','')}({rec.get('BMI_Category','')})  "
         f"BP:{rec.get('BP','')}  Pulse:{rec.get('Pulse_bpm','')}bpm  "
         f"Temp:{rec.get('Temp_F','')}F  SpO2:{rec.get('SpO2_pct','')}%")
    story.append(Paragraph(vit,S["sm"]))
    # Diagnosis
    code=rec.get("Final_ACD_Code") or rec.get("ACD_Code_1","")
    mean=rec.get("Final_ACD_Meaning") or rec.get("ACD_Meaning_1","")
    cc=rec.get("Chief_Complaints","")
    if code or cc:
        story.append(HRFlowable(width=W,thickness=0.5,color=colors.HexColor("#b7d9c5"),spaceAfter=2))
    if cc: story.append(Paragraph(f"C/O: {cc}",S["sm"]))
    if code: story.append(Paragraph(code,S["dx"])); story.append(Paragraph(mean,S["dxs"]))
    # Medicines
    if mode in ("rx","both"):
        meds=rec.get("Medicines",[])
        if meds:
            story.append(HRFlowable(width=W,thickness=0.5,color=colors.HexColor("#b7d9c5"),spaceAfter=2))
            story.append(Paragraph("Shamana Aushadhi",S["sec"]))
            hdr=[[Paragraph(h,S["bd"]) for h in ["#","Drug Name","Form / Route","Instruction","Duration"]]]
            rows=[]
            for i,m in enumerate(meds,1):
                fr=m.get("form","")
                if m.get("route","Oral")!="Oral": fr+=f"\n({m.get('route','')})"
                rows.append([Paragraph(str(i),S["sm"]),
                             Paragraph(f"<b>{m.get('name','')}</b>",S["n"]),
                             Paragraph(fr,S["sm"]),
                             Paragraph(med_instruction(m),S["mi"]),
                             Paragraph(f"{m.get('dur_val','')} {m.get('dur_unit','')}",S["sm"])])
            mt=Table(hdr+rows,colWidths=[6*mm,48*mm,28*mm,W-110*mm,28*mm])
            mt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),G),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                                     ("FONTSIZE",(0,0),(-1,-1),7.5),("ROWBACKGROUNDS",(0,1),(-1,-1),[BG,colors.white]),
                                     ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#cccccc")),
                                     ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),("VALIGN",(0,0),(-1,-1),"TOP")]))
            story.append(mt)
    # PK
    if mode in ("pk","both"):
        all_tx=[(c,rec.get(f"tx_{c}",[]),rec.get(f"tc_{c}",{}))
                for c in ["Purvakarma","Pradhana Karma","Pashchata Karma"]]
        all_tx=[(c,s,cm) for c,s,cm in all_tx if s]
        if all_tx:
            story.append(HRFlowable(width=W,thickness=0.5,color=colors.HexColor("#b7d9c5"),spaceAfter=2))
            story.append(Paragraph("Panchakarma Treatment Plan",S["sec"]))
            cat_bg={"Purvakarma":colors.HexColor("#e8f5e9"),"Pradhana Karma":colors.HexColor("#fff3e0"),
                    "Pashchata Karma":colors.HexColor("#e3f2fd")}
            for cat,sel,cmt in all_tx:
                story.append(Paragraph(f"<b>{cat}</b>",S["bd"]))
                rows=[[Paragraph(h,S["bd"]) for h in ["Procedure","Code","Comments"]]]
                for tx in sel:
                    code2=xcode(tx); name2=tx.split(" — ")[0] if " — " in tx else tx
                    rows.append([Paragraph(name2,S["n"]),
                                 Paragraph(f"<b>{code2}</b>",ParagraphStyle("pc",fontName="Helvetica-Bold",fontSize=8,textColor=G)),
                                 Paragraph(cmt.get(code2,""),S["sm"])])
                tbl=Table(rows,colWidths=[55*mm,22*mm,W-77*mm])
                tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),G),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                                          ("FONTSIZE",(0,0),(-1,-1),7.5),("BACKGROUND",(0,1),(-1,-1),cat_bg.get(cat,BG)),
                                          ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#cccccc")),
                                          ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),("VALIGN",(0,0),(-1,-1),"TOP")]))
                story.append(tbl); story.append(Spacer(1,1.5*mm))
        if rec.get("TX_Custom"): story.append(Paragraph(f"<b>Additional:</b>  {rec['TX_Custom']}",S["sm"]))
    # Extras
    if rec.get("Lab_Tests"):
        story.append(HRFlowable(width=W,thickness=0.5,color=colors.HexColor("#b7d9c5"),spaceAfter=2))
        story.append(Paragraph("Investigations for Next Visit",S["sec"]))
        story.append(Paragraph(rec["Lab_Tests"],S["n"]))
    if rec.get("Followup_Date"):
        story.append(Paragraph(f"<b>Next Visit:</b>  {rec['Followup_Date']}",S["bd"]))
    if rec.get("Instructions"):
        story.append(HRFlowable(width=W,thickness=0.5,color=colors.HexColor("#b7d9c5"),spaceAfter=2))
        story.append(Paragraph("Instructions / Pathya",S["sec"]))
        for line in rec["Instructions"].split("\n"):
            if line.strip(): story.append(Paragraph(f"  {line.strip()}",S["ins"]))
    # Signature
    story.append(Spacer(1,8*mm))
    story.append(HRFlowable(width=W,thickness=0.4,color=GY,spaceAfter=3))
    sd=[[Paragraph("Reg. No.:  _______________________",S["sL"]),
         Paragraph(f"<b>{rec.get('Physician','')}</b>",S["sR"])],
        [Paragraph("Date: ________________",S["sL"]),Paragraph("MD (Ayurveda)",S["sR"])],
        [Paragraph("",S["sL"]),Paragraph("Signature &amp; Stamp",S["sR"])]]
    st2=Table(sd,colWidths=[W/2,W/2])
    st2.setStyle(TableStyle([("FONTSIZE",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),2)]))
    story.append(st2)
    story.append(Spacer(1,4*mm))
    story.append(HRFlowable(width=W,thickness=0.8,color=GOLD,spaceAfter=1))
    story.append(HRFlowable(width=W,thickness=0.3,color=GY,spaceAfter=2))
    story.append(Paragraph("Conceptized by: Dr. Kiran M Goud, MD (Ay.)  |  Developed by: Dr. Prasanna Kulkarni, MD (Ay.), MS (Data Science)  |  ACD: Namaste Portal  |  SAT-I: WHO",S["ft"]))
    doc.build(story); buf.seek(0); return buf

# ─────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────
_defs = {"logged_in":False,"user_role":None,"user_name":None,
         "last_activity":None,"force_pin_change":False,
         "records":[],"active_rec":{},"pid_counter":1,"med_count":1,
         "gs_ok":False,"ws_opd":None,"ws_phys":None,
         "gs_phys_loaded":False,"gs_records_loaded":False}
for k,v in _defs.items():
    if k not in st.session_state: st.session_state[k]=v
for cat in ["Purvakarma","Pradhana Karma","Pashchata Karma"]:
    if f"tx_{cat}" not in st.session_state: st.session_state[f"tx_{cat}"]=[]
    if f"tc_{cat}" not in st.session_state: st.session_state[f"tc_{cat}"]={}

# Connect to Google Sheets once
if not st.session_state.gs_ok:
    ws_opd, ws_phys, gs_err = connect_sheets()
    if ws_opd:
        st.session_state.ws_opd  = ws_opd
        st.session_state.ws_phys = ws_phys
        st.session_state.gs_ok   = True
        # Load existing records
        if not st.session_state.gs_records_loaded:
            existing = gs_load(ws_opd)
            if existing: st.session_state.records = existing
            st.session_state.gs_records_loaded = True

# Init pins (with sheet overlay if available)
init_pins()

# ─────────────────────────────────────────────────────────────────
# SESSION TIMEOUT
# ─────────────────────────────────────────────────────────────────
if st.session_state.logged_in and st.session_state.last_activity:
    elapsed = (datetime.now() - st.session_state.last_activity).total_seconds() / 3600
    if elapsed > SESSION_HRS:
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.user_name = None

if st.session_state.logged_in:
    st.session_state.last_activity = datetime.now()

# ─────────────────────────────────────────────────────────────────
# LOGIN SCREEN
# ─────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    st.markdown("""
    <div style='text-align:center;margin-top:30px;'>
      <div style='font-family:Noto Serif,serif;font-size:1.5rem;font-weight:700;color:#1a3a2a'>SKAMCSHRC</div>
      <div style='color:#888;font-size:0.82rem;margin-bottom:6px'>
        Sri Kalabyraveshwara Swamy Ayurvedic Medical College<br>Hospital &amp; Research Centre, Bangalore
      </div>
    </div>
    """, unsafe_allow_html=True)

    lc1, lc2, lc3 = st.columns([1, 1.2, 1])
    with lc2:
        st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">OPD System — Sign In</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Select your name and enter your PIN</div>', unsafe_allow_html=True)

        # Name list — Reception + Admin + all physicians
        login_names = ["— Select your name —", RECEP_NAME, ADMIN_NAME] + \
                      sorted([n for n in ALL_PHYS_NAMES if n != ADMIN_NAME])

        sel = st.selectbox("Your Name", login_names, key="login_sel")
        pin = st.text_input("Your PIN", type="password", max_chars=8,
                            key="login_pin", placeholder="Enter PIN")

        if st.button("Sign In", type="primary", use_container_width=True, key="do_login"):
            if sel == "— Select your name —":
                st.error("Please select your name from the list.")
            elif not pin:
                st.error("Please enter your PIN.")
            else:
                ok, needs_change = check_pin(sel, pin)
                if ok:
                    st.session_state.logged_in      = True
                    st.session_state.user_name      = sel
                    st.session_state.user_role      = get_role(sel)
                    st.session_state.force_pin_change = needs_change
                    st.session_state.last_activity  = datetime.now()
                    st.rerun()
                else:
                    st.error("Incorrect PIN. Please try again.")

        st.markdown("---")
        st.markdown("<div style='font-size:0.72rem;color:#aaa;text-align:center'>"
                    "First time? Default PIN is <b>1234</b><br>"
                    "You'll be asked to set a new PIN after login</div>",
                    unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────
# FORCE PIN CHANGE
# ─────────────────────────────────────────────────────────────────
if st.session_state.force_pin_change:
    st.markdown('<div class="hdr"><h2>SKAMCSHRC OPD</h2></div>', unsafe_allow_html=True)
    st.markdown('<div class="pin-box">', unsafe_allow_html=True)
    st.markdown(f"### Welcome, {st.session_state.user_name}")
    st.warning("You are using the default PIN **1234**. Please set your own personal PIN to continue.")
    pc1, pc2 = st.columns(2)
    with pc1: np1 = st.text_input("New PIN (4-8 digits)", type="password", key="np1", max_chars=8)
    with pc2: np2 = st.text_input("Confirm New PIN",      type="password", key="np2", max_chars=8)
    if st.button("Set PIN & Continue", type="primary", key="set_pin"):
        if not np1 or not np2:
            st.error("Please fill both fields.")
        elif np1 != np2:
            st.error("PINs do not match.")
        elif len(np1) < 4 or not np1.isdigit():
            st.error("PIN must be 4-8 digits.")
        elif np1 == DEFAULT_PHYS_PIN:
            st.error("Please choose a different PIN (not 1234).")
        else:
            save_new_pin(st.session_state.user_name, np1)
            st.session_state.force_pin_change = False
            st.success("PIN set successfully!")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────
# MAIN APP HEADER
# ─────────────────────────────────────────────────────────────────
ROLE = st.session_state.user_role
NAME = st.session_state.user_name

rb = {"Admin":'<span class="rb-admin">ADMIN</span>',
      "Physician":'<span class="rb-phys">PHYSICIAN</span>',
      "Receptionist":'<span class="rb-recep">RECEPTIONIST</span>'}.get(ROLE,"")

st.markdown(f"""
<div class="hdr">
  <h2>SKAMCSHRC — OPD Clinical Data Entry &nbsp;{rb}</h2>
  <p>Logged in as <b>{NAME}</b> &nbsp;|&nbsp;
     {st.session_state.last_activity.strftime('%d %b %Y  %I:%M %p') if st.session_state.last_activity else ''}</p>
</div>
""", unsafe_allow_html=True)

if not ACD_OK:
    st.warning("newACD.xlsx not found — ACD code lookup disabled.")
if not st.session_state.gs_ok:
    st.info("Google Sheets not configured — data saves to session only. Export using the sidebar.")

m1,m2,m3,m4 = st.columns(4)
m1.metric("Date",  date.today().strftime("%d %b %Y"))
m2.metric("Time",  datetime.now().strftime("%I:%M %p"))
today_n = len([r for r in st.session_state.records
               if str(r.get("Visit_Date","")).startswith(str(date.today()))])
m3.metric("Today's Patients", today_n)
m4.metric("Total Records",    len(st.session_state.records))
st.markdown("---")

# ─────────────────────────────────────────────────────────────────
# BUILD TABS BY ROLE
# ─────────────────────────────────────────────────────────────────
if ROLE == "Receptionist":
    tab_labels = ["Register Patient", "Today's Queue"]
elif ROLE == "Physician":
    tab_labels = ["My Patients"]
else:  # Admin
    tab_labels = ["Register Patient", "Today's Queue", "Consultation", "Physician Management"]

tabs = st.tabs(tab_labels)

# ══════════════════════════════════════════════════════════════════
# REGISTRATION TAB (Receptionist + Admin tab[0])
# ══════════════════════════════════════════════════════════════════
def render_registration():
    st.markdown("### Register New / Returning Patient")

    # ── Patient search ──────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("Search Returning Patient")
    s1, s2 = st.columns(2)
    with s1: srch_id  = st.text_input("Search by Patient ID",     key="srch_id",  placeholder="e.g. N260001")
    with s2: srch_mob = st.text_input("Search by Mobile Number",   key="srch_mob", placeholder="10-digit mobile")

    found_v = []
    if srch_id  and len(srch_id)  >= 4:  found_v = find_patient(st.session_state.records, pid=srch_id)
    elif srch_mob and len(srch_mob) == 10: found_v = find_patient(st.session_state.records, mobile=srch_mob)

    ret = st.session_state.get("ret_patient")
    vc  = st.session_state.get("ret_vc", 1)

    if found_v:
        last = found_v[-1]
        new_vc = len(found_v) + 1
        st.success(f"Found: **{last.get('Patient_Name','')}** | ID: {last.get('Patient_ID','')} | "
                   f"Mobile: {last.get('Mobile','')} | Total visits: {len(found_v)} | "
                   f"Last visit: {last.get('Visit_Date','')} | "
                   f"Last Dx: **{last.get('Final_ACD_Code') or last.get('ACD_Code_1','')}** "
                   f"{last.get('Final_ACD_Meaning') or last.get('ACD_Meaning_1','')}")
        if st.button(f"Confirm — Register for Visit #{new_vc}", type="primary", key="conf_ret"):
            st.session_state.ret_patient = last
            st.session_state.ret_vc      = new_vc
            ret = last; vc = new_vc
    elif (srch_id and len(srch_id)>=4) or (srch_mob and len(srch_mob)==10):
        st.info("Not found. Fill the form below to register as a new patient.")
    st.markdown('</div>', unsafe_allow_html=True)

    def pf(f, d): return ret[f] if ret and ret.get(f) else d

    # ── Triage ───────────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("1  Triage")
    triage = st.radio("Priority", ["Routine","Urgent"], index=0, horizontal=True, key="triage")
    if triage == "Urgent":
        st.markdown('<div class="triage-u">URGENT — See immediately</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="triage-r">ROUTINE — Regular queue</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Patient details ──────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("2  Patient Details")

    tk_col, pid_col = st.columns([1, 2])
    with tk_col:
        token = next_token(st.session_state.records)
        st.markdown(f'<div style="background:#2d5a3d;color:#f5e6c8;border-radius:8px;'
                    f'padding:8px 16px;font-weight:700;font-size:1.1rem;display:inline-block">'
                    f'Token: {token}</div>', unsafe_allow_html=True)
    with pid_col:
        pid = st.text_input("Patient ID", value=pf("Patient_ID", auto_pid()), key="pid")

    c1, c2, c3 = st.columns(3)
    with c1:
        pat_name = st.text_input("Patient Name", value=pf("Patient_Name",""), key="pat_name",
                                  placeholder="Full name")
    with c2:
        mobile = st.text_input("Mobile Number (10 digits)", value=pf("Mobile",""),
                                key="mobile", max_chars=10)
        if mobile and not validate_mobile(mobile):
            st.warning("Enter a valid 10-digit mobile number")
    with c3:
        vdate = st.date_input("Visit Date", value=date.today(), key="vdate")

    c4, c5, c6 = st.columns(3)
    with c4:
        age_def = int(pf("Age", 30))
        age     = st.number_input("Age (years)", 0, 120, age_def, key="age")
        gd      = pf("Gender", GENDER_OPT[0])
        gender  = st.selectbox("Gender", GENDER_OPT,
                                index=GENDER_OPT.index(gd) if gd in GENDER_OPT else 0,
                                key="gender")
    with c5:
        vtype    = st.selectbox("Visit Type", ["New Case","Follow Up"],
                                 index=0 if not ret else 1, key="vtype")
        dd       = pf("District", DISTRICT_LIST[0])
        district = st.selectbox("District", DISTRICT_LIST,
                                 index=DISTRICT_LIST.index(dd) if dd in DISTRICT_LIST else 0,
                                 key="district")
    with c6:
        od       = pf("Occupation", OCCUPATION_OPT[0])
        occ      = st.selectbox("Occupation", OCCUPATION_OPT,
                                 index=OCCUPATION_OPT.index(od) if od in OCCUPATION_OPT else 0,
                                 key="occ")
        pk2      = pf("Prakriti", PRAKRITI_OPT[0])
        prakriti = st.selectbox("Prakriti", PRAKRITI_OPT,
                                 index=PRAKRITI_OPT.index(pk2) if pk2 in PRAKRITI_OPT else 0,
                                 key="prakriti")

    lrisk   = st.multiselect("Lifestyle Risk Category", LIFESTYLE_RISK, key="lrisk")
    consent = st.checkbox("Patient / Guardian consents to data collection", key="consent")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Department & Physician ───────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("3  Department & Physician")
    dc1, dc2 = st.columns(2)
    with dc1:
        dept_def  = pf("Department", "")
        dept_keys = list(DEPARTMENTS.keys())
        dk_def    = next((k for k,v in DEPARTMENTS.items() if v==dept_def),
                         st.session_state.get("dept_key","KC"))
        dept_key  = st.selectbox("Department", dept_keys, format_func=dlbl,
                                  index=dept_keys.index(dk_def) if dk_def in dept_keys else 0,
                                  key="dept_sel")
        st.session_state.dept_key = dept_key
    with dc2:
        on_req = st.checkbox("On Request (show all physicians)", key="on_req")

    # Filter physicians by department — using MASTER_PHYSICIANS
    if on_req:
        phys_list = sorted(ALL_PHYS_NAMES)
    else:
        phys_list = sorted([n for n,d in MASTER_PHYSICIANS if dept_key in d])
    if not phys_list: phys_list = sorted(ALL_PHYS_NAMES)

    phys_def  = pf("Physician", phys_list[0])
    physician = st.selectbox("Physician",
                              phys_list,
                              index=phys_list.index(phys_def) if phys_def in phys_list else 0,
                              key="phys_sel")
    phys_depts = PHYS_DEPTS.get(physician, [])
    if phys_depts:
        st.caption(f"{physician} — {' | '.join([dlbl(d) for d in phys_depts])}")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Chief Complaints & Provisional Diagnosis ─────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("4  Chief Complaints & Provisional Diagnosis")
    chief    = st.multiselect("Chief Complaints (select all that apply)",
                               DEPT_CONDITIONS.get(dept_key, []), key="chief")
    other_cc = st.text_input("Additional complaint (free text)", key="other_cc")

    st.markdown("**Provisional Diagnosis 1**")
    _, pc1, pm1 = acd_widget("ps1", "psel1", "Search Diagnosis 1")
    st.markdown("**Provisional Diagnosis 2** (optional)")
    _, pc2, pm2 = acd_widget("ps2", "psel2", "Search Diagnosis 2")

    sc1, sc2 = st.columns(2)
    with sc1: severity = st.selectbox("Severity",         SEVERITY_OPT, key="severity")
    with sc2: duration = st.selectbox("Disease Duration",  DURATION_OPT, key="duration")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Save ─────────────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("5  Save & Send to Physician")
    if st.button("Save Registration", type="primary", use_container_width=True, key="save_rec"):
        if not pat_name.strip():
            st.error("Please enter patient name.")
        elif mobile and not validate_mobile(mobile):
            st.error("Please enter a valid 10-digit mobile number.")
        else:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rec = {
                "Patient_ID":pid, "Patient_Name":pat_name.strip(), "Mobile":mobile,
                "Token_No":token, "Visit_Date":str(vdate),
                "Visit_Time":datetime.now().strftime("%H:%M:%S"),
                "Visit_DateTime":ts, "Visit_Count":vc,
                "Visit_Type":vtype, "Age":age, "Gender":gender,
                "District":district, "Occupation":occ, "Prakriti":prakriti,
                "Lifestyle_Risk":", ".join(lrisk) if lrisk else "",
                "Triage":triage, "Department":dlbl(dept_key), "Physician":physician,
                "Status":"Awaiting Physician",
                "Consent":"Yes" if consent else "No",
                "Chief_Complaints":", ".join(chief)+(f"; {other_cc}" if other_cc else ""),
                "ACD_Code_1":pc1, "ACD_Meaning_1":pm1,
                "ACD_Code_2":pc2, "ACD_Meaning_2":pm2,
                "Severity":severity, "Disease_Duration":duration,
                # Physician fields (empty until consultation)
                **{f: "" for f in ["Height_cm","Weight_kg","BMI","BMI_Category",
                                    "BP","Pulse_bpm","Temp_F","SpO2_pct","RR_per_min",
                                    "Other_Investigation","Nadi","Jihva","Agni","Mala",
                                    "Mutra","Sleep","Shabda","Sparsha","Drik","Akriti",
                                    "Dosha","Dushya","Bala","Kala","Satva","Satmya",
                                    "Vyasana","Prakriti_Confirmed","Final_ACD_Code",
                                    "Final_ACD_Meaning","Treatment_Response",
                                    "TX_Purvakarma","TX_Pradhana_Karma","TX_Pashchata_Karma",
                                    "TX_Comments_Purvakarma","TX_Comments_Pradhana",
                                    "TX_Comments_Pashchata","TX_Custom","Medicines_Summary",
                                    "Lab_Tests","Followup_Date","Instructions",
                                    "Physician_Notes","Followup_Notes"]},
            }
            st.session_state.records.append(rec)
            ws = st.session_state.get("ws_opd")
            if ws: gs_upsert(ws, rec, ["Patient_ID","Visit_DateTime"])
            if not ret: st.session_state.pid_counter += 1
            reset_form()
            st.success(f"Registered — **{pat_name}** | Token **{token}** | "
                       f"Assigned to **{physician}** | Visit #{vc}")
            st.info("Patient is now visible in the physician's queue.")
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# QUEUE TAB (Receptionist + Admin)
# ══════════════════════════════════════════════════════════════════
def render_queue():
    st.markdown("### Today's Patient Queue")
    today = str(date.today())
    tr = [r for r in st.session_state.records if str(r.get("Visit_Date","")).startswith(today)]

    if not tr:
        st.info("No patients registered today yet.")
        return

    total  = len(tr)
    urgent = len([r for r in tr if r.get("Triage")=="Urgent"])
    wait   = len([r for r in tr if r.get("Status","")=="Awaiting Physician"])
    done   = len([r for r in tr if r.get("Status","")=="Completed"])

    q1,q2,q3,q4 = st.columns(4)
    q1.metric("Total Today",        total)
    q2.metric("Urgent",             urgent)
    q3.metric("Awaiting Physician", wait)
    q4.metric("Completed",          done)
    st.markdown("---")

    phys_today = sorted(set(r.get("Physician","") for r in tr if r.get("Physician","")))
    for phys in phys_today:
        pr = [r for r in tr if r.get("Physician","")==phys]
        # Sort: urgent first, then by token
        pr_sorted = sorted(pr, key=lambda x: (x.get("Triage","")!="Urgent", x.get("Token_No","")))
        wc = len([r for r in pr if r.get("Status","")!="Completed"])
        dc = len([r for r in pr if r.get("Status","")=="Completed"])
        with st.expander(f"{phys}  —  {len(pr)} patients  "
                         f"({wc} waiting, {dc} done)", expanded=True):
            for r in pr_sorted:
                status = r.get("Status","Awaiting Physician")
                triage = r.get("Triage","Routine")
                css = "q-urgent" if triage=="Urgent" else \
                      ("q-done"   if status=="Completed"      else "q-wait")
                icon = "🔴 " if triage=="Urgent" else ("✓ " if status=="Completed" else "⏳ ")
                st.markdown(
                    f'<div class="{css}">'
                    f'{icon}<b>{r.get("Token_No","")}</b> &nbsp;|&nbsp; '
                    f'{r.get("Patient_Name","")} &nbsp;|&nbsp; '
                    f'{r.get("Age","")} yrs / {r.get("Gender","")} &nbsp;|&nbsp; '
                    f'<span style="font-family:monospace;font-weight:700">{r.get("ACD_Code_1","")}</span>'
                    f' &nbsp;|&nbsp; {status}'
                    f'</div>', unsafe_allow_html=True)

                # Admin can reassign
                if ROLE == "Admin":
                    with st.form(key=f"ra_{r.get('Token_No','')}_{r.get('Visit_DateTime','')}"):
                        new_p = st.selectbox("Reassign to", sorted(ALL_PHYS_NAMES),
                                              index=sorted(ALL_PHYS_NAMES).index(r.get("Physician","")) \
                                                    if r.get("Physician","") in ALL_PHYS_NAMES else 0,
                                              key=f"rp_{r.get('Token_No','')}")
                        if st.form_submit_button("Reassign"):
                            for i,r2 in enumerate(st.session_state.records):
                                if r2.get("Visit_DateTime")==r.get("Visit_DateTime"):
                                    st.session_state.records[i]["Physician"] = new_p
                                    ws = st.session_state.get("ws_opd")
                                    if ws: gs_upsert(ws, st.session_state.records[i],
                                                     ["Patient_ID","Visit_DateTime"])
                            st.success(f"Reassigned to {new_p}")
                            st.rerun()

# ══════════════════════════════════════════════════════════════════
# CONSULTATION TAB (Physician + Admin)
# ══════════════════════════════════════════════════════════════════
def render_consultation():
    st.markdown(f"### Consultation — {NAME}")

    # Physician sees their own records; Admin sees all
    if ROLE == "Physician":
        my_recs = [r for r in st.session_state.records if r.get("Physician","") == NAME]
    else:
        my_recs = st.session_state.records

    rec = st.session_state.get("active_rec", {})

    if not rec:
        # ── Load patient ────────────────────────────────────────
        st.info("Select a patient to consult.")

        # Today's pending cases for this physician
        today = str(date.today())
        pending = [r for r in my_recs
                   if str(r.get("Visit_Date","")).startswith(today)
                   and r.get("Status","") in ("Awaiting Physician","")]
        pending_sorted = sorted(pending,
                                 key=lambda x: (x.get("Triage","")!="Urgent", x.get("Token_No","")))

        if pending_sorted:
            st.markdown("#### Today's Pending Patients")
            for p in pending_sorted:
                col_a, col_b = st.columns([5,1])
                with col_a:
                    urg = "🔴 URGENT — " if p.get("Triage")=="Urgent" else ""
                    st.markdown(
                        f'<div class="{"q-urgent" if p.get("Triage")==str("Urgent") else "q-wait"}">'
                        f'{urg}<b>{p.get("Token_No","")}</b> &nbsp;—&nbsp; '
                        f'<b>{p.get("Patient_Name","")}</b> &nbsp;|&nbsp; '
                        f'{p.get("Age","")} yrs / {p.get("Gender","")} &nbsp;|&nbsp; '
                        f'{p.get("Chief_Complaints","")[:60]}'
                        f'</div>', unsafe_allow_html=True)
                with col_b:
                    if st.button("Open", key=f"op_{p.get('Token_No','')}_{p.get('Visit_DateTime','')}"):
                        st.session_state.active_rec = dict(p)
                        st.rerun()

        st.markdown("---")
        # Search by ID or mobile
        lc1, lc2 = st.columns(2)
        with lc1: lid  = st.text_input("Load by Patient ID",     key="lid_t2")
        with lc2: lmob = st.text_input("Load by Mobile Number",   key="lmob_t2")
        if lid or lmob:
            found = find_patient(my_recs,
                                  pid=lid if lid else None,
                                  mobile=lmob if lmob else None)
            if found:
                st.session_state.active_rec = dict(found[-1])
                st.rerun()
            else:
                st.warning("Patient not found in your case list.")
        return

    # ── Active patient ──────────────────────────────────────────
    # Follow-up notes from previous visits
    prev_fu = sorted(
        [r for r in my_recs
         if r.get("Patient_ID")==rec.get("Patient_ID")
         and r.get("Visit_DateTime")!=rec.get("Visit_DateTime")
         and str(r.get("Followup_Notes","")).strip()],
        key=lambda x: x.get("Visit_DateTime",""))
    if prev_fu:
        last = prev_fu[-1]
        st.markdown(
            f'<div class="fu-box"><h4>Follow-up Notes from last visit '
            f'({last.get("Visit_Date","")} — '
            f'{last.get("Final_ACD_Code") or last.get("ACD_Code_1","")})</h4>'
            f'<p>{str(last.get("Followup_Notes","")).replace(chr(10),"<br>")}</p></div>',
            unsafe_allow_html=True)

    # Patient summary banner
    with st.expander("Patient Details", expanded=True):
        b1,b2,b3,b4,b5 = st.columns(5)
        b1.metric("Name",    rec.get("Patient_Name",""))
        b2.metric("Token",   rec.get("Token_No",""))
        b3.metric("Age/Sex", f"{rec.get('Age','')} / {rec.get('Gender','')}")
        b4.metric("Visit #", rec.get("Visit_Count","1"))
        b5.metric("Triage",  rec.get("Triage",""))
        st.write(f"**ID:** {rec.get('Patient_ID','')} | **Mobile:** {rec.get('Mobile','')} | "
                 f"**Dept:** {rec.get('Department','')} | **Prakriti:** {rec.get('Prakriti','')}")
        if rec.get("Chief_Complaints"):
            st.write(f"**Chief Complaints:** {rec['Chief_Complaints']}")
        if rec.get("ACD_Code_1"):
            st.markdown(f'**Provisional Dx:** <span class="code-tag">{rec["ACD_Code_1"]}</span> '
                        f'{rec.get("ACD_Meaning_1","")}', unsafe_allow_html=True)
        if st.button("Close / Load different patient", key="close_rec"):
            st.session_state.active_rec = {}
            st.rerun()

    # Treatment response (follow-ups)
    if str(rec.get("Visit_Count","1")) != "1":
        st.markdown('<div class="card">', unsafe_allow_html=True)
        sec("Response to Previous Treatment")
        tr_def = rec.get("Treatment_Response", TREATMENT_RESPONSE[0])
        tr_idx = TREATMENT_RESPONSE.index(tr_def) if tr_def in TREATMENT_RESPONSE else 0
        treatment_response = st.selectbox("How did patient respond?",
                                           TREATMENT_RESPONSE, index=tr_idx, key="tr")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        treatment_response = "Not yet assessed"

    # Vitals
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("1  Vitals")
    v1,v2,v3 = st.columns(3)
    with v1:
        height = st.number_input("Height (cm)",  50.0, 250.0, 160.0, step=1.0, key="ht")
        weight = st.number_input("Weight (kg)",  1.0,  300.0, 50.0,  step=0.5, key="wt")
        bmi_v  = weight / ((height/100)**2) if height > 0 else 0
        bmi_c  = bmi_cat(bmi_v)
        st.markdown(f'<div class="bmi">BMI: {bmi_v:.1f} — {bmi_c}</div>', unsafe_allow_html=True)
    with v2:
        bp_s = st.number_input("BP Systolic (mmHg)",  60,  250, 120, step=1, key="bps")
        bp_d = st.number_input("BP Diastolic (mmHg)", 40,  160,  80, step=1, key="bpd")
    with v3:
        pulse = st.number_input("Pulse (bpm)",       30, 220, 76,   step=1,   key="pulse")
        temp  = st.number_input("Temperature (F)",   90.0, 108.0, 98.6, step=0.1, key="temp")
    vv4,vv5 = st.columns(2)
    with vv4: spo2 = st.number_input("SpO2 (%)",          50, 100, 98, step=1, key="spo2")
    with vv5: rr   = st.number_input("Resp. Rate (/min)",  5,  60, 16, step=1, key="rr")
    other_inv = st.text_area("Lab Reports / Other Investigations", key="other_inv", height=50,
                              placeholder="e.g. Hb 11.2 g/dL; FBS 126 mg/dL; X-ray: Disc prolapse L4-L5")
    st.markdown('</div>', unsafe_allow_html=True)

    # Ashtavidha Pariksha
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("2  Ashtavidha Pariksha")
    a1,a2,a3,a4 = st.columns(4)
    with a1: nadi=sel_other("Nadi",   NADI_OPT,   "nadi");  jihva=sel_other("Jihva",  JIHVA_OPT, "jihva")
    with a2: agni=sel_other("Agni",   AGNI_OPT,   "agni");  mala =sel_other("Mala",   MALA_OPT,  "mala")
    with a3: mutra=sel_other("Mutra", MUTRA_OPT,  "mutra"); sleep=sel_other("Nidra",  SLEEP_OPT, "sleep")
    with a4: shabda=sel_other("Shabda",SHABDA_OPT,"shabda");sparsha=sel_other("Sparsha",SPARSHA_OPT,"sparsha")
    aa5,aa6 = st.columns(2)
    with aa5: drik  =sel_other("Drik",  DRIK_OPT,  "drik")
    with aa6: akriti=sel_other("Akriti",AKRITI_OPT,"akriti")
    st.markdown('</div>', unsafe_allow_html=True)

    # Dashavidha Pariksha
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("3  Dashavidha Atura Pariksha")
    d1,d2,d3 = st.columns(3)
    with d1:
        dosha  = sel_other("Dosha (Dominant)", DOSHA_OPT, "dosha")
        dushya = st.multiselect("Dushya (Dhatu / Mala)", DUSHYA_OPT, key="dushya")
        bala   = sel_other("Bala (Strength)",  BALA_OPT,  "bala")
    with d2:
        kala   = st.selectbox("Kala (Season)", KALA_OPT,   key="kala")
        satva  = sel_other("Satva",            SATVA_OPT,  "satva")
        satmya = sel_other("Satmya",           SATMYA_OPT, "satmya")
    with d3:
        vyasana = sel_other("Vyasana (Habits)", VYASANA_OPT, "vyasana")
        cprak   = st.selectbox("Prakriti (confirm)", PRAKRITI_OPT,
                                index=PRAKRITI_OPT.index(rec.get("Prakriti", PRAKRITI_OPT[0]))
                                      if rec.get("Prakriti") in PRAKRITI_OPT else 0,
                                key="cprak")
    st.markdown('</div>', unsafe_allow_html=True)

    # Final Diagnosis
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("4  Final Diagnosis")
    pcode = rec.get("ACD_Code_1",""); pmean = rec.get("ACD_Meaning_1","")
    if pcode:
        st.markdown(f"Provisional: <span class='code-tag'>{pcode}</span> — {pmean}",
                    unsafe_allow_html=True)
    _, fd_code, fd_mean = acd_widget("fds","fdsel","Search Final Diagnosis")
    if st.checkbox("Same as Provisional", key="same_prov") and pcode:
        fd_code = pcode; fd_mean = pmean
        st.markdown(f'<span class="code-tag">{fd_code}</span>  {fd_mean}',
                    unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Panchakarma
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("5  Panchakarma Treatment Plan (optional)")

    # Running summary
    sp = []
    for cat in ["Purvakarma","Pradhana Karma","Pashchata Karma"]:
        s = st.session_state.get(f"tx_{cat}", [])
        if s: sp.append(f"<b>{cat}:</b> {', '.join([x.split(' — ')[0] for x in s])}")
    if sp:
        st.markdown('<div class="tx-box">'+"<br>".join(sp)+"</div>", unsafe_allow_html=True)

    tx_tabs = st.tabs(["Purvakarma","Pradhana Karma","Pashchata Karma"])
    for cat, ttab in zip(["Purvakarma","Pradhana Karma","Pashchata Karma"], tx_tabs):
        with ttab:
            opts = [f"{nm} — {desc} [{cd}]" for cd,nm,desc in PK_TX[cat]]
            cur  = [c for c in st.session_state.get(f"tx_{cat}",[]) if c in opts]
            chosen = st.multiselect(f"Select {cat} procedures", opts, default=cur,
                                     key=f"tx_ms_{cat}")
            st.session_state[f"tx_{cat}"] = chosen
            if chosen:
                st.markdown("**Add comments for each procedure:**")
                ex = st.session_state.get(f"tc_{cat}", {}); nc = {}
                for tx in chosen:
                    code = xcode(tx); name = tx.split(" — ")[0] if " — " in tx else tx
                    st.markdown(f'<div style="background:#f0fff4;border-left:3px solid #2d6a4f;'
                                f'border-radius:0 7px 7px 0;padding:6px 12px;margin:4px 0">',
                                unsafe_allow_html=True)
                    cmt = st.text_input(f"{name}  [{code}]", value=ex.get(code,""),
                                         key=f"tc_{cat}_{code}",
                                         placeholder="e.g. with Dhanwantaram taila 45 min daily x 7 days")
                    st.markdown('</div>', unsafe_allow_html=True)
                    nc[code] = cmt
                st.session_state[f"tc_{cat}"] = nc

    tx_custom = st.text_input("Additional treatment / Yoga / Pathya", key="tx_custom",
                               placeholder="e.g. Pathya Ahara, Yoga Nidra")
    st.markdown('</div>', unsafe_allow_html=True)

    # Shamana Aushadhi
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("6  Medicines (Shamana Aushadhi)")
    ac, rc, _ = st.columns([1,1,5])
    with ac:
        if st.button("+ Add Medicine", key="add_med"):
            st.session_state.med_count += 1; st.rerun()
    with rc:
        if st.session_state.med_count > 1 and st.button("- Remove Last", key="rem_med"):
            st.session_state.med_count -= 1; st.rerun()

    medicines = []
    for i in range(1, st.session_state.med_count+1):
        st.markdown(f'<div class="med-box"><b>Medicine {i}</b>', unsafe_allow_html=True)
        r1a,r1b,r1c = st.columns([3,2,2])
        with r1a: mname  = st.text_input(f"Drug Name {i}", key=f"mn_{i}",
                                          placeholder="e.g. Triphala Churna, Ashwagandha Vati")
        with r1b: mform  = csel(f"Dosage Form {i}", DOSAGE_FORMS, f"mf_{i}")
        with r1c: mroute = csel(f"Route {i}",        ROUTE_OPTIONS, f"mr_{i}", idx=0)

        r2a,r2b,r2c,r2d,r2e = st.columns([2,2,2,1,1])
        with r2a: mdose  = csel(f"Dose {i}",    DOSE_OPTIONS,    f"md_{i}",  ph="e.g. 5g BD")
        with r2b: mtiming = st.selectbox(f"Timing {i}", TIMING_OPTIONS, key=f"mt_{i}")
        with r2c: manupana = csel(f"Anupana {i}", ANUPANA_OPTIONS, f"ma_{i}", idx=0)
        with r2d: mdur_val = st.number_input(f"Duration {i}", 1, 999, 15, step=1, key=f"mdv_{i}")
        with r2e: mdur_unit= st.selectbox(f"Unit {i}", DURATION_UNIT, key=f"mdu_{i}")

        preview = {"form":mform,"dose":mdose,"timing":mtiming,"anupana":manupana,
                   "dur_val":mdur_val,"dur_unit":mdur_unit,"notes":""}
        if mdose and mdose != "— Custom —":
            st.caption(f"Instruction preview: {med_instruction(preview)}")

        mnotes = st.text_input(f"Notes for Medicine {i} (optional)", key=f"mno_{i}",
                                placeholder="e.g. take warm, avoid in pregnancy")
        st.markdown('</div>', unsafe_allow_html=True)
        if mname.strip():
            medicines.append({"name":mname,"form":mform,"route":mroute,"dose":mdose,
                               "timing":mtiming,"anupana":manupana,
                               "dur_val":mdur_val,"dur_unit":mdur_unit,"notes":mnotes})

    st.markdown('</div>', unsafe_allow_html=True)

    # Lab tests + Follow-up
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("7  Lab Tests & Follow-up Date")
    l1, l2 = st.columns([3,1])
    with l1:
        lab_tests = st.text_area("Tests to be done before next visit", key="lab_tests",
                                  height=50, placeholder="e.g. CBC, FBS, HbA1c, Lipid profile")
    with l2:
        followup_date = st.date_input("Next Visit Date",
                                       value=date.today()+timedelta(days=15), key="fu_date")
        st.caption("Default: 15 days")
    st.markdown('</div>', unsafe_allow_html=True)

    # Instructions
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("8  Instructions for Patient (optional)")
    instructions = st.text_area("Dietary advice, lifestyle, precautions", key="instruct",
                                  height=70,
                                  placeholder="e.g. Avoid cold and oily food\nDrink warm water throughout the day\nRest adequately")
    st.markdown('</div>', unsafe_allow_html=True)

    # Notes
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("9  Physician Notes")
    phys_notes = st.text_area("Clinical notes (for records)", key="phys_notes", height=50,
                               placeholder="Referrals, special observations, clinical notes...")
    followup_notes = st.text_area("Follow-up reminder (visible at patient's next visit)",
                                   key="fu_notes", height=55,
                                   placeholder="e.g. Check BP response\nReview HbA1c\nAssess Sneha Pana tolerance before Virechana")
    st.markdown('</div>', unsafe_allow_html=True)

    # Save + PDF
    st.markdown('<div class="card">', unsafe_allow_html=True)
    sec("10  Save & Print Prescription")

    def build_full():
        tx_pur = st.session_state.get("tx_Purvakarma",[])
        tx_pra = st.session_state.get("tx_Pradhana Karma",[])
        tx_pas = st.session_state.get("tx_Pashchata Karma",[])
        tc_pur = st.session_state.get("tc_Purvakarma",{})
        tc_pra = st.session_state.get("tc_Pradhana Karma",{})
        tc_pas = st.session_state.get("tc_Pashchata Karma",{})
        r = dict(rec)
        r["tx_Purvakarma"]    = tx_pur; r["tx_Pradhana Karma"] = tx_pra; r["tx_Pashchata Karma"] = tx_pas
        r["tc_Purvakarma"]    = tc_pur; r["tc_Pradhana Karma"] = tc_pra; r["tc_Pashchata Karma"] = tc_pas
        r["TX_Custom"]        = st.session_state.get("tx_custom","")
        r["Medicines"]        = medicines
        r["Lab_Tests"]        = st.session_state.get("lab_tests","")
        r["Instructions"]     = st.session_state.get("instruct","")
        r["Followup_Date"]    = str(st.session_state.get("fu_date",""))
        r["Physician_Notes"]  = st.session_state.get("phys_notes","")
        r["Followup_Notes"]   = st.session_state.get("fu_notes","")
        r["Height_cm"]  = st.session_state.get("ht",0)
        r["Weight_kg"]  = st.session_state.get("wt",0)
        r["BMI"]        = round(bmi_v,1); r["BMI_Category"] = bmi_c
        r["BP"]         = f"{st.session_state.get('bps',120)}/{st.session_state.get('bpd',80)}"
        r["Pulse_bpm"]  = st.session_state.get("pulse",76)
        r["Temp_F"]     = st.session_state.get("temp",98.6)
        r["SpO2_pct"]   = st.session_state.get("spo2",98)
        sp = st.session_state.get("same_prov", False)
        if sp:      r["Final_ACD_Code"]=pcode; r["Final_ACD_Meaning"]=pmean
        elif fd_code: r["Final_ACD_Code"]=fd_code; r["Final_ACD_Meaning"]=fd_mean
        return r

    def cmt_flat(sel, cmt):
        return "; ".join([f"{xcode(t)}: {cmt.get(xcode(t),'')}" for t in sel if cmt.get(xcode(t))])

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        if st.button("Save Consultation", type="primary", use_container_width=True, key="save_cons"):
            r = build_full()
            tx_pur = st.session_state.get("tx_Purvakarma",[])
            tx_pra = st.session_state.get("tx_Pradhana Karma",[])
            tx_pas = st.session_state.get("tx_Pashchata Karma",[])
            tc_pur = st.session_state.get("tc_Purvakarma",{})
            tc_pra = st.session_state.get("tc_Pradhana Karma",{})
            tc_pas = st.session_state.get("tc_Pashchata Karma",{})
            med_sum = "; ".join([f"{m['name']} {m['form']} {m['dose']} {m['timing']} "
                                  f"x{m['dur_val']} {m['dur_unit']} | Anupana:{m['anupana']}"
                                  for m in medicines])
            sp = st.session_state.get("same_prov",False)
            upd = {
                "Status":"Completed","Treatment_Response":treatment_response,
                "Height_cm":r["Height_cm"],"Weight_kg":r["Weight_kg"],
                "BMI":r["BMI"],"BMI_Category":r["BMI_Category"],
                "BP":r["BP"],"Pulse_bpm":r["Pulse_bpm"],"Temp_F":r["Temp_F"],
                "SpO2_pct":r["SpO2_pct"],"RR_per_min":st.session_state.get("rr",16),
                "Other_Investigation":st.session_state.get("other_inv",""),
                "Nadi":nadi,"Jihva":jihva,"Agni":agni,"Mala":mala,
                "Mutra":mutra,"Sleep":sleep,"Shabda":shabda,"Sparsha":sparsha,
                "Drik":drik,"Akriti":akriti,"Dosha":dosha,
                "Dushya":", ".join(dushya) if dushya else "",
                "Bala":bala,"Kala":kala,"Satva":satva,"Satmya":satmya,
                "Vyasana":vyasana,"Prakriti_Confirmed":cprak,
                "Final_ACD_Code":  pcode if sp else (fd_code or ""),
                "Final_ACD_Meaning":pmean if sp else (fd_mean or ""),
                "TX_Purvakarma":    "; ".join([s.split(" — ")[0] for s in tx_pur]),
                "TX_Pradhana_Karma":"; ".join([s.split(" — ")[0] for s in tx_pra]),
                "TX_Pashchata_Karma":"; ".join([s.split(" — ")[0] for s in tx_pas]),
                "TX_Comments_Purvakarma":cmt_flat(tx_pur,tc_pur),
                "TX_Comments_Pradhana":  cmt_flat(tx_pra,tc_pra),
                "TX_Comments_Pashchata": cmt_flat(tx_pas,tc_pas),
                "TX_Custom":st.session_state.get("tx_custom",""),
                "Medicines_Summary":med_sum,
                "Lab_Tests":st.session_state.get("lab_tests",""),
                "Instructions":st.session_state.get("instruct",""),
                "Followup_Date":str(st.session_state.get("fu_date","")),
                "Physician_Notes":st.session_state.get("phys_notes",""),
                "Followup_Notes":st.session_state.get("fu_notes",""),
            }
            rec.update(upd)
            for i, r2 in enumerate(st.session_state.records):
                if (r2.get("Patient_ID")==rec.get("Patient_ID") and
                    r2.get("Visit_DateTime")==rec.get("Visit_DateTime")):
                    st.session_state.records[i] = rec; break
            ws = st.session_state.get("ws_opd")
            if ws: gs_upsert(ws, rec, ["Patient_ID","Visit_DateTime"])
            st.success(f"Saved — {rec.get('Patient_Name','')} | "
                       f"Final Dx: {upd['Final_ACD_Code'] or '(not set)'}")
            reset_form()
            st.session_state.pid_counter += 1
            st.rerun()

    with s2:
        r_rx = build_full()
        pdf_rx = make_pdf(r_rx, mode="rx")
        st.download_button("Prescription", data=pdf_rx,
                            file_name=f"Rx_{rec.get('Patient_ID','PT')}_{date.today()}.pdf",
                            mime="application/pdf", key="dl_rx",
                            use_container_width=True)
    with s3:
        has_pk = any(st.session_state.get(f"tx_{c}",[])
                     for c in ["Purvakarma","Pradhana Karma","Pashchata Karma"])
        if has_pk:
            r_pk = build_full()
            pdf_pk = make_pdf(r_pk, mode="pk")
            st.download_button("PK Advice", data=pdf_pk,
                                file_name=f"PK_{rec.get('Patient_ID','PT')}_{date.today()}.pdf",
                                mime="application/pdf", key="dl_pk",
                                use_container_width=True)
        else:
            st.button("PK Advice", disabled=True, use_container_width=True,
                      help="Select Panchakarma procedures first")
    with s4:
        r_both = build_full()
        pdf_both = make_pdf(r_both, mode="both")
        st.download_button("Full Document", data=pdf_both,
                            file_name=f"Full_{rec.get('Patient_ID','PT')}_{date.today()}.pdf",
                            mime="application/pdf", key="dl_both",
                            use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PHYSICIAN MANAGEMENT (Admin only)
# ══════════════════════════════════════════════════════════════════
def render_phys_mgmt():
    st.markdown("### Physician Management")
    pm1, pm2 = st.tabs(["View & Manage", "Add New"])

    with pm1:
        st.markdown("#### All Physicians")
        pin_store = st.session_state.get("pin_store", {})
        for name, _ in sorted(MASTER_PHYSICIANS, key=lambda x: x[0]):
            entry = pin_store.get(name, {})
            pin_set = entry.get("set", False)
            c1,c2,c3 = st.columns([4,2,1])
            with c1:
                depts = ", ".join(PHYS_DEPTS.get(name,[]))
                st.markdown(f"**{name}** — {depts}")
            with c2:
                st.caption("PIN set ✓" if pin_set else "⚠️ Using default PIN 1234")
            with c3:
                if st.button("Reset PIN", key=f"rp_{name}"):
                    st.session_state.pin_store[name] = {"hash": hp(DEFAULT_PHYS_PIN), "set": False}
                    ws_phys = st.session_state.get("ws_phys")
                    if ws_phys:
                        gs_upsert(ws_phys,
                                  {"Name":name,"PIN_Hash":hp(DEFAULT_PHYS_PIN),"PIN_Set":"No",
                                   "Added_Date":str(date.today()),"Active":"Yes","Extra_Depts":""},
                                  ["Name"])
                    st.success(f"PIN reset to 1234 for {name}")

        # Admin PIN management
        st.markdown("---")
        st.markdown("#### Change Your Own PIN")
        op1,op2 = st.columns(2)
        with op1: ap1 = st.text_input("New PIN", type="password", key="ap1", max_chars=8)
        with op2: ap2 = st.text_input("Confirm", type="password", key="ap2", max_chars=8)
        if st.button("Change Admin PIN", key="chg_admin"):
            if ap1 != ap2: st.error("PINs do not match.")
            elif len(ap1)<4 or not ap1.isdigit(): st.error("PIN must be 4-8 digits.")
            else:
                save_new_pin(NAME, ap1)
                st.success("PIN changed successfully.")

    with pm2:
        st.markdown("#### Add New Physician to PIN System")
        st.info("Note: To add to the department list permanently, contact the developer. "
                "This sets a PIN for an existing or new physician name.")
        nc1,nc2 = st.columns(2)
        with nc1: new_name = st.text_input("Full Name", key="new_nm", placeholder="e.g. Dr. Ramesh Kumar")
        with nc2: new_pin  = st.text_input("Initial PIN", type="password", key="new_p", max_chars=8)
        if st.button("Add Physician", type="primary", key="add_phys"):
            if not new_name.strip(): st.error("Enter a name.")
            elif not new_pin or len(new_pin)<4 or not new_pin.isdigit(): st.error("PIN must be 4-8 digits.")
            else:
                save_new_pin(new_name.strip(), new_pin)
                st.success(f"Added {new_name.strip()} with custom PIN.")

# ─────────────────────────────────────────────────────────────────
# ROUTE TABS
# ─────────────────────────────────────────────────────────────────
if ROLE == "Receptionist":
    with tabs[0]: render_registration()
    with tabs[1]: render_queue()

elif ROLE == "Physician":
    with tabs[0]: render_consultation()

else:  # Admin
    with tabs[0]: render_registration()
    with tabs[1]: render_queue()
    with tabs[2]: render_consultation()
    with tabs[3]: render_phys_mgmt()

# ─────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### SKAMCSHRC OPD v10.0")
    rb_css = {"Admin":"rb-admin","Physician":"rb-phys","Receptionist":"rb-recep"}.get(ROLE,"")
    st.markdown(f'<span class="{rb_css}">{ROLE}</span> &nbsp; <b>{NAME}</b>',
                unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.72rem;color:#888;margin-top:4px'>"
        "Conceptized: Dr. Kiran M Goud, MD (Ay.)<br>"
        "Developed: Dr. Prasanna Kulkarni, MD (Ay.), MS (DS)"
        "</div>", unsafe_allow_html=True)

    if st.session_state.gs_ok:
        st.success("Google Sheets connected")
    else:
        st.warning("Session-only mode")

    if st.button("Logout / Switch User", use_container_width=True, key="logout"):
        for k in ["logged_in","user_role","user_name","force_pin_change","last_activity","active_rec"]:
            st.session_state[k] = False if k=="logged_in" else None
        reset_form()
        st.rerun()

    st.markdown("---")
    st.markdown("### Quick Patient Search")
    qs = st.text_input("Patient ID or Mobile", key="qs")
    if qs:
        recs = st.session_state.records
        if ROLE == "Physician": recs = [r for r in recs if r.get("Physician","")==NAME]
        hits = find_patient(recs,
                            pid=qs if not (len(qs)==10 and qs.isdigit()) else None,
                            mobile=qs if len(qs)==10 and qs.isdigit() else None)
        if hits:
            st.success(f"{len(hits)} visit(s)")
            for v in hits[-3:]:
                st.markdown(f"**{v.get('Visit_Date','')}** — "
                            f"`{v.get('Final_ACD_Code') or v.get('ACD_Code_1','')}` "
                            f"{v.get('Department','')}")
        else: st.info("Not found.")

    st.markdown("---")
    st.markdown("### Export Records")

    # Date filter
    ef1,ef2 = st.columns(2)
    with ef1: d_from = st.date_input("From", value=date.today()-timedelta(days=30), key="d_from")
    with ef2: d_to   = st.date_input("To",   value=date.today(), key="d_to")

    # Records to export (physicians see only their own)
    exp_recs = st.session_state.records
    if ROLE == "Physician":
        exp_recs = [r for r in exp_recs if r.get("Physician","") == NAME]

    filtered = [r for r in exp_recs
                if str(d_from) <= str(r.get("Visit_Date","")) <= str(d_to)]
    st.write(f"Filtered: **{len(filtered)} records**")

    if filtered:
        skip = {"tx_Purvakarma","tx_Pradhana Karma","tx_Pashchata Karma",
                "tc_Purvakarma","tc_Pradhana Karma","tc_Pashchata Karma","Medicines"}
        ecols = [c for c in OPD_COLS if c not in skip]
        df_exp = pd.DataFrame([{k: clean(str(r.get(k,""))) for k in ecols} for r in filtered])

        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df_exp.to_excel(w, index=False, sheet_name="OPD_Records")
        buf.seek(0)
        st.download_button("Download Excel", data=buf,
                            file_name=f"SKAMCSHRC_{d_from}_{d_to}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True)
        csv_d = df_exp.to_csv(index=False).encode("utf-8-sig")
        st.download_button("Download CSV", data=csv_d,
                            file_name=f"SKAMCSHRC_{d_from}_{d_to}.csv",
                            mime="text/csv", use_container_width=True)

"""
SKAMCSHRC | OPD Clinical Data Entry System v9.0
Sri Kalabyraveshwara Swamy Ayurvedic Medical College, Hospital & Research Centre

Conceptized by : Dr. Kiran M Goud, MD (Ay.)
Developed by   : Dr. Prasanna Kulkarni, MD (Ay.), MS (Data Science)

DEFAULT PINS (change immediately after first login):
  Admin (Dr. Prasanna)   : 999999
  Reception Desk         : 000000
  All Physicians         : 1234  (forced change on first login)

GOOGLE SHEETS SETUP:
  Three tabs required: OPD_Records | Physicians | Referrals
  App auto-creates all tabs and seeds physician list on first run.

Run : streamlit run skamcmeddata_v9.py
Place newACD.xlsx in the same folder.
"""

import streamlit as st
import pandas as pd
import re, io, hashlib, time
from datetime import date, datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
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
.login-box{max-width:420px;margin:60px auto;background:#f8faf9;
  border:1px solid #d1e5d8;border-radius:14px;padding:36px 40px;
  box-shadow:0 4px 24px rgba(0,0,0,0.08);}
.login-title{color:#1a3a2a;font-family:'Noto Serif',serif;font-size:1.3rem;
  font-weight:700;text-align:center;margin-bottom:4px;}
.login-sub{color:#666;font-size:0.8rem;text-align:center;margin-bottom:22px;}
.role-badge-admin{background:#1a3a2a;color:#f5e6c8;border-radius:6px;
  padding:4px 12px;font-weight:700;font-size:0.8rem;display:inline-block;}
.role-badge-physician{background:#1565c0;color:white;border-radius:6px;
  padding:4px 12px;font-weight:700;font-size:0.8rem;display:inline-block;}
.role-badge-receptionist{background:#2e7d32;color:white;border-radius:6px;
  padding:4px 12px;font-weight:700;font-size:0.8rem;display:inline-block;}
.sec{font-size:0.74rem;font-weight:600;text-transform:uppercase;letter-spacing:1.1px;
  color:#2d6a4f;border-bottom:1px solid #b7d9c5;padding-bottom:5px;margin-bottom:10px;}
.card{background:#f8faf9;border:1px solid #d1e5d8;border-radius:9px;
  padding:14px 17px;margin-bottom:11px;}
.badge{background:#e8f5e9;border:1px solid #81c784;border-radius:4px;
  padding:2px 7px;font-size:0.73rem;font-weight:600;color:#2e7d32;font-family:monospace;}
.code-big{background:#1a3a2a;color:#f5e6c8;border-radius:5px;
  padding:4px 10px;font-size:0.85rem;font-weight:700;font-family:monospace;}
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
.returning-banner{background:#e8f4fd;border:2px solid #2196f3;border-radius:9px;
  padding:12px 16px;margin:8px 0;}
.token-badge{background:#2d5a3d;color:#f5e6c8;border-radius:8px;
  padding:6px 16px;font-size:1.1rem;font-weight:700;display:inline-block;}
.queue-row-urgent{background:#fef3c7;border-left:4px solid #d97706;
  border-radius:6px;padding:8px 12px;margin:4px 0;}
.queue-row-waiting{background:#f0f7f3;border-left:4px solid #2d6a4f;
  border-radius:6px;padding:8px 12px;margin:4px 0;}
.queue-row-done{background:#f5f5f5;border-left:4px solid #999;
  border-radius:6px;padding:8px 12px;margin:4px 0;opacity:0.7;}
.referral-in{background:#e8f4fd;border:1px solid #90caf9;border-radius:8px;
  padding:10px 14px;margin:6px 0;}
.referral-out{background:#f3e5f5;border:1px solid #ce93d8;border-radius:8px;
  padding:10px 14px;margin:6px 0;}
.referral-urgent{border-left:4px solid #d32f2f !important;}
.pin-change-box{background:#fff8e1;border:2px solid #ffc107;border-radius:9px;
  padding:20px;margin:10px 0;}
.stTabs [data-baseweb="tab-list"]{gap:4px;}
.stTabs [data-baseweb="tab"]{height:42px;background:#f0f7f3;border-radius:8px 8px 0 0;
  border:1px solid #c8dfd0;font-weight:500;color:#2d5a3d;font-size:0.86rem;}
.stTabs [aria-selected="true"]{background:#2d5a3d !important;
  color:#f5e6c8 !important;border-color:#2d5a3d !important;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────
DEFAULT_PHYSICIAN_PIN = "1234"
DEFAULT_ADMIN_PIN     = "999999"
DEFAULT_RECEP_PIN     = "000000"
SESSION_TIMEOUT_HRS   = 4
MAX_LOGIN_ATTEMPTS    = 3
LOCKOUT_MINUTES       = 5

def hash_pin(p): return hashlib.sha256(str(p).encode()).hexdigest()

HASH_DEFAULT_PHYS  = hash_pin(DEFAULT_PHYSICIAN_PIN)
HASH_DEFAULT_ADMIN = hash_pin(DEFAULT_ADMIN_PIN)
HASH_DEFAULT_RECEP = hash_pin(DEFAULT_RECEP_PIN)

# ─────────────────────────────────────────────────────────────────
# SHEET COLUMNS
# ─────────────────────────────────────────────────────────────────
OPD_COLS = [
    "Token_No","Patient_ID","Patient_Name","Mobile","Visit_Date","Visit_Time",
    "Visit_DateTime","Visit_Year","Visit_Count","Visit_Type","Consultation_Type",
    "Age","Gender","District","Occupation","Prakriti","Lifestyle_Risk","Triage",
    "Department","Physician","Status","Chief_Complaints","Chief_Complaints_Modified",
    "ACD_Code_1","ACD_Meaning_1","ACD_Code_2","ACD_Meaning_2","Severity","Disease_Duration",
    "Height_cm","Weight_kg","BMI","BMI_Category","BP","Pulse_bpm","Temp_F",
    "SpO2_pct","RR_per_min","Other_Investigation",
    "Nadi","Jihva","Agni","Mala","Mutra","Sleep","Shabda","Sparsha","Drik","Akriti",
    "Dosha","Dushya","Bala","Kala","Satva","Satmya","Vyasana","Prakriti_Confirmed",
    "Final_ACD_Code","Final_ACD_Meaning",
    "TX_Purvakarma","TX_Pradhana_Karma","TX_Pashchata_Karma",
    "TX_Comments_Purvakarma","TX_Comments_Pradhana","TX_Comments_Pashchata","TX_Custom",
    "Medicines_Summary","Lab_Tests","Instructions","Followup_Date",
    "Physician_Notes","Followup_Notes","Treatment_Response","Consent",
]
PHYS_COLS = ["Name","Departments","PIN_Hash","Role","Status","PIN_Changed","Added_Date"]
REF_COLS  = [
    "Referral_ID","Date","Time","From_Physician","From_Dept",
    "To_Physician","To_Dept","Patient_ID","Patient_Name","Token_No",
    "Reason","Priority","Status","Notes","Resolved_Date","Resolved_Notes",
]

# ─────────────────────────────────────────────────────────────────
# SEED PHYSICIAN DATA (hardcoded roster)
# ─────────────────────────────────────────────────────────────────
SEED_PHYSICIANS = [
    ("Dr. Abdul",          "KC,PK"),
    ("Dr. Amrutha",        "KC"),
    ("Dr. Anjali",         "SHALYA"),
    ("Dr. Anupama",        "PRASOOTI,STREE_ROGA"),
    ("Dr. Chaitra N",      "PRASOOTI,STREE_ROGA"),
    ("Dr. Chetana",        "PRASOOTI,STREE_ROGA"),
    ("Dr. Elgeena",        "SPL"),
    ("Dr. Gopal TL",       "AGADA,SPL"),
    ("Dr. Hamsaveni",      "SHALAKYA"),
    ("Dr. Harshitha",      "KC"),
    ("Dr. Jambavathi",     "SHALYA"),
    ("Dr. Jyothi",         "SPL"),
    ("Dr. Karthik",        "SPL"),
    ("Dr. Kiran Kumar",    "AGADA,SPL"),
    ("Dr. Kiran M Goud",   "PK"),
    ("Dr. Lokeshwari",     "KB"),
    ("Dr. Lolashri",       "PK"),
    ("Dr. Mahantesh",      "SPL"),
    ("Dr. Manasa",         "AGADA"),
    ("Dr. Mangala",        "KB"),
    ("Dr. Manjunath",      "KC,PK"),
    ("Dr. Meera",          "AGADA"),
    ("Dr. Nayan",          "KB"),
    ("Dr. Nayana",         "AGADA"),
    ("Dr. Neetha",         "AGADA"),
    ("Dr. Neharu",         "SHALYA"),
    ("Dr. Nithyashree",    "SHALAKYA"),
    ("Dr. Padmavathi",     "SHALAKYA"),
    ("Dr. Papiya Jana",    "PRASOOTI,STREE_ROGA"),
    ("Dr. Pranesh",        "KC"),
    ("Dr. Prasanna",       "SPL,YOGA"),
    ("Dr. Prathibha",      "SPL"),
    ("Dr. Priyanka",       "KB,SPL"),
    ("Dr. Pushpa",         "KB"),
    ("Dr. Radhika",        "AGADA"),
    ("Dr. Roopini",        "AGADA"),
    ("Dr. Shailaja SV",    "SHALYA"),
    ("Dr. Shanthala",      "SPL"),
    ("Dr. Shashirekha",    "KC,SPL,YOGA"),
    ("Dr. Sheshashaye B",  "SHALYA"),
    ("Dr. Shilpa",         "SPL"),
    ("Dr. Shreyas",        "KC,PK"),
    ("Dr. Shridevi",       "PRASOOTI,STREE_ROGA"),
    ("Dr. Shubha V Hegde", "AGADA"),
    ("Dr. Sindhura",       "KC,PK"),
    ("Dr. Sowmya",         "PRASOOTI,STREE_ROGA"),
    ("Dr. Sreekanth",      "AGADA"),
    ("Dr. Sujathamma",     "SHALAKYA"),
    ("Dr. Suma Saji",      "AGADA"),
    ("Dr. Sunayana",       "SPL,YOGA"),
    ("Dr. Sunitha GS",     "AGADA,KC"),
    ("Dr. Supreeth MJ",    "KC,PK"),
    ("Dr. Usha",           "PK"),
    ("Dr. Veena",          "SHALAKYA"),
    ("Dr. Venkatesh",      "SHALAKYA"),
    ("Dr. Vijayalakshmi",  "KC,PK"),
    ("Dr. Vinay Kumar KN", "KC,PK"),
    ("Dr. Vishwanath",     "SHALYA"),
]

# ─────────────────────────────────────────────────────────────────
# GOOGLE SHEETS CONNECTION
# ─────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_gspread_client():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        if "gcp_service_account" not in st.secrets:
            return None, "Secret [gcp_service_account] not found."
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        return client, None
    except Exception as e:
        return None, str(e)

@st.cache_resource(show_spinner=False)
def get_workbook():
    client, err = get_gspread_client()
    if not client: return None, err
    try:
        wb = client.open(st.secrets["sheet"]["name"])
        return wb, None
    except Exception as e:
        return None, str(e)

def get_or_create_sheet(wb, title, headers):
    """Get sheet tab by title, create with headers if missing."""
    try:
        ws = wb.worksheet(title)
        if not ws.row_values(1):
            ws.append_row(headers)
        return ws
    except Exception:
        try:
            ws = wb.add_worksheet(title=title, rows=2000, cols=len(headers))
            ws.append_row(headers)
            return ws
        except Exception:
            return None

def sheet_load(ws):
    try: return ws.get_all_records()
    except: return []

def sheet_upsert(ws, row_dict, key_cols):
    """Insert or update row matching key_cols."""
    try:
        cols_list = list(row_dict.keys())
        row = [clean(str(row_dict.get(c,""))) for c in cols_list]
        all_vals = ws.get_all_values()
        if not all_vals:
            ws.append_row(row); return
        hdrs = all_vals[0]
        # Find key column indices
        key_idxs = {}
        for kc in key_cols:
            if kc in hdrs: key_idxs[kc] = hdrs.index(kc)
        for i, r in enumerate(all_vals[1:], start=2):
            match = all(len(r)>key_idxs[kc] and
                        r[key_idxs[kc]]==clean(str(row_dict.get(kc,"")))
                        for kc in key_idxs)
            if match:
                # Build full row aligned to header
                full = [clean(str(row_dict.get(h,""))) for h in hdrs]
                ws.update(f"A{i}", [full]); return
        ws.append_row(row)
    except Exception as e:
        st.warning(f"Sheet write warning: {e}")

def sheet_append(ws, row_dict, col_order):
    try:
        row = [clean(str(row_dict.get(c,""))) for c in col_order]
        ws.append_row(row)
    except Exception as e:
        st.warning(f"Sheet append warning: {e}")

# ─────────────────────────────────────────────────────────────────
# ACD FLAT SEARCH
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
        def is_top(c): return bool(re.match(r"^[A-Z]{1,4}$",c))
        leaves=[]
        for _,row in df[~df["code"].apply(is_top)].iterrows():
            leaves.append({"code":row["code"],"condition":row["condition"],
                           "meaning":row["meaning"],
                           "label":f"{row['condition']} ({row['meaning']}) [{row['code']}]",
                           "search":f"{row['condition']} {row['meaning']} {row['code']}".lower()})
        return leaves, True
    except FileNotFoundError:
        return [], False

ACD_FLAT, ACD_LOADED = load_acd("newACD.xlsx")

def search_acd(q, n=40):
    if not q or len(q)<2: return []
    ql = q.lower().strip()
    exact = [i for i in ACD_FLAT if i["code"].lower()==ql]
    rest  = [i for i in ACD_FLAT if ql in i["search"] and i not in exact]
    return (exact+rest)[:n]

def acd_widget(sk, selk, label="Search Diagnosis"):
    q = st.text_input(label, key=sk,
                      placeholder="Type condition, English term or code (e.g. tonsil, sciatica, AAB-6)")
    res = search_acd(q)
    if q and len(q)>=2:
        if res:
            opts = ["— Select —"]+[r["label"] for r in res]
            sel  = st.selectbox(f"Results ({len(res)} found)", opts, key=selk)
            if sel!="— Select —":
                code = sel.split("[")[-1].rstrip("]").strip()
                mean = sel.split("(")[-1].split(")")[0].strip() if "(" in sel else ""
                st.markdown(f'<span class="code-big">{code}</span>&nbsp;&nbsp;'
                            f'<span style="font-size:0.8rem;color:#555">{mean}</span>',
                            unsafe_allow_html=True)
                return sel, code, mean
        else: st.caption("No matches. Try different keywords.")
    return "","",""

# ─────────────────────────────────────────────────────────────────
# STATIC DATA
# ─────────────────────────────────────────────────────────────────
DEPARTMENTS = {
    "KC":"Kaya Chikitsa (General Medicine)","PK":"Panchakarma",
    "SPL":"Swasthavritta & Lifestyle","AGADA":"Agada Tantra",
    "SHALYA":"Shalya Tantra","SHALAKYA":"Shalakya Tantra",
    "KB":"Kaumarabhritya","PRASOOTI":"Prasooti Tantra",
    "STREE_ROGA":"Stri Roga","YOGA":"Yoga & Wellness",
}
DEPT_CONDITIONS = {
    "KC":["Fever / Pyrexia","Vomiting / Nausea","GIT Disorders","Tiredness",
          "Giddiness","Loss of Strength","Stroke / Hemiplegia","Facial Paralysis",
          "General Weakness","Cough","Cardiac Complaints","Jaundice",
          "Anaemia","Headache","Loss of Appetite","Constipation","Other"],
    "PK":["Pain - Low Back","Pain - Knee / Joint","Pain - Cervical","Pain - Shoulder",
          "Sciatica","Rheumatoid Arthritis","Osteoarthritis","Gout","Frozen Shoulder",
          "Hemiplegia (PK)","Facial Palsy (PK)","Neurological for PK","Other"],
    "SPL":["Obesity","Diabetes Mellitus","High Cholesterol","Hypothyroidism",
           "Hyperthyroidism","Metabolic Syndrome","Hypertension","Insomnia",
           "Stress / Anxiety","Chronic Fatigue","Other"],
    "AGADA":["Psoriasis","Eczema / Dermatitis","Hair Fall","Premature Greying",
             "Vitiligo","Allergic Skin Reaction","Herpes","Acne","Fungal Infection",
             "Toxic conditions","Other"],
    "SHALYA":["Haemorrhoids","Fistula-in-Ano","Fissure-in-Ano","Rectal Prolapse",
              "Wound / Ulcer","Fracture","Abscess","Urinary complaints (Male)",
              "Urinary Incontinence","Kidney Stone","Other"],
    "SHALAKYA":["Diminished Vision","Cataract","Conjunctivitis","Eye Pain",
                "Sinusitis","Nasal Obstruction","Earache","Hearing Loss",
                "Throat Pain / Tonsillitis","Oral / Dental Disorder","Other"],
    "KB":["Fever - Child","Diarrhoea - Child","Failure to Thrive","Juvenile Arthritis",
          "Cerebral Palsy","Childhood Asthma","Skin Disorder - Child","Worm Infestation",
          "Growth Retardation","Developmental Disorder","Other"],
    "PRASOOTI":["Morning Sickness","Back Pain in Pregnancy","Oedema in Pregnancy",
                "Gestational Diabetes","Gestational Hypertension","Threatened Abortion",
                "Foetal Complications","Antenatal Checkup","Post-partum Disorders",
                "Insufficient Lactation","Other"],
    "STREE_ROGA":["Menorrhagia","Irregular Periods","Dysmenorrhoea","Leucorrhoea",
                  "Infertility (Female)","PCOS","Uterine Fibroid",
                  "Menopausal Complaints","Pelvic Pain / PID","Other"],
    "YOGA":["Stress / Burnout","Insomnia","Low Immunity","Obesity (Yoga)",
            "Respiratory Wellness","General Wellness"],
}
PK_TREATMENTS = {
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
        ("SAT-I.55","Lepa","Medicated Paste Application"),
        ("SAT-I.438","Parisheka","Medicated Streaming"),
        ("SAT-I.406","Kshara Karma","Caustic Application"),
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
JIHVA_OPT=["Sama/Lipta (Coated)","Nirama/Shuddha (Clean)","Ruksha (Dry)","Ardra (Moist)",
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
DUSHYA_OPT=["Rasa","Rakta","Mamsa","Meda","Asthi","Majja","Shukra/Artava","Other (specify below)"]
BALA_OPT=["Pravara Bala (Strong)","Madhyama Bala (Moderate)","Avara Bala (Weak)","Other (specify below)"]
KALA_OPT=["Vasanta (Spring)","Grishma (Summer)","Varsha (Monsoon)",
           "Sharad (Autumn)","Hemanta (Early Winter)","Shishira (Late Winter)"]
SATVA_OPT=["Sattva Pradhana","Rajas Pradhana","Tamas Pradhana","Madhyama","Other (specify below)"]
SATMYA_OPT=["Sarva Satmya","Desha Satmya","Kula Satmya","Madhyama","Other (specify below)"]
SHABDA_OPT=SPARSHA_OPT=DRIK_OPT=["Prakruta (Normal)","Vikruta (Altered)","Not assessed","Other (specify below)"]
AKRITI_OPT=["Prakruta (Normal)","Vikruta (Abnormal)","Not assessed","Other (specify below)"]
VYASANA_OPT=["None (NA)","Dhumapana (Smoking)","Madyapana (Alcohol)",
              "Tambula/Gutkha","Multiple habits","Other (specify below)"]
SEVERITY_OPT=["Mridu (Mild)","Madhyama (Moderate)","Maha/Tivra (Severe)"]
DURATION_OPT=["Less than 1 month (Acute)","1-6 months","6-12 months",
               "1-2 years","2-5 years","5-10 years","More than 10 years (Chronic)"]
LIFESTYLE_RISK=["Musculo-Skeletal","Cardiovascular","Metabolic/Endocrine","Neurological",
                 "Respiratory","Gastrointestinal","Gynaecological","Paediatric",
                 "Dermatological","Renal/Urological","None identified"]
GENDER_OPT=["Male","Female","Other","Prefer not to say"]
OCCUPATION_OPT=["Business","Service/Government","Agriculture","Housewife","Student",
                 "Labour/Manual work","Professional","Retired","Other"]
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
REFERRAL_PRIORITY=["Routine","Urgent","Emergency"]
REFERRAL_STATUS=["Pending","Accepted","Consultation Done","Resolved","Cancelled"]

def bmi_cat(b):
    for lo,hi,l in BMI_CATS:
        if lo<=b<hi: return l
    return ""

# ─────────────────────────────────────────────────────────────────
# DOSE TRANSLATION
# ─────────────────────────────────────────────────────────────────
def translate_dose(dose, form):
    fm = (form or "").lower()
    if any(x in fm for x in ["vati","gutika","tablet","capsule","cap"]): unit="tablet(s)"
    elif any(x in fm for x in ["churna","powder","bhasma"]): unit="gram(s)"
    elif any(x in fm for x in ["kashaya","syrup","kwatha","asava","arishta","taila","ghrita","avaleha"]): unit="ml"
    elif "drop" in fm: unit="drop(s)"
    else: unit="dose"
    MAP={"1 OD":f"Take 1 {unit} once daily","1 BD":f"Take 1 {unit} twice daily",
         "1 TID":f"Take 1 {unit} thrice daily","2 BD":f"Take 2 {unit} twice daily",
         "2 TID":f"Take 2 {unit} thrice daily","1 HS":f"Take 1 {unit} at bedtime",
         "SOS":f"Take 1 {unit} as needed (SOS)","5 ml OD":"Take 5 ml once daily",
         "5 ml BD":"Take 5 ml twice daily","5 ml TID":"Take 5 ml thrice daily",
         "10 ml OD":"Take 10 ml once daily","10 ml BD":"Take 10 ml twice daily",
         "10 ml TID":"Take 10 ml thrice daily","1 tsp OD":"Take 1 tsp (5ml) once daily",
         "1 tsp BD":"Take 1 tsp (5ml) twice daily","1 tsp TID":"Take 1 tsp (5ml) thrice daily"}
    return MAP.get(dose, dose or "")

def timing_txt(t):
    M={"Before food":"before meals","After food":"after meals","Between meals":"between meals",
       "At bedtime":"at bedtime","Empty stomach":"on empty stomach","With food":"with meals"}
    return M.get(t, t.lower() if t else "")

def anupana_txt(a):
    M={"Water":"with water","Warm water":"with warm water","Milk":"with milk",
       "Honey":"with honey","Ghee":"with ghee","Buttermilk":"with buttermilk",
       "Coconut water":"with coconut water","Ginger juice":"with ginger juice",
       "Cold water":"with cold water","Fruit juice":"with fruit juice"}
    return M.get(a, f"with {a.lower()}" if a else "")

def full_instruction(m):
    parts=[translate_dose(m.get("dose",""),m.get("form",""))]
    if m.get("timing"): parts.append(timing_txt(m["timing"]))
    if m.get("anupana"): parts.append(anupana_txt(m["anupana"]))
    if m.get("dur_val"): parts.append(f"for {m['dur_val']} {m.get('dur_unit','Days').lower()}")
    if m.get("notes"): parts.append(f"({m['notes']})")
    return ", ".join(p for p in parts if p)

# ─────────────────────────────────────────────────────────────────
# TOKEN + PID HELPERS
# ─────────────────────────────────────────────────────────────────
def next_token(records):
    today=str(date.today())
    nums=[int(str(r.get("Token_No","")).split("-")[-1])
          for r in records
          if str(r.get("Visit_Date","")).startswith(today)
          and "-" in str(r.get("Token_No",""))]
    return f"{today}-{(max(nums)+1 if nums else 1):03d}"

def auto_pid():
    yr=str(date.today().year)[2:]
    return f"N{yr}{st.session_state.get('pid_counter',1):04d}"

def validate_mobile(m):
    return bool(re.match(r"^\d{10}$",str(m).strip()))

# ─────────────────────────────────────────────────────────────────
# GENERAL HELPERS
# ─────────────────────────────────────────────────────────────────
def section(t): st.markdown(f'<div class="sec">{t}</div>', unsafe_allow_html=True)
def dept_lbl(k): return DEPARTMENTS.get(k,k)
def xcode(s):
    if s and "[" in s: return s.split("[")[-1].rstrip("]").strip()
    return ""
def clean(v):
    if not isinstance(v,str): return v
    return re.sub(r'[^\x00-\x7F\u0900-\u097F\u0080-\u00FF]','',str(v)).strip()
def sel_other(label,opts,key,idx=0):
    v=st.selectbox(label,opts,index=idx,key=key)
    if v=="Other (specify below)":
        ov=st.text_input(f"Specify — {label}",key=f"{key}_oth",placeholder="Type here")
        return ov if ov else "Other"
    return v
def custom_sel(label,opts,key,idx=0,ph="Type here"):
    v=st.selectbox(label,opts,index=idx,key=key)
    if v=="— Custom —":
        cv=st.text_input(f"Custom {label}",key=f"{key}_c",placeholder=ph)
        return cv if cv else ""
    return v

def find_patient(records, pid=None, mobile=None):
    out=[]
    for r in records:
        if pid and str(r.get("Patient_ID","")).strip()==str(pid).strip():
            out.append(r)
        elif mobile and str(r.get("Mobile","")).strip()==str(mobile).strip():
            out.append(r)
    return sorted(out, key=lambda x: x.get("Visit_DateTime",""))

def reset_form():
    for cat in ["Purvakarma","Pradhana Karma","Pashchata Karma"]:
        st.session_state[f"TX_{cat}"]=[]; st.session_state[f"TX_comments_{cat}"]={}
    st.session_state.med_count=1; st.session_state.rec={}
    st.session_state.pop("confirm_patient",None); st.session_state.pop("visit_count_override",None)

# ─────────────────────────────────────────────────────────────────
# PDF ENGINE (consolidated)
# ─────────────────────────────────────────────────────────────────
GREEN=colors.HexColor("#1a3a2a"); GOLD=colors.HexColor("#c8a96e")
GREY=colors.HexColor("#888888"); DGREY=colors.HexColor("#444444")
BGROW1=colors.HexColor("#f0f7f3")

def Ss():
    return {
        "hm": ParagraphStyle("hm",fontName="Helvetica",fontSize=7.5,alignment=TA_CENTER,textColor=GREY,spaceAfter=1),
        "sec":ParagraphStyle("sec",fontName="Helvetica-Bold",fontSize=9,textColor=GREEN,spaceBefore=5,spaceAfter=2),
        "n":  ParagraphStyle("n",fontName="Helvetica",fontSize=8.5,spaceAfter=2,leading=12),
        "sm": ParagraphStyle("sm",fontName="Helvetica",fontSize=7.5,textColor=DGREY,leading=11),
        "bd": ParagraphStyle("bd",fontName="Helvetica-Bold",fontSize=8.5,leading=12),
        "dx": ParagraphStyle("dx",fontName="Helvetica-Bold",fontSize=15,textColor=GREEN,spaceAfter=1,leading=18),
        "dxs":ParagraphStyle("dxs",fontName="Helvetica",fontSize=9,textColor=DGREY,spaceAfter=4,leading=12),
        "ptn":ParagraphStyle("ptn",fontName="Helvetica-Bold",fontSize=11,textColor=GREEN,spaceAfter=1),
        "mi": ParagraphStyle("mi",fontName="Helvetica",fontSize=8,textColor=colors.HexColor("#1a237e"),leading=11),
        "ins":ParagraphStyle("ins",fontName="Helvetica",fontSize=8.5,textColor=colors.HexColor("#1a237e"),leading=13,spaceAfter=2),
        "sR": ParagraphStyle("sR",fontName="Helvetica",fontSize=8,alignment=TA_RIGHT),
        "sL": ParagraphStyle("sL",fontName="Helvetica",fontSize=8,alignment=TA_LEFT),
        "ft": ParagraphStyle("ft",fontName="Helvetica",fontSize=6.5,alignment=TA_CENTER,textColor=GREY),
    }

def pdf_header(story,S,W):
    story.append(Paragraph("JAI SRI GURUDEV",S["hm"]))
    story.append(Paragraph("Sri Kalabyraveshwara Swamy Ayurvedic Medical College, Hospital & Research Centre",
                            ParagraphStyle("hb",fontName="Helvetica-Bold",fontSize=9.5,alignment=TA_CENTER,textColor=GREEN,spaceAfter=1)))
    story.append(Paragraph("No.10, Pipeline Road, RPC Layout, Hampinagara, Vijayanagar 2nd Stage, Bangalore - 560104",S["hm"]))
    story.append(Paragraph("Ph: 080-XXXXXXXX  |  info@skamcshrc.edu.in  |  NABH Accredited",S["hm"]))
    story.append(HRFlowable(width=W,thickness=2,color=GREEN,spaceAfter=1))
    story.append(HRFlowable(width=W,thickness=0.8,color=GOLD,spaceAfter=3))

def pdf_pat(rec,S,W):
    rows=[
        [Paragraph(f"<b>{rec.get('Patient_Name','—')}</b>",S["ptn"]),Paragraph("",S["n"]),
         Paragraph(f"<b>Token: {rec.get('Token_No','')}</b>",ParagraphStyle("tok",fontName="Helvetica-Bold",fontSize=10,textColor=GREEN,alignment=TA_RIGHT)),
         Paragraph(datetime.now().strftime("%d %b %Y  %I:%M %p"),ParagraphStyle("dt",fontName="Helvetica",fontSize=8,alignment=TA_RIGHT))],
        [Paragraph(f"<b>ID:</b> {rec.get('Patient_ID','')}  |  <b>Mobile:</b> {rec.get('Mobile','')}",S["n"]),Paragraph("",S["n"]),
         Paragraph(f"<b>Age/Gender:</b> {rec.get('Age','')} yrs / {rec.get('Gender','')}",S["n"]),
         Paragraph(f"<b>Visit #{rec.get('Visit_Count','1')}</b>  |  {rec.get('Visit_Type','')}",ParagraphStyle("vs",fontName="Helvetica",fontSize=8.5,alignment=TA_RIGHT))],
        [Paragraph(f"<b>Dept:</b> {rec.get('Department','')}",S["n"]),Paragraph("",S["n"]),
         Paragraph(f"<b>Prakriti:</b> {rec.get('Prakriti','')}",S["n"]),
         Paragraph(f"<b>Physician:</b> {rec.get('Physician','')}",ParagraphStyle("ph",fontName="Helvetica-Bold",fontSize=8.5,alignment=TA_RIGHT))],
    ]
    t=Table(rows,colWidths=[60*mm,10*mm,55*mm,48*mm])
    t.setStyle(TableStyle([("FONTSIZE",(0,0),(-1,-1),8.5),("ROWBACKGROUNDS",(0,0),(-1,-1),[BGROW1,colors.white,BGROW1]),
                            ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#cccccc")),("TOPPADDING",(0,0),(-1,-1),2.5),("BOTTOMPADDING",(0,0),(-1,-1),2.5),
                            ("SPAN",(0,0),(1,0)),("SPAN",(2,0),(3,0)),("SPAN",(0,1),(1,1)),("SPAN",(0,2),(1,2))]))
    return t

def pdf_dx(story,rec,S,W):
    code=rec.get("Final_ACD_Code") or rec.get("ACD_Code_1","")
    mean=rec.get("Final_ACD_Meaning") or rec.get("ACD_Meaning_1","")
    cc=rec.get("Chief_Complaints_Modified") or rec.get("Chief_Complaints","")
    if code or cc:
        story.append(HRFlowable(width=W,thickness=0.5,color=colors.HexColor("#b7d9c5"),spaceAfter=2))
    if cc: story.append(Paragraph(f"C/O: {cc}",S["sm"]))
    if code: story.append(Paragraph(code,S["dx"])); story.append(Paragraph(mean,S["dxs"]))

def pdf_meds(story,rec,S,W):
    meds=rec.get("Medicines",[])
    if not meds: return
    story.append(HRFlowable(width=W,thickness=0.5,color=colors.HexColor("#b7d9c5"),spaceAfter=2))
    story.append(Paragraph("Shamana Aushadhi",S["sec"]))
    hdr=[[Paragraph(h,S["bd"]) for h in ["#","Drug Name","Form / Route","Instruction","Duration"]]]
    rows=[]
    for i,m in enumerate(meds,1):
        instr=full_instruction(m)
        fr=m.get("form",""); rt=m.get("route","Oral")
        if rt!="Oral": fr+=f"\n({rt})"
        rows.append([Paragraph(str(i),S["sm"]),Paragraph(f"<b>{m.get('name','')}</b>",S["n"]),
                     Paragraph(fr,S["sm"]),Paragraph(instr,S["mi"]),
                     Paragraph(f"{m.get('dur_val','')} {m.get('dur_unit','')}",S["sm"])])
    mt=Table(hdr+rows,colWidths=[6*mm,48*mm,28*mm,W-110*mm,28*mm])
    mt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),GREEN),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                             ("FONTSIZE",(0,0),(-1,-1),7.5),("ROWBACKGROUNDS",(0,1),(-1,-1),[BGROW1,colors.white]),
                             ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#cccccc")),
                             ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(mt)

def pdf_pk(story,rec,S,W):
    all_tx=[(c,rec.get(f"TX_{c}",[]),rec.get(f"TX_comments_{c}",{}))
            for c in ["Purvakarma","Pradhana Karma","Pashchata Karma"]]
    all_tx=[(c,s,cm) for c,s,cm in all_tx if s]
    if not all_tx and not rec.get("TX_Custom"): return
    story.append(HRFlowable(width=W,thickness=0.5,color=colors.HexColor("#b7d9c5"),spaceAfter=2))
    story.append(Paragraph("Panchakarma Treatment Plan",S["sec"]))
    cat_bg={"Purvakarma":colors.HexColor("#e8f5e9"),"Pradhana Karma":colors.HexColor("#fff3e0"),
            "Pashchata Karma":colors.HexColor("#e3f2fd")}
    for cat,sel,cmt in all_tx:
        story.append(Paragraph(f"<b>{cat}</b>",S["bd"]))
        rows=[[Paragraph(h,S["bd"]) for h in ["Procedure","Code","Comments"]]]
        for tx in sel:
            code=xcode(tx); name=tx.split(" — ")[0] if " — " in tx else tx
            rows.append([Paragraph(name,S["n"]),
                         Paragraph(f"<b>{code}</b>",ParagraphStyle("pc",fontName="Helvetica-Bold",fontSize=8,textColor=GREEN)),
                         Paragraph(cmt.get(code,""),S["sm"])])
        tbl=Table(rows,colWidths=[55*mm,22*mm,W-77*mm])
        tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),GREEN),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                                  ("FONTSIZE",(0,0),(-1,-1),7.5),("BACKGROUND",(0,1),(-1,-1),cat_bg.get(cat,BGROW1)),
                                  ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#cccccc")),
                                  ("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2),("VALIGN",(0,0),(-1,-1),"TOP")]))
        story.append(tbl); story.append(Spacer(1,1.5*mm))
    if rec.get("TX_Custom"): story.append(Paragraph(f"<b>Additional:</b>  {rec['TX_Custom']}",S["sm"]))

def pdf_extras(story,rec,S,W):
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

def pdf_sig(story,S,W,rec):
    story.append(Spacer(1,8*mm))
    story.append(HRFlowable(width=W,thickness=0.4,color=GREY,spaceAfter=3))
    sd=[[Paragraph("Reg. No.:  _______________________",S["sL"]),Paragraph(f"<b>{rec.get('Physician','')}</b>",S["sR"])],
        [Paragraph("Date: ________________",S["sL"]),Paragraph("MD (Ayurveda)",S["sR"])],
        [Paragraph("",S["sL"]),Paragraph("Signature &amp; Stamp",S["sR"])]]
    st2=Table(sd,colWidths=[W/2,W/2])
    st2.setStyle(TableStyle([("FONTSIZE",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),2)]))
    story.append(st2)

def pdf_footer(story,S,W):
    story.append(Spacer(1,4*mm))
    story.append(HRFlowable(width=W,thickness=0.8,color=GOLD,spaceAfter=1))
    story.append(HRFlowable(width=W,thickness=0.3,color=GREY,spaceAfter=2))
    story.append(Paragraph("Conceptized by: Dr. Kiran M Goud, MD (Ay.)  |  Developed by: Dr. Prasanna Kulkarni, MD (Ay.), MS (Data Science)  |  ACD: Namaste Portal  |  SAT-I: WHO",S["ft"]))

def make_pdf(rec, mode="both"):
    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,topMargin=12*mm,bottomMargin=18*mm,leftMargin=18*mm,rightMargin=18*mm)
    W=A4[0]-36*mm; S=Ss(); story=[]
    pdf_header(story,S,W)
    title={"rx":"Prescription","pk":"Panchakarma Procedure Advice","both":"OPD Prescription"}.get(mode,"Prescription")
    story.append(Paragraph(title,ParagraphStyle("tit",fontName="Helvetica-Bold",fontSize=13,alignment=TA_CENTER,textColor=GREEN,spaceAfter=2)))
    story.append(HRFlowable(width=W,thickness=0.8,color=GOLD,spaceAfter=3))
    story.append(pdf_pat(rec,S,W)); story.append(Spacer(1,1*mm))
    vit=f"Ht:{rec.get('Height_cm','')}cm  Wt:{rec.get('Weight_kg','')}kg  BMI:{rec.get('BMI','')}({rec.get('BMI_Category','')})  BP:{rec.get('BP','')}  Pulse:{rec.get('Pulse_bpm','')}bpm  Temp:{rec.get('Temp_F','')}F  SpO2:{rec.get('SpO2_pct','')}%"
    story.append(Paragraph(vit,S["sm"]))
    pdf_dx(story,rec,S,W)
    if mode in ("rx","both"): pdf_meds(story,rec,S,W)
    if mode in ("pk","both"): pdf_pk(story,rec,S,W)
    pdf_extras(story,rec,S,W); pdf_sig(story,S,W,rec); pdf_footer(story,S,W)
    doc.build(story); buf.seek(0); return buf

# ─────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────
_ss_defaults = {
    "logged_in":False,"user_role":None,"user_name":None,
    "login_attempts":0,"lockout_until":None,"last_activity":None,
    "force_pin_change":False,
    "records":[],"physicians":[],"referrals":[],
    "rec":{},"dept_key":"KC","pid_counter":1,"med_count":1,
    "gs_loaded":False,
}
for k,v in _ss_defaults.items():
    if k not in st.session_state: st.session_state[k]=v
for cat in ["Purvakarma","Pradhana Karma","Pashchata Karma"]:
    if f"TX_{cat}" not in st.session_state: st.session_state[f"TX_{cat}"]=[]
    if f"TX_comments_{cat}" not in st.session_state: st.session_state[f"TX_comments_{cat}"]={}

# ─────────────────────────────────────────────────────────────────
# GOOGLE SHEETS INIT
# ─────────────────────────────────────────────────────────────────
wb, gs_err = get_workbook()
GS_OK = wb is not None

ws_opd, ws_phys, ws_ref = None, None, None
if GS_OK:
    ws_opd  = get_or_create_sheet(wb, "OPD_Records", OPD_COLS)
    ws_phys = get_or_create_sheet(wb, "Physicians",  PHYS_COLS)
    ws_ref  = get_or_create_sheet(wb, "Referrals",   REF_COLS)

if GS_OK and not st.session_state.gs_loaded:
    if ws_opd:
        existing = sheet_load(ws_opd)
        if existing: st.session_state.records = existing
    if ws_phys:
        phys_data = sheet_load(ws_phys)
        if not phys_data:
            # Seed physician roster on first run
            today_str = str(date.today())
            rows_to_seed = []
            # Reception
            rows_to_seed.append({"Name":"Reception Desk","Departments":"ALL",
                                  "PIN_Hash":hash_pin(DEFAULT_RECEP_PIN),"Role":"Receptionist",
                                  "Status":"Active","PIN_Changed":"Yes","Added_Date":today_str})
            # Admin (Dr. Prasanna)
            rows_to_seed.append({"Name":"Dr. Prasanna","Departments":"SPL,YOGA",
                                  "PIN_Hash":hash_pin(DEFAULT_ADMIN_PIN),"Role":"Admin",
                                  "Status":"Active","PIN_Changed":"No","Added_Date":today_str})
            # All physicians
            for name, depts in SEED_PHYSICIANS:
                if name == "Dr. Prasanna": continue  # already added as admin
                rows_to_seed.append({"Name":name,"Departments":depts,
                                     "PIN_Hash":HASH_DEFAULT_PHYS,"Role":"Physician",
                                     "Status":"Active","PIN_Changed":"No","Added_Date":today_str})
            for row in rows_to_seed:
                sheet_append(ws_phys, row, PHYS_COLS)
            st.session_state.physicians = rows_to_seed
        else:
            st.session_state.physicians = phys_data
    if ws_ref:
        ref_data = sheet_load(ws_ref)
        if ref_data: st.session_state.referrals = ref_data
    st.session_state.gs_loaded = True

# ─────────────────────────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────────────────────────
def get_physician_record(name):
    for p in st.session_state.physicians:
        if str(p.get("Name","")).strip() == str(name).strip():
            return p
    return None

def get_active_physicians():
    return [p for p in st.session_state.physicians
            if str(p.get("Status","Active")).strip()=="Active"
            and str(p.get("Role","Physician")).strip() in ("Physician","Admin")]

def get_phys_names_for_dept(dept_key, on_req=False):
    active = [p["Name"] for p in get_active_physicians()]
    if on_req: return sorted(active)
    result = []
    for p in get_active_physicians():
        depts = [d.strip() for d in str(p.get("Departments","")).split(",")]
        if dept_key in depts: result.append(p["Name"])
    return sorted(result) if result else sorted(active)

def check_session_timeout():
    if st.session_state.last_activity:
        elapsed = (datetime.now() - st.session_state.last_activity).total_seconds() / 3600
        if elapsed > SESSION_TIMEOUT_HRS:
            st.session_state.logged_in = False
            st.session_state.user_role = None
            st.session_state.user_name = None
            return True
    st.session_state.last_activity = datetime.now()
    return False

def try_login(name_or_role, pin_entered, physicians_list):
    """Attempt login. Returns (success, role, name, force_pin_change, error_msg)."""
    # Guard: ensure login_attempts is always an int
    if not isinstance(st.session_state.get("login_attempts"), int):
        st.session_state.login_attempts = 0

    # Check lockout
    if st.session_state.lockout_until:
        try:
            remaining = (st.session_state.lockout_until - datetime.now()).total_seconds()
            if remaining > 0:
                return False, None, None, False, f"Too many failed attempts. Try again in {int(remaining/60)+1} minute(s)."
            else:
                st.session_state.lockout_until = None
                st.session_state.login_attempts = 0
        except Exception:
            st.session_state.lockout_until = None
            st.session_state.login_attempts = 0

    ph = hash_pin(pin_entered)

    # Reception Desk — fully handled here, never falls through
    if name_or_role == "Reception Desk":
        if ph == hash_pin(DEFAULT_RECEP_PIN):
            st.session_state.login_attempts = 0
            return True, "Receptionist", "Reception Desk", False, None
        rec_p = get_physician_record("Reception Desk")
        if rec_p and ph == str(rec_p.get("PIN_Hash", "")):
            st.session_state.login_attempts = 0
            return True, "Receptionist", "Reception Desk", False, None
        st.session_state.login_attempts += 1
        if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
            st.session_state.lockout_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
            return False, None, None, False, f"Locked for {LOCKOUT_MINUTES} minutes."
        remaining_attempts = MAX_LOGIN_ATTEMPTS - st.session_state.login_attempts
        return False, None, None, False, f"Incorrect PIN. {remaining_attempts} attempt(s) remaining."

    # Find physician by name
    matched = get_physician_record(name_or_role)
    if not matched:
        st.session_state.login_attempts += 1
        if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
            st.session_state.lockout_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
        return False, None, None, False, "Physician not found."

    if str(matched.get("Status", "Active")) != "Active":
        return False, None, None, False, "This account is deactivated. Contact Admin."

    if ph != str(matched.get("PIN_Hash", "")):
        st.session_state.login_attempts += 1
        remaining_attempts = MAX_LOGIN_ATTEMPTS - st.session_state.login_attempts
        if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
            st.session_state.lockout_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
            return False, None, None, False, f"Locked for {LOCKOUT_MINUTES} minutes."
        return False, None, None, False, f"Incorrect PIN. {remaining_attempts} attempt(s) remaining."

    # Success
    st.session_state.login_attempts = 0
    force_change = str(matched.get("PIN_Changed", "No")).strip() == "No"
    role = str(matched.get("Role", "Physician")).strip()
    return True, role, matched["Name"], force_change, None

def do_pin_change(physician_name, new_pin, confirm_pin):
    if new_pin != confirm_pin:
        return False, "PINs do not match."
    if len(str(new_pin)) < 4:
        return False, "PIN must be at least 4 digits."
    if not str(new_pin).isdigit():
        return False, "PIN must contain digits only."
    new_hash = hash_pin(new_pin)
    # Update in session
    for i, p in enumerate(st.session_state.physicians):
        if str(p.get("Name","")).strip() == physician_name:
            st.session_state.physicians[i]["PIN_Hash"] = new_hash
            st.session_state.physicians[i]["PIN_Changed"] = "Yes"
            # Sync to sheet
            if ws_phys:
                sheet_upsert(ws_phys, st.session_state.physicians[i], ["Name"])
            return True, "PIN changed successfully."
    return False, "Physician not found."

# ─────────────────────────────────────────────────────────────────
# LOGIN SCREEN
# ─────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align:center;margin-top:30px;">
      <div style="font-family:'Noto Serif',serif;font-size:1.5rem;font-weight:700;
                  color:#1a3a2a;margin-bottom:4px;">SKAMCSHRC</div>
      <div style="color:#666;font-size:0.85rem;margin-bottom:30px;">
        Sri Kalabyraveshwara Swamy Ayurvedic Medical College<br>Hospital & Research Centre, Bangalore
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1,1.4,1])
    with col_c:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">OPD Clinical Data Entry</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Sign in to continue</div>', unsafe_allow_html=True)

        # Build login name list from physicians
        login_names = ["— Select —", "Reception Desk"]
        if st.session_state.physicians:
            active_names = [p["Name"] for p in st.session_state.physicians
                            if str(p.get("Status","Active"))=="Active" and p["Name"]!="Reception Desk"]
            login_names += sorted(active_names)
        else:
            # Fallback if sheets not connected — show seeded names
            login_names += sorted([n for n,_ in SEED_PHYSICIANS])
            login_names.append("Dr. Prasanna")

        sel_name = st.selectbox("Select Your Name", login_names, key="login_name")
        pin_in   = st.text_input("Enter PIN", type="password", max_chars=8, key="login_pin",
                                  placeholder="Enter your PIN")

        if st.button("Login", type="primary", use_container_width=True, key="do_login"):
            if sel_name == "— Select —":
                st.error("Please select your name.")
            elif not pin_in:
                st.error("Please enter your PIN.")
            else:
                ok, role, name, force_chg, err = try_login(
                    sel_name, pin_in, st.session_state.physicians)
                if ok:
                    st.session_state.logged_in     = True
                    st.session_state.user_role     = role
                    st.session_state.user_name     = name
                    st.session_state.force_pin_change = force_chg
                    st.session_state.last_activity = datetime.now()
                    st.rerun()
                else:
                    st.error(err)

        st.markdown("---")
        st.markdown("<div style='font-size:0.73rem;color:#888;text-align:center;'>"
                    "Default PIN for all physicians: <b>1234</b><br>"
                    "You will be asked to change it on first login</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────
# SESSION TIMEOUT CHECK
# ─────────────────────────────────────────────────────────────────
if check_session_timeout():
    st.warning("Session expired. Please login again.")
    st.rerun()

# ─────────────────────────────────────────────────────────────────
# FORCE PIN CHANGE SCREEN
# ─────────────────────────────────────────────────────────────────
if st.session_state.force_pin_change:
    st.markdown('<div class="main-hdr"><h2>SKAMCSHRC OPD</h2></div>', unsafe_allow_html=True)
    st.markdown('<div class="pin-change-box">', unsafe_allow_html=True)
    st.markdown(f"### Welcome, {st.session_state.user_name}")
    st.warning("You are using the default PIN. Please set a new personal PIN before continuing.")
    c1,c2 = st.columns(2)
    with c1: new_p  = st.text_input("New PIN (min 4 digits)", type="password", key="new_pin", max_chars=8)
    with c2: conf_p = st.text_input("Confirm New PIN",        type="password", key="conf_pin",max_chars=8)
    if st.button("Set PIN & Continue", type="primary", key="set_pin"):
        ok, msg = do_pin_change(st.session_state.user_name, new_p, conf_p)
        if ok:
            st.session_state.force_pin_change = False
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────
# MAIN APP — HEADER
# ─────────────────────────────────────────────────────────────────
ROLE = st.session_state.user_role
NAME = st.session_state.user_name

role_badge = {
    "Admin":       '<span class="role-badge-admin">ADMIN (HOD)</span>',
    "Physician":   '<span class="role-badge-physician">PHYSICIAN</span>',
    "Receptionist":'<span class="role-badge-receptionist">RECEPTIONIST</span>',
}.get(ROLE,"")

st.markdown(f"""
<div class="main-hdr">
  <h2>SKAMCSHRC — OPD Clinical Data Entry &nbsp;&nbsp;{role_badge}</h2>
  <p>Logged in as: <b>{NAME}</b> &nbsp;|&nbsp; Session started: {st.session_state.last_activity.strftime('%I:%M %p') if st.session_state.last_activity else ''}</p>
</div>
""", unsafe_allow_html=True)

if not ACD_LOADED:
    st.warning("newACD.xlsx not found.")
if not GS_OK:
    if gs_err: st.error(f"Google Sheets: {gs_err}")
    else: st.info("Google Sheets not configured — session-only mode.")

# Metrics
m1,m2,m3,m4 = st.columns(4)
m1.metric("Date", date.today().strftime("%d %b %Y"))
m2.metric("Time", datetime.now().strftime("%I:%M %p"))
today_n = len([r for r in st.session_state.records
               if str(r.get("Visit_Date","")).startswith(str(date.today()))])
m3.metric("Today's Records", today_n)
m4.metric("Total Records", len(st.session_state.records))
st.markdown("---")

# ─────────────────────────────────────────────────────────────────
# BUILD TABS BASED ON ROLE
# ─────────────────────────────────────────────────────────────────
if ROLE == "Receptionist":
    tabs = st.tabs(["Reception & Screening", "Today's Queue"])
elif ROLE == "Physician":
    tabs = st.tabs(["My Cases & Consultation", "Cross Referrals"])
else:  # Admin
    tabs = st.tabs(["Reception & Screening", "Physician Consultation",
                    "Cross Referrals", "Physician Management"])

# ─────────────────────────────────────────────────────────────────
# SHARED: RECEPTION FORM (used by Receptionist and Admin)
# ─────────────────────────────────────────────────────────────────
def render_reception_tab():
    st.markdown("### Reception & Screening")

    # Patient search
    st.markdown('<div class="card">', unsafe_allow_html=True)
    section("SEARCH RETURNING PATIENT")
    sc1,sc2 = st.columns(2)
    with sc1: srch_id  = st.text_input("Search by Registration Number", key="srch_id",  placeholder="e.g. N260001")
    with sc2: srch_mob = st.text_input("Search by Mobile Number",        key="srch_mob", placeholder="10-digit mobile")
    found_v=[]
    if srch_id and len(srch_id)>=4:
        found_v = find_patient(st.session_state.records, pid=srch_id)
    elif srch_mob and len(srch_mob)==10:
        found_v = find_patient(st.session_state.records, mobile=srch_mob)
    ret = st.session_state.get("confirm_patient",None)
    visit_count = st.session_state.get("visit_count_override",1) if ret else 1
    if found_v:
        last=found_v[-1]; vc=len(found_v)+1
        st.markdown(
            f'<div class="returning-banner"><h4>Returning Patient — {last.get("Patient_Name","")}</h4>'
            f'<b>ID:</b> {last.get("Patient_ID","")}  |  <b>Mobile:</b> {last.get("Mobile","")}  |  '
            f'<b>Visits:</b> {len(found_v)}  |  <b>Last:</b> {last.get("Visit_Date","")}  |  '
            f'<b>Last Dx:</b> <span style="font-family:monospace;font-weight:700">'
            f'{last.get("Final_ACD_Code") or last.get("ACD_Code_1","")}</span>  '
            f'{last.get("Final_ACD_Meaning") or last.get("ACD_Meaning_1","")}  |  '
            f'<b>Physician:</b> {last.get("Physician","")}</div>',
            unsafe_allow_html=True)
        if st.button(f"Confirm & Auto-fill for Visit #{vc}", type="primary", key="conf_ret"):
            st.session_state.confirm_patient=last; st.session_state["visit_count_override"]=vc
    elif (srch_id and len(srch_id)>=4) or (srch_mob and len(srch_mob)==10):
        st.info("No records found. Register as new patient below.")
    st.markdown('</div>',unsafe_allow_html=True)

    def pf(f,d): return ret[f] if ret and ret.get(f) else d

    # Triage
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("1  TRIAGE")
    triage=st.radio("Triage",["Routine","Urgent"],index=0,horizontal=True,key="triage_r")
    if triage=="Urgent":
        st.markdown('<div class="triage-u">URGENT</div>',unsafe_allow_html=True)
    else:
        st.markdown('<div class="triage-r">ROUTINE</div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

    # Demographics
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("2  PATIENT DEMOGRAPHICS")
    tk_col,pid_col=st.columns([1,2])
    with tk_col:
        token=next_token(st.session_state.records)
        st.markdown(f'<div class="token-badge">Token: {token}</div>',unsafe_allow_html=True)
    with pid_col:
        pid=st.text_input("Patient ID",value=pf("Patient_ID",auto_pid()),key="pid")
    r1a,r1b,r1c=st.columns(3)
    with r1a: pat_name=st.text_input("Patient Name",value=pf("Patient_Name",""),key="pat_name")
    with r1b:
        mobile=st.text_input("Mobile (10 digits)",value=pf("Mobile",""),key="mobile",max_chars=10)
        if mobile and not validate_mobile(mobile): st.warning("Enter valid 10-digit number")
    with r1c: vdate=st.date_input("Visit Date",value=date.today(),key="vdate")
    r2a,r2b,r2c=st.columns(3)
    with r2a:
        age=st.number_input("Age (years)",0,120,int(pf("Age",30)),key="age")
        gd=pf("Gender",GENDER_OPT[0]); gi=GENDER_OPT.index(gd) if gd in GENDER_OPT else 0
        gender=st.selectbox("Gender",GENDER_OPT,index=gi,key="gender")
    with r2b:
        vtype=st.selectbox("Visit Type",["New Case","Follow Up"],index=0 if not ret else 1,key="vtype")
        dd=pf("District",DISTRICT_LIST[0]); di=DISTRICT_LIST.index(dd) if dd in DISTRICT_LIST else 0
        district=st.selectbox("District",DISTRICT_LIST,index=di,key="district")
    with r2c:
        od=pf("Occupation",OCCUPATION_OPT[0]); oi=OCCUPATION_OPT.index(od) if od in OCCUPATION_OPT else 0
        occ=st.selectbox("Occupation",OCCUPATION_OPT,index=oi,key="occ")
        pk=pf("Prakriti",PRAKRITI_OPT[0]); pi2=PRAKRITI_OPT.index(pk) if pk in PRAKRITI_OPT else 0
        prakriti=st.selectbox("Prakriti",PRAKRITI_OPT,index=pi2,key="prakriti")
    lrisk=st.multiselect("Lifestyle Risk",LIFESTYLE_RISK,key="lrisk")
    consent=st.checkbox("Patient / Guardian consents to data storage",key="consent")
    st.markdown('</div>',unsafe_allow_html=True)

    # Department & Physician
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("3  DEPARTMENT & PHYSICIAN")
    dc1,dc2=st.columns(2)
    with dc1:
        dept_def=pf("Department",""); dkeys=list(DEPARTMENTS.keys())
        dk_def=next((k for k,v in DEPARTMENTS.items() if v==dept_def),st.session_state.dept_key)
        dept_key=st.selectbox("Department",dkeys,format_func=dept_lbl,
                               index=dkeys.index(dk_def) if dk_def in dkeys else 0,key="dept_sel")
        st.session_state.dept_key=dept_key
    with dc2:
        on_req=st.checkbox("On Request (all physicians)",key="on_req")
    phys_list=get_phys_names_for_dept(dept_key,on_req)
    phd=pf("Physician",phys_list[0] if phys_list else "")
    physician=st.selectbox("Physician",phys_list,index=phys_list.index(phd) if phd in phys_list else 0,key="phys_sel")
    consult_type="On Request" if on_req else "Regular"
    st.markdown('</div>',unsafe_allow_html=True)

    # Complaints & Diagnosis
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("4  CHIEF COMPLAINTS & PROVISIONAL DIAGNOSIS")
    chief=st.multiselect("Chief Complaints",DEPT_CONDITIONS.get(dept_key,[]),key="chief")
    other_cc=st.text_input("Additional Chief Complaint",key="other_cc")
    st.markdown("**Provisional Diagnosis 1**")
    _,pc1,pm1=acd_widget("ps1","psel1","Search Diagnosis 1")
    st.markdown("**Provisional Diagnosis 2** (optional)")
    _,pc2,pm2=acd_widget("ps2","psel2","Search Diagnosis 2")
    sc1,sc2=st.columns(2)
    with sc1: severity=st.selectbox("Severity",SEVERITY_OPT,key="severity")
    with sc2: duration=st.selectbox("Disease Duration",DURATION_OPT,key="duration")
    st.markdown('</div>',unsafe_allow_html=True)

    # Save
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("5  SAVE RECEPTION RECORD")
    if st.button("Save Reception Record",type="primary",key="save_rec"):
        if mobile and not validate_mobile(mobile):
            st.error("Enter valid 10-digit mobile number.")
        else:
            ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rec={
                "Token_No":token,"Patient_ID":pid,"Patient_Name":pat_name,"Mobile":mobile,
                "Visit_Date":str(vdate),"Visit_Time":datetime.now().strftime("%H:%M:%S"),
                "Visit_DateTime":ts,"Visit_Year":vdate.year,"Visit_Count":visit_count,
                "Visit_Type":vtype,"Consultation_Type":consult_type,"Status":"Awaiting Physician",
                "Age":age,"Gender":gender,"District":district,"Occupation":occ,
                "Prakriti":prakriti,"Lifestyle_Risk":", ".join(lrisk) if lrisk else "",
                "Triage":triage,"Department":dept_lbl(dept_key),"Physician":physician,
                "Chief_Complaints":", ".join(chief)+(f"; {other_cc}" if other_cc else ""),
                "Chief_Complaints_Modified":"",
                "ACD_Code_1":pc1,"ACD_Meaning_1":pm1,"ACD_Code_2":pc2,"ACD_Meaning_2":pm2,
                "Severity":severity,"Disease_Duration":duration,"Consent":"Yes" if consent else "No",
                "Height_cm":"","Weight_kg":"","BMI":"","BMI_Category":"","BP":"","Pulse_bpm":"",
                "Temp_F":"","SpO2_pct":"","RR_per_min":"","Other_Investigation":"",
                "Nadi":"","Jihva":"","Agni":"","Mala":"","Mutra":"","Sleep":"",
                "Shabda":"","Sparsha":"","Drik":"","Akriti":"","Dosha":"","Dushya":"",
                "Bala":"","Kala":"","Satva":"","Satmya":"","Vyasana":"","Prakriti_Confirmed":"",
                "Final_ACD_Code":"","Final_ACD_Meaning":"",
                "TX_Purvakarma":"","TX_Pradhana_Karma":"","TX_Pashchata_Karma":"",
                "TX_Comments_Purvakarma":"","TX_Comments_Pradhana":"","TX_Comments_Pashchata":"",
                "TX_Custom":"","Medicines_Summary":"","Lab_Tests":"","Followup_Date":"",
                "Instructions":"","Physician_Notes":"","Followup_Notes":"","Treatment_Response":"",
            }
            st.session_state.rec=rec
            st.session_state.records.append(rec)
            if ws_opd: sheet_upsert(ws_opd, rec, ["Patient_ID","Visit_DateTime"])
            if not ret: st.session_state.pid_counter+=1
            reset_form()
            st.success(f"Saved — {pid} | Token {token} | Visit #{visit_count}. Proceed to Physician tab.")
    st.markdown('</div>',unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# SHARED: QUEUE VIEW (Receptionist + Admin)
# ─────────────────────────────────────────────────────────────────
def render_queue_tab():
    st.markdown("### Today's Patient Queue")
    today=str(date.today())
    today_recs=[r for r in st.session_state.records if str(r.get("Visit_Date","")).startswith(today)]
    if not today_recs:
        st.info("No patients registered today yet.")
        return

    # Stats row
    total=len(today_recs)
    urgent=len([r for r in today_recs if r.get("Triage")=="Urgent"])
    waiting=len([r for r in today_recs if r.get("Status","")=="Awaiting Physician"])
    completed=len([r for r in today_recs if r.get("Status","")=="Completed"])
    q1,q2,q3,q4=st.columns(4)
    q1.metric("Total Today", total)
    q2.metric("Urgent", urgent)
    q3.metric("Awaiting Physician", waiting)
    q4.metric("Completed", completed)
    st.markdown("---")

    # Per-physician breakdown
    physicians_today=sorted(set(r.get("Physician","") for r in today_recs if r.get("Physician","")))
    if physicians_today:
        st.markdown("#### Queue by Physician")
        for phys in physicians_today:
            phys_recs=[r for r in today_recs if r.get("Physician","")==phys]
            with st.expander(f"{phys}  ({len(phys_recs)} patients)", expanded=True):
                for r in sorted(phys_recs, key=lambda x: x.get("Token_No","")):
                    status=r.get("Status","Awaiting Physician")
                    triage=r.get("Triage","Routine")
                    css = "queue-row-urgent" if triage=="Urgent" else \
                          ("queue-row-done" if status=="Completed" else "queue-row-waiting")
                    status_icon={"Awaiting Physician":"⏳","Completed":"✓","Urgent":"🔴"}.get(
                        status if status!="Urgent" else "Urgent","•")
                    st.markdown(
                        f'<div class="{css}">'
                        f'<b>{r.get("Token_No","")}</b> &nbsp;|&nbsp; '
                        f'{r.get("Patient_Name","")} &nbsp;|&nbsp; '
                        f'{r.get("Age","")} yrs / {r.get("Gender","")} &nbsp;|&nbsp; '
                        f'<span style="font-family:monospace">'
                        f'{r.get("ACD_Code_1","")}</span> &nbsp;|&nbsp; '
                        f'<b>{status}</b> &nbsp;{status_icon}'
                        f'</div>',
                        unsafe_allow_html=True)

                    # Admin can reassign physician
                    if ROLE=="Admin":
                        with st.form(key=f"reassign_{r.get('Token_No','')}_{r.get('Visit_DateTime','')}"):
                            all_phys=[p["Name"] for p in get_active_physicians()]
                            cur_idx=all_phys.index(r.get("Physician","")) if r.get("Physician","") in all_phys else 0
                            new_phys=st.selectbox("Reassign to",all_phys,index=cur_idx,
                                                   key=f"rp_{r.get('Token_No','')}")
                            if st.form_submit_button("Reassign"):
                                for idx,rec2 in enumerate(st.session_state.records):
                                    if rec2.get("Visit_DateTime")==r.get("Visit_DateTime"):
                                        st.session_state.records[idx]["Physician"]=new_phys
                                        if ws_opd: sheet_upsert(ws_opd,st.session_state.records[idx],
                                                                  ["Patient_ID","Visit_DateTime"])
                                        st.success(f"Reassigned to {new_phys}")
                                        st.rerun()

# ─────────────────────────────────────────────────────────────────
# SHARED: CONSULTATION FORM
# ─────────────────────────────────────────────────────────────────
def render_consultation_tab():
    st.markdown("### Physician Consultation")

    # Case selector for physician — filter to their cases
    if ROLE == "Physician":
        my_records = [r for r in st.session_state.records
                      if r.get("Physician","") == NAME or
                      (r.get("Consultation_Type","")=="On Request" and r.get("Final_ACD_Code",""))]
        # Also include referrals directed to this physician
        ref_pids = [ref.get("Patient_ID","") for ref in st.session_state.referrals
                    if ref.get("To_Physician","")==NAME and
                    ref.get("Status","") not in ("Resolved","Cancelled")]
        for pid_ref in ref_pids:
            for r in st.session_state.records:
                if r.get("Patient_ID","")==pid_ref and r not in my_records:
                    my_records.append(r)
    else:  # Admin
        my_records = st.session_state.records

    rec = st.session_state.rec
    if not rec:
        st.info("No active patient. Load by Patient ID or Mobile below.")
        lc1,lc2=st.columns(2)
        with lc1: lid=st.text_input("Load by Registration Number",key="load_id_t2")
        with lc2: lmob=st.text_input("Load by Mobile Number",key="load_mob_t2")
        if lid or lmob:
            found=find_patient(my_records,pid=lid if lid else None,
                               mobile=lmob if lmob else None)
            if found: st.session_state.rec=found[-1]; st.rerun()
            else: st.warning("Not found in your case list.")
        # Show today's pending cases for quick load
        today=str(date.today())
        pending=[r for r in my_records
                 if str(r.get("Visit_Date","")).startswith(today)
                 and r.get("Status","")=="Awaiting Physician"]
        if pending:
            st.markdown("#### Today's Pending Cases")
            for p in sorted(pending, key=lambda x: (x.get("Triage","")!="Urgent", x.get("Token_No",""))):
                col_a,col_b=st.columns([4,1])
                with col_a:
                    triage_icon="🔴 " if p.get("Triage","")=="Urgent" else ""
                    st.markdown(
                        f'<div class="queue-row-{"urgent" if p.get("Triage")=="Urgent" else "waiting"}">'
                        f'{triage_icon}<b>{p.get("Token_No","")}</b> — '
                        f'{p.get("Patient_Name","")} ({p.get("Age","")} yrs) — '
                        f'<span class="code-big" style="font-size:0.75rem">{p.get("ACD_Code_1","")}</span>'
                        f'</div>', unsafe_allow_html=True)
                with col_b:
                    if st.button("Open",key=f"open_{p.get('Token_No','')}_{p.get('Visit_DateTime','')}"):
                        st.session_state.rec=p; st.rerun()
        return

    # ── Active patient ───────────────────────────────────────────
    # Follow-up notes from previous visit
    prev_fu=[r for r in st.session_state.records
             if r.get("Patient_ID")==rec.get("Patient_ID")
             and r.get("Visit_DateTime")!=rec.get("Visit_DateTime")
             and str(r.get("Followup_Notes","")).strip()]
    if prev_fu:
        last=sorted(prev_fu,key=lambda x: x.get("Visit_DateTime",""))[-1]
        st.markdown(f'<div class="followup-box"><h4>Follow-up Notes from {last.get("Visit_Date","")} '
                    f'(Dx: {last.get("Final_ACD_Code") or last.get("ACD_Code_1","")})</h4>'
                    f'<p>{str(last.get("Followup_Notes","")).replace(chr(10),"<br>")}</p></div>',
                    unsafe_allow_html=True)

    # Patient banner
    with st.expander("Patient Summary",expanded=True):
        b1,b2,b3,b4,b5=st.columns(5)
        b1.metric("Patient", rec.get("Patient_Name","") or rec.get("Patient_ID",""))
        b2.metric("Token",   rec.get("Token_No",""))
        b3.metric("Dept",    rec.get("Department",""))
        b4.metric("Visit #", rec.get("Visit_Count","1"))
        b5.metric("Triage",  rec.get("Triage",""))
        st.write(f"**ID:** {rec.get('Patient_ID','')}  |  **Mobile:** {rec.get('Mobile','')}  |  "
                 f"**Age/Gender:** {rec.get('Age','')} / {rec.get('Gender','')}")
        if rec.get("ACD_Code_1"):
            st.markdown(f'**Provisional:** <span class="code-big">{rec["ACD_Code_1"]}</span>  {rec.get("ACD_Meaning_1","")}',
                        unsafe_allow_html=True)

    # Treatment response (follow-ups)
    if str(rec.get("Visit_Count","1"))!="1":
        st.markdown('<div class="card">',unsafe_allow_html=True)
        section("TREATMENT RESPONSE (Follow-up)")
        tr_def=rec.get("Treatment_Response",TREATMENT_RESPONSE[0])
        tr_idx=TREATMENT_RESPONSE.index(tr_def) if tr_def in TREATMENT_RESPONSE else 0
        treatment_response=st.selectbox("Response to Previous Treatment",TREATMENT_RESPONSE,index=tr_idx,key="tr")
        st.markdown('</div>',unsafe_allow_html=True)
    else:
        treatment_response="Not yet assessed"

    # Modify complaints & diagnosis
    with st.expander("Modify Chief Complaints & Diagnosis (Physician Override)",expanded=False):
        mod_cc=st.text_area("Modified Chief Complaints",value=rec.get("Chief_Complaints",""),key="mod_cc",height=55)
        st.markdown("**Corrected Provisional Diagnosis**")
        _,mod_code1,mod_mean1=acd_widget("mod_s","mod_sel","Search Corrected Diagnosis")
        if not mod_code1: mod_code1=rec.get("ACD_Code_1",""); mod_mean1=rec.get("ACD_Meaning_1","")

    # Vitals
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("1  VITALS & ANTHROPOMETRY")
    v1,v2,v3=st.columns(3)
    with v1:
        height=st.number_input("Height (cm)",50.0,250.0,160.0,step=1.0,key="height")
        weight=st.number_input("Weight (kg)",1.0,300.0,50.0,step=0.5,key="weight")
        bmi_v=weight/((height/100)**2) if height>0 else 0; bmi_c=bmi_cat(bmi_v)
        st.markdown(f'<div class="bmi-box">BMI: {bmi_v:.1f} — {bmi_c}</div>',unsafe_allow_html=True)
    with v2:
        bp_s=st.number_input("BP Systolic",60,250,120,step=1,key="bps")
        bp_d=st.number_input("BP Diastolic",40,160,80,step=1,key="bpd")
    with v3:
        pulse=st.number_input("Pulse (bpm)",30,220,76,step=1,key="pulse")
        temp=st.number_input("Temperature (F)",90.0,108.0,98.6,step=0.1,key="temp")
    vv4,vv5=st.columns(2)
    with vv4: spo2=st.number_input("SpO2 (%)",50,100,98,step=1,key="spo2")
    with vv5: rr=st.number_input("Resp. Rate (/min)",5,60,16,step=1,key="rr")
    other_inv=st.text_area("Other Investigations",key="other_inv",height=50,placeholder="e.g. Hb 11.2; FBS 126")
    st.markdown('</div>',unsafe_allow_html=True)

    # Ashtavidha
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("2  ASHTAVIDHA PARIKSHA")
    a1,a2,a3,a4=st.columns(4)
    with a1: nadi=sel_other("Nadi",NADI_OPT,"nadi"); jihva=sel_other("Jihva",JIHVA_OPT,"jihva")
    with a2: agni=sel_other("Agni",AGNI_OPT,"agni"); mala=sel_other("Mala",MALA_OPT,"mala")
    with a3: mutra=sel_other("Mutra",MUTRA_OPT,"mutra"); sleep=sel_other("Nidra",SLEEP_OPT,"sleep")
    with a4: shabda=sel_other("Shabda",SHABDA_OPT,"shabda"); sparsha=sel_other("Sparsha",SPARSHA_OPT,"sparsha")
    aa5,aa6=st.columns(2)
    with aa5: drik=sel_other("Drik",DRIK_OPT,"drik")
    with aa6: akriti=sel_other("Akriti",AKRITI_OPT,"akriti")
    st.markdown('</div>',unsafe_allow_html=True)

    # Dashavidha
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("3  DASHAVIDHA ATURA PARIKSHA")
    d1,d2,d3=st.columns(3)
    with d1:
        dosha=sel_other("Dosha",DOSHA_OPT,"dosha"); dushya=st.multiselect("Dushya",DUSHYA_OPT,key="dushya")
        bala=sel_other("Bala",BALA_OPT,"bala")
    with d2:
        kala=st.selectbox("Kala",KALA_OPT,key="kala"); satva=sel_other("Satva",SATVA_OPT,"satva")
        satmya=sel_other("Satmya",SATMYA_OPT,"satmya")
    with d3:
        vyasana=sel_other("Vyasana",VYASANA_OPT,"vyasana")
        cprak=st.selectbox("Prakriti (confirm)",PRAKRITI_OPT,
                            index=PRAKRITI_OPT.index(rec.get("Prakriti",PRAKRITI_OPT[0]))
                                  if rec.get("Prakriti") in PRAKRITI_OPT else 0,key="cprak")
    st.markdown('</div>',unsafe_allow_html=True)

    # Final diagnosis
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("4  FINAL DIAGNOSIS")
    pcode=mod_code1 or rec.get("ACD_Code_1",""); pmean=mod_mean1 or rec.get("ACD_Meaning_1","")
    if pcode:
        st.markdown(f"Provisional: <span class='code-big'>{pcode}</span> — {pmean}",unsafe_allow_html=True)
    _,fd_code,fd_mean=acd_widget("fds","fdsel","Search Final Diagnosis")
    use_prov=st.checkbox("Same as Provisional",key="use_prov")
    if use_prov: fd_code=pcode; fd_mean=pmean
    if use_prov and pcode:
        st.markdown(f'<span class="code-big">{fd_code}</span>  {fd_mean}',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)

    # Panchakarma
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("5  PANCHAKARMA TREATMENT PLAN (SAT-I Codes)")
    sparts=[f"<b>{c}:</b> {', '.join([x.split(' — ')[0] for x in st.session_state.get(f'TX_{c}',[])])}"
            for c in ["Purvakarma","Pradhana Karma","Pashchata Karma"]
            if st.session_state.get(f"TX_{c}",[]) ]
    if sparts: st.markdown('<div class="tx-summary">'+"<br>".join(sparts)+"</div>",unsafe_allow_html=True)
    tx_tabs_w=st.tabs(["Purvakarma","Pradhana Karma","Pashchata Karma"])
    for cat,ttab in zip(["Purvakarma","Pradhana Karma","Pashchata Karma"],tx_tabs_w):
        with ttab:
            opts=[f"{nm} — {desc} [{cd}]" for cd,nm,desc in PK_TREATMENTS[cat]]
            cur=[c for c in st.session_state.get(f"TX_{cat}",[]) if c in opts]
            chosen=st.multiselect(f"Select {cat}",options=opts,default=cur,key=f"TX_ms_{cat}")
            st.session_state[f"TX_{cat}"]=chosen
            if chosen:
                st.markdown("**Procedure-wise Comments:**")
                ex=st.session_state.get(f"TX_comments_{cat}",{}); nc={}
                for tx in chosen:
                    code=xcode(tx); name=tx.split(" — ")[0] if " — " in tx else tx
                    st.markdown('<div class="proc-cmt">',unsafe_allow_html=True)
                    cmt=st.text_input(f"{name}  [{code}]",value=ex.get(code,""),
                                       key=f"cmt_{cat}_{code}",placeholder="e.g. with Dhanwantaram taila 45 min")
                    st.markdown('</div>',unsafe_allow_html=True)
                    nc[code]=cmt
                st.session_state[f"TX_comments_{cat}"]=nc
                st.markdown("  ".join([f'<span class="badge">{xcode(t)}</span>' for t in chosen]),unsafe_allow_html=True)
    tx_custom=st.text_input("Additional / Yoga / Pathya",key="tx_custom",placeholder="e.g. Pathya Ahara, Yoga Nidra")
    st.markdown('</div>',unsafe_allow_html=True)

    # Shamana Aushadhi
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("6  SHAMANA AUSHADHI (Internal Medications)")
    ac,rc,_=st.columns([1,1,5])
    with ac:
        if st.button("+ Add Medicine",key="add_med"): st.session_state.med_count+=1; st.rerun()
    with rc:
        if st.session_state.med_count>1 and st.button("- Remove Last",key="rem_med"):
            st.session_state.med_count-=1; st.rerun()
    medicines=[]
    for i in range(1,st.session_state.med_count+1):
        st.markdown(f'<div class="med-row"><div class="med-num">Medicine {i}</div>',unsafe_allow_html=True)
        r1a,r1b,r1c=st.columns([3,2,2])
        with r1a: mname=st.text_input(f"Drug Name {i}",key=f"mn_{i}",placeholder="e.g. Triphala Churna")
        with r1b: mform=custom_sel(f"Dosage Form {i}",DOSAGE_FORMS,f"mf_{i}")
        with r1c: mroute=custom_sel(f"Route {i}",ROUTE_OPTIONS,f"mr_{i}",idx=0)
        r2a,r2b,r2c,r2d,r2e=st.columns([2,2,2,1,1])
        with r2a: mdose=custom_sel(f"Dose {i}",DOSE_OPTIONS,f"md_{i}",ph="e.g. 5g BD")
        with r2b: mtiming=st.selectbox(f"Timing {i}",TIMING_OPTIONS,key=f"mt_{i}")
        with r2c: manupana=custom_sel(f"Anupana {i}",ANUPANA_OPTIONS,f"ma_{i}",idx=0)
        with r2d: mdur_val=st.number_input(f"Duration {i}",min_value=1,max_value=999,value=15,step=1,key=f"mdv_{i}")
        with r2e: mdur_unit=st.selectbox(f"Unit {i}",DURATION_UNIT,index=0,key=f"mdu_{i}")
        prev_m={"form":mform,"dose":mdose,"timing":mtiming,"anupana":manupana,"dur_val":mdur_val,"dur_unit":mdur_unit,"notes":""}
        if mdose and mdose!="— Custom —": st.caption(f"Instruction: {full_instruction(prev_m)}")
        mnotes=st.text_input(f"Notes {i} (optional)",key=f"mno_{i}",placeholder="e.g. avoid in pregnancy")
        st.markdown('</div>',unsafe_allow_html=True)
        if mname.strip():
            medicines.append({"name":mname,"form":mform,"route":mroute,"dose":mdose,
                               "timing":mtiming,"anupana":manupana,"dur_val":mdur_val,"dur_unit":mdur_unit,"notes":mnotes})
    st.markdown('</div>',unsafe_allow_html=True)

    # Lab tests
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("7  LAB TESTS FOR NEXT VISIT")
    lab_tests=st.text_area("Investigations required",key="lab_tests",height=50,placeholder="e.g. CBC, FBS, HbA1c")
    st.markdown('</div>',unsafe_allow_html=True)

    # Instructions + follow-up date
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("8  INSTRUCTIONS / PATHYA & FOLLOW-UP DATE")
    ic1,ic2=st.columns([3,1])
    with ic1: instructions=st.text_area("Patient Instructions",key="instructions",height=75,placeholder="e.g. Avoid cold food\nDrink warm water")
    with ic2:
        followup_date=st.date_input("Next Visit",value=date.today()+timedelta(days=15),key="followup_date")
        st.caption("Default: 15 days")
    st.markdown('</div>',unsafe_allow_html=True)

    # Physician notes
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("9  PHYSICIAN NOTES")
    phys_notes=st.text_area("Clinical observations / referrals",key="phys_notes",height=50,placeholder="Special instructions, referrals...")
    st.markdown('</div>',unsafe_allow_html=True)

    # Follow-up notes
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("10  FOLLOW-UP NOTES (Shown at Next Visit)")
    followup_notes=st.text_area("Notes for review at next visit",key="followup_notes",height=65,
                                 placeholder="e.g. Monitor BP\nCheck HbA1c\nReview Sneha Pana response")
    st.markdown('</div>',unsafe_allow_html=True)

    # Save + PDF
    st.markdown('<div class="card">',unsafe_allow_html=True)
    section("11  SAVE & GENERATE PRESCRIPTIONS")

    def build_r():
        tx_pur=st.session_state.get("TX_Purvakarma",[])
        tx_pra=st.session_state.get("TX_Pradhana Karma",[])
        tx_pas=st.session_state.get("TX_Pashchata Karma",[])
        r=dict(rec)
        r["TX_Purvakarma"]=tx_pur; r["TX_Pradhana Karma"]=tx_pra; r["TX_Pashchata Karma"]=tx_pas
        r["TX_comments_Purvakarma"]=st.session_state.get("TX_comments_Purvakarma",{})
        r["TX_comments_Pradhana Karma"]=st.session_state.get("TX_comments_Pradhana Karma",{})
        r["TX_comments_Pashchata Karma"]=st.session_state.get("TX_comments_Pashchata Karma",{})
        r["TX_Custom"]=st.session_state.get("tx_custom",""); r["Medicines"]=medicines
        r["Lab_Tests"]=st.session_state.get("lab_tests","")
        r["Instructions"]=st.session_state.get("instructions","")
        r["Followup_Date"]=str(st.session_state.get("followup_date",""))
        r["Physician_Notes"]=st.session_state.get("phys_notes","")
        r["Followup_Notes"]=st.session_state.get("followup_notes","")
        r["Height_cm"]=st.session_state.get("height",0); r["Weight_kg"]=st.session_state.get("weight",0)
        r["BMI"]=round(bmi_v,1); r["BMI_Category"]=bmi_c
        r["BP"]=f"{st.session_state.get('bps',120)}/{st.session_state.get('bpd',80)}"
        r["Pulse_bpm"]=st.session_state.get("pulse",76); r["Temp_F"]=st.session_state.get("temp",98.6)
        r["SpO2_pct"]=st.session_state.get("spo2",98)
        r["Chief_Complaints_Modified"]=st.session_state.get("mod_cc","")
        r["ACD_Code_1"]=mod_code1 or rec.get("ACD_Code_1",""); r["ACD_Meaning_1"]=mod_mean1 or rec.get("ACD_Meaning_1","")
        if use_prov: r["Final_ACD_Code"]=pcode; r["Final_ACD_Meaning"]=pmean
        elif fd_code: r["Final_ACD_Code"]=fd_code; r["Final_ACD_Meaning"]=fd_mean
        return r

    def cmt_flat(sel,cmt): return "; ".join([f"{xcode(t)}: {cmt.get(xcode(t),'')}" for t in sel if cmt.get(xcode(t))])

    s1,s2,s3,s4=st.columns(4)
    with s1:
        if st.button("Save Consultation",type="primary",key="save_phys"):
            r=build_r()
            tx_pur=st.session_state.get("TX_Purvakarma",[]); tx_pra=st.session_state.get("TX_Pradhana Karma",[]); tx_pas=st.session_state.get("TX_Pashchata Karma",[])
            cpur=st.session_state.get("TX_comments_Purvakarma",{}); cpra=st.session_state.get("TX_comments_Pradhana Karma",{}); cpas=st.session_state.get("TX_comments_Pashchata Karma",{})
            med_sum="; ".join([f"{m['name']} {m['form']} {m['route']} {m['dose']} {m['timing']} x{m['dur_val']} {m['dur_unit']} Anupana:{m['anupana']}" for m in medicines])
            update={
                "Status":"Completed","Height_cm":r["Height_cm"],"Weight_kg":r["Weight_kg"],
                "BMI":r["BMI"],"BMI_Category":r["BMI_Category"],"BP":r["BP"],"Pulse_bpm":r["Pulse_bpm"],
                "Temp_F":r["Temp_F"],"SpO2_pct":r["SpO2_pct"],"RR_per_min":st.session_state.get("rr",16),
                "Other_Investigation":st.session_state.get("other_inv",""),
                "Nadi":nadi,"Jihva":jihva,"Agni":agni,"Mala":mala,"Mutra":mutra,"Sleep":sleep,
                "Shabda":shabda,"Sparsha":sparsha,"Drik":drik,"Akriti":akriti,"Dosha":dosha,
                "Dushya":", ".join(dushya) if dushya else "","Bala":bala,"Kala":kala,
                "Satva":satva,"Satmya":satmya,"Vyasana":vyasana,"Prakriti_Confirmed":cprak,
                "Treatment_Response":treatment_response,
                "Chief_Complaints_Modified":st.session_state.get("mod_cc",""),
                "ACD_Code_1":r["ACD_Code_1"],"ACD_Meaning_1":r["ACD_Meaning_1"],
                "Final_ACD_Code":r.get("Final_ACD_Code",""),"Final_ACD_Meaning":r.get("Final_ACD_Meaning",""),
                "TX_Purvakarma":"; ".join([s.split(" — ")[0] for s in tx_pur]),
                "TX_Pradhana_Karma":"; ".join([s.split(" — ")[0] for s in tx_pra]),
                "TX_Pashchata_Karma":"; ".join([s.split(" — ")[0] for s in tx_pas]),
                "TX_Comments_Purvakarma":cmt_flat(tx_pur,cpur),"TX_Comments_Pradhana":cmt_flat(tx_pra,cpra),
                "TX_Comments_Pashchata":cmt_flat(tx_pas,cpas),"TX_Custom":st.session_state.get("tx_custom",""),
                "Medicines_Summary":med_sum,"Lab_Tests":st.session_state.get("lab_tests",""),
                "Instructions":st.session_state.get("instructions",""),
                "Followup_Date":str(st.session_state.get("followup_date","")),
                "Physician_Notes":st.session_state.get("phys_notes",""),
                "Followup_Notes":st.session_state.get("followup_notes",""),
            }
            rec.update(update)
            for idx,r2 in enumerate(st.session_state.records):
                if r2.get("Patient_ID")==rec.get("Patient_ID") and r2.get("Visit_DateTime")==rec.get("Visit_DateTime"):
                    st.session_state.records[idx]=rec; break
            if ws_opd: sheet_upsert(ws_opd,rec,["Patient_ID","Visit_DateTime"])
            st.success(f"Saved — {rec.get('Patient_Name','')} | Final: {update.get('Final_ACD_Code','not set')}")
            reset_form(); st.session_state.pid_counter+=1; st.rerun()

    with s2:
        r_rx=build_r(); pdf_rx=make_pdf(r_rx,mode="rx")
        st.download_button("Prescription Only",data=pdf_rx,
                            file_name=f"Rx_{rec.get('Patient_ID','PT')}_{date.today()}.pdf",
                            mime="application/pdf",key="dl_rx")
    with s3:
        has_pk=any(st.session_state.get(f"TX_{c}",[]) for c in ["Purvakarma","Pradhana Karma","Pashchata Karma"])
        if has_pk:
            r_pk=build_r(); pdf_pk_buf=make_pdf(r_pk,mode="pk")
            st.download_button("PK Advice Only",data=pdf_pk_buf,
                                file_name=f"PK_{rec.get('Patient_ID','PT')}_{date.today()}.pdf",
                                mime="application/pdf",key="dl_pk")
        else: st.caption("Select PK procedures to enable.")
    with s4:
        r_b=build_r(); pdf_b=make_pdf(r_b,mode="both")
        st.download_button("Full Document",data=pdf_b,
                            file_name=f"Full_{rec.get('Patient_ID','PT')}_{date.today()}.pdf",
                            mime="application/pdf",key="dl_both")
    st.markdown('</div>',unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# REFERRALS TAB
# ─────────────────────────────────────────────────────────────────
def render_referrals_tab():
    st.markdown("### Cross Referrals")

    ref_tabs = st.tabs(["Referrals IN", "Refer a Patient", "Referrals OUT"])

    # ── Referrals IN ─────────────────────────────────────────────
    with ref_tabs[0]:
        st.markdown("#### Cases Referred To Me")
        if ROLE=="Admin":
            my_in=[r for r in st.session_state.referrals]
        else:
            my_in=[r for r in st.session_state.referrals if r.get("To_Physician","")==NAME]
        pending_in=[r for r in my_in if r.get("Status","")=="Pending"]
        done_in   =[r for r in my_in if r.get("Status","")!="Pending"]
        if not my_in:
            st.info("No referrals received.")
        for ref in sorted(pending_in, key=lambda x: (x.get("Priority","")!="Emergency",
                                                       x.get("Priority","")!="Urgent",x.get("Date",""))):
            priority=ref.get("Priority","Routine")
            css="referral-in" + (" referral-urgent" if priority in ("Urgent","Emergency") else "")
            pri_icon={"Emergency":"🚨","Urgent":"⚠️","Routine":"📋"}.get(priority,"📋")
            st.markdown(
                f'<div class="{css}">'
                f'{pri_icon} <b>{priority}</b> &nbsp;|&nbsp; '
                f'<b>{ref.get("Patient_Name","")}</b> ({ref.get("Patient_ID","")}) &nbsp;|&nbsp; '
                f'Token: {ref.get("Token_No","")} &nbsp;|&nbsp; '
                f'From: <b>{ref.get("From_Physician","")}</b> ({ref.get("From_Dept","")}) &nbsp;|&nbsp; '
                f'Date: {ref.get("Date","")} &nbsp;|&nbsp; Status: <b>{ref.get("Status","")}</b>'
                f'<br><i>Reason: {ref.get("Reason","")}</i>'
                f'</div>', unsafe_allow_html=True)
            col_a,col_b,col_c=st.columns(3)
            with col_a:
                if st.button("Accept",key=f"acc_{ref.get('Referral_ID','')}"):
                    for i,r in enumerate(st.session_state.referrals):
                        if r.get("Referral_ID","")==ref.get("Referral_ID",""):
                            st.session_state.referrals[i]["Status"]="Accepted"
                            if ws_ref: sheet_upsert(ws_ref,st.session_state.referrals[i],["Referral_ID"])
                    st.rerun()
            with col_b:
                if st.button("Load Patient",key=f"load_ref_{ref.get('Referral_ID','')}"):
                    found=find_patient(st.session_state.records,pid=ref.get("Patient_ID",""))
                    if found: st.session_state.rec=found[-1]; st.rerun()
            with col_c:
                res_note=st.text_input(f"Resolution note",key=f"rn_{ref.get('Referral_ID','')}",
                                        placeholder="Brief note on action taken")
                if st.button("Mark Resolved",key=f"res_{ref.get('Referral_ID','')}"):
                    for i,r in enumerate(st.session_state.referrals):
                        if r.get("Referral_ID","")==ref.get("Referral_ID",""):
                            st.session_state.referrals[i]["Status"]="Resolved"
                            st.session_state.referrals[i]["Resolved_Date"]=str(date.today())
                            st.session_state.referrals[i]["Resolved_Notes"]=res_note
                            if ws_ref: sheet_upsert(ws_ref,st.session_state.referrals[i],["Referral_ID"])
                    st.rerun()
        if done_in:
            with st.expander(f"Resolved / Past Referrals ({len(done_in)})"):
                for ref in done_in:
                    st.markdown(f"**{ref.get('Date','')}** — {ref.get('Patient_Name','')} — "
                                f"From: {ref.get('From_Physician','')} — Status: {ref.get('Status','')}")

    # ── Refer a Patient ──────────────────────────────────────────
    with ref_tabs[1]:
        st.markdown("#### Send a Referral")
        rc1,rc2=st.columns(2)
        with rc1:
            ref_pid=st.text_input("Patient ID",key="ref_pid",placeholder="Enter patient ID")
            ref_pat_name=""
            if ref_pid:
                found=find_patient(st.session_state.records,pid=ref_pid)
                if found:
                    ref_pat_name=found[-1].get("Patient_Name","")
                    ref_tok=found[-1].get("Token_No","")
                    st.success(f"Found: {ref_pat_name} | Token: {ref_tok}")
                else:
                    st.warning("Patient not found.")
                    ref_tok=""
        with rc2:
            all_active_phys=[p["Name"] for p in get_active_physicians() if p["Name"]!=NAME]
            to_phys=st.selectbox("Refer To (Physician)",["— Select —"]+all_active_phys,key="ref_to_phys")
        to_dept=""
        if to_phys!="— Select —":
            mp=get_physician_record(to_phys)
            if mp: to_dept=str(mp.get("Departments","")).split(",")[0].strip()
            st.caption(f"Department: {dept_lbl(to_dept) if to_dept else ''}")
        ref_reason=st.text_area("Reason for Referral",key="ref_reason",height=70,
                                 placeholder="e.g. For Panchakarma evaluation of Kati Basti for L4-L5 disc prolapse")
        ref_priority=st.selectbox("Priority",REFERRAL_PRIORITY,key="ref_priority")
        if st.button("Send Referral",type="primary",key="send_ref"):
            if not ref_pid or not ref_pat_name:
                st.error("Enter a valid Patient ID first.")
            elif to_phys=="— Select —":
                st.error("Select a physician to refer to.")
            elif not ref_reason:
                st.error("Please enter a reason for referral.")
            else:
                from_dept=""
                mp_self=get_physician_record(NAME)
                if mp_self: from_dept=str(mp_self.get("Departments","")).split(",")[0].strip()
                ref_id=f"REF-{date.today()}-{len(st.session_state.referrals)+1:04d}"
                new_ref={
                    "Referral_ID":ref_id,"Date":str(date.today()),
                    "Time":datetime.now().strftime("%H:%M:%S"),
                    "From_Physician":NAME,"From_Dept":from_dept,
                    "To_Physician":to_phys,"To_Dept":to_dept,
                    "Patient_ID":ref_pid,"Patient_Name":ref_pat_name,
                    "Token_No":ref_tok if ref_pid else "",
                    "Reason":ref_reason,"Priority":ref_priority,
                    "Status":"Pending","Notes":"","Resolved_Date":"","Resolved_Notes":"",
                }
                st.session_state.referrals.append(new_ref)
                if ws_ref: sheet_append(ws_ref, new_ref, REF_COLS)
                st.success(f"Referral sent to {to_phys} | ID: {ref_id}")

    # ── Referrals OUT ─────────────────────────────────────────────
    with ref_tabs[2]:
        st.markdown("#### Referrals I Sent")
        if ROLE=="Admin":
            my_out=st.session_state.referrals
        else:
            my_out=[r for r in st.session_state.referrals if r.get("From_Physician","")==NAME]
        if not my_out:
            st.info("No referrals sent yet.")
        for ref in sorted(my_out, key=lambda x: x.get("Date",""), reverse=True):
            status=ref.get("Status",""); priority=ref.get("Priority","")
            status_color={"Pending":"#fef3c7","Accepted":"#e8f4fd",
                           "Resolved":"#dcfce7","Consultation Done":"#e8f5e9"}.get(status,"#f5f5f5")
            st.markdown(
                f'<div style="background:{status_color};border-radius:7px;padding:8px 12px;margin:4px 0;">'
                f'<b>{ref.get("Date","")}</b> &nbsp;|&nbsp; '
                f'{ref.get("Patient_Name","")} ({ref.get("Patient_ID","")}) &nbsp;|&nbsp; '
                f'To: <b>{ref.get("To_Physician","")}</b> &nbsp;|&nbsp; '
                f'Priority: <b>{priority}</b> &nbsp;|&nbsp; Status: <b>{status}</b>'
                f'{("<br><i>Resolution: " + ref.get("Resolved_Notes","") + "</i>") if ref.get("Resolved_Notes","") else ""}'
                f'</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# PHYSICIAN MANAGEMENT (Admin only)
# ─────────────────────────────────────────────────────────────────
def render_physician_mgmt():
    st.markdown("### Physician Management")

    pm_tabs=st.tabs(["Active Physicians","Add New Physician","Deactivated"])

    with pm_tabs[0]:
        st.markdown("#### Active Physicians")
        active=[p for p in st.session_state.physicians if str(p.get("Status","Active"))=="Active"]
        for p in sorted(active, key=lambda x: x.get("Name","")):
            col_a,col_b,col_c,col_d=st.columns([3,2,1,1])
            with col_a:
                role_tag={"Admin":"🔴 Admin","Physician":"🔵 Physician",
                           "Receptionist":"🟢 Receptionist"}.get(str(p.get("Role","")),"")
                st.markdown(f"**{p.get('Name','')}** &nbsp; {role_tag}")
                st.caption(f"Depts: {p.get('Departments','')}")
            with col_b:
                pin_status="PIN set" if str(p.get("PIN_Changed","No"))=="Yes" else "⚠️ Default PIN"
                st.caption(pin_status)
            with col_c:
                if st.button("Reset PIN",key=f"rpin_{p.get('Name','')}"):
                    for i,ph in enumerate(st.session_state.physicians):
                        if ph.get("Name","")==p.get("Name",""):
                            st.session_state.physicians[i]["PIN_Hash"]=HASH_DEFAULT_PHYS
                            st.session_state.physicians[i]["PIN_Changed"]="No"
                            if ws_phys: sheet_upsert(ws_phys,st.session_state.physicians[i],["Name"])
                    st.success(f"PIN reset to 1234 for {p.get('Name','')}")
                    st.rerun()
            with col_d:
                if p.get("Name","")!=NAME:  # Can't deactivate yourself
                    if st.button("Deactivate",key=f"deact_{p.get('Name','')}"):
                        for i,ph in enumerate(st.session_state.physicians):
                            if ph.get("Name","")==p.get("Name",""):
                                st.session_state.physicians[i]["Status"]="Inactive"
                                if ws_phys: sheet_upsert(ws_phys,st.session_state.physicians[i],["Name"])
                        st.success(f"{p.get('Name','')} deactivated.")
                        st.rerun()

    with pm_tabs[1]:
        st.markdown("#### Add New Physician / Staff")
        na1,na2=st.columns(2)
        with na1:
            new_name=st.text_input("Full Name",key="new_phys_name",placeholder="e.g. Dr. Ramesh Kumar")
            new_role=st.selectbox("Role",["Physician","Receptionist","Admin"],key="new_role")
        with na2:
            new_depts=st.multiselect("Departments",list(DEPARTMENTS.keys()),
                                      format_func=dept_lbl,key="new_depts")
            new_pin=st.text_input("Set Initial PIN (min 4 digits)",type="password",
                                   key="new_pin",placeholder="e.g. 5678")
        if st.button("Add Physician",type="primary",key="add_phys"):
            if not new_name.strip():
                st.error("Enter a name.")
            elif not new_pin or len(new_pin)<4 or not new_pin.isdigit():
                st.error("PIN must be at least 4 digits.")
            elif any(p["Name"]==new_name.strip() for p in st.session_state.physicians):
                st.error("Physician with this name already exists.")
            else:
                new_entry={"Name":new_name.strip(),
                           "Departments":",".join(new_depts) if new_depts else "ALL",
                           "PIN_Hash":hash_pin(new_pin),"Role":new_role,
                           "Status":"Active","PIN_Changed":"Yes","Added_Date":str(date.today())}
                st.session_state.physicians.append(new_entry)
                if ws_phys: sheet_append(ws_phys,new_entry,PHYS_COLS)
                st.success(f"Added {new_name.strip()} as {new_role}.")
                st.rerun()

    with pm_tabs[2]:
        st.markdown("#### Deactivated / Former Physicians")
        inactive=[p for p in st.session_state.physicians if str(p.get("Status",""))=="Inactive"]
        if not inactive:
            st.info("No deactivated physicians.")
        for p in inactive:
            col_a,col_b=st.columns([4,1])
            with col_a: st.markdown(f"**{p.get('Name','')}**  |  {p.get('Departments','')}  |  Role: {p.get('Role','')}")
            with col_b:
                if st.button("Reactivate",key=f"react_{p.get('Name','')}"):
                    for i,ph in enumerate(st.session_state.physicians):
                        if ph.get("Name","")==p.get("Name",""):
                            st.session_state.physicians[i]["Status"]="Active"
                            if ws_phys: sheet_upsert(ws_phys,st.session_state.physicians[i],["Name"])
                    st.success(f"{p.get('Name','')} reactivated.")
                    st.rerun()

# ─────────────────────────────────────────────────────────────────
# ROUTE TO CORRECT TABS BY ROLE
# ─────────────────────────────────────────────────────────────────
if ROLE == "Receptionist":
    with tabs[0]: render_reception_tab()
    with tabs[1]: render_queue_tab()

elif ROLE == "Physician":
    with tabs[0]: render_consultation_tab()
    with tabs[1]: render_referrals_tab()

else:  # Admin
    with tabs[0]: render_reception_tab()
    with tabs[1]: render_consultation_tab()
    with tabs[2]: render_referrals_tab()
    with tabs[3]: render_physician_mgmt()

# ─────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### SKAMCSHRC OPD v9.0")
    st.markdown(f"**Logged in:** {NAME}")
    role_clr={"Admin":"#1a3a2a","Physician":"#1565c0","Receptionist":"#2e7d32"}.get(ROLE,"#333")
    st.markdown(f'<span style="background:{role_clr};color:white;border-radius:5px;padding:3px 10px;font-size:0.8rem;font-weight:700">{ROLE}</span>',unsafe_allow_html=True)
    if GS_OK: st.success("Google Sheets connected")
    else:
        if gs_err: st.error(f"GS: {gs_err[:80]}")
        else: st.warning("Not configured")

    # Switch User
    if st.button("Switch User / Logout", key="logout"):
        for k in ["logged_in","user_role","user_name","force_pin_change",
                  "login_attempts","lockout_until","last_activity","rec"]:
            st.session_state[k] = False if k=="logged_in" else None
        reset_form()
        st.rerun()

    st.markdown("---")

    # Quick patient search
    st.markdown("### Patient Search")
    qs=st.text_input("ID or Mobile",key="qs_sb")
    if qs:
        hits=find_patient(st.session_state.records,
                          pid=qs if not (len(qs)==10 and qs.isdigit()) else None,
                          mobile=qs if len(qs)==10 and qs.isdigit() else None)
        if hits:
            st.success(f"{len(hits)} visit(s) found")
            for v in hits[-3:]:
                st.markdown(f"**{v.get('Visit_Date','')}** — `{v.get('Final_ACD_Code') or v.get('ACD_Code_1','')}` {v.get('Department','')}")
        elif qs: st.info("Not found.")

    st.markdown("---")
    st.markdown("### Records & Export")
    st.write(f"**Total: {len(st.session_state.records)} records**")

    # Date filter
    df1,df2=st.columns(2)
    with df1: d_from=st.date_input("From",value=date.today()-timedelta(days=30),key="d_from")
    with df2: d_to  =st.date_input("To",  value=date.today(),key="d_to")

    # Physician filter for admin
    if ROLE=="Admin":
        all_phys_names=["All Physicians"]+sorted(set(r.get("Physician","") for r in st.session_state.records if r.get("Physician","")))
        phys_filter=st.selectbox("Filter by Physician",all_phys_names,key="phys_filter_sb")
    else:
        phys_filter=NAME

    filtered=[r for r in st.session_state.records
              if str(d_from)<=str(r.get("Visit_Date",""))<=str(d_to)
              and (phys_filter in ("All Physicians","") or r.get("Physician","")==phys_filter)]
    st.write(f"Filtered: **{len(filtered)} records**")

    if filtered:
        skip={"TX_Purvakarma","TX_Pradhana Karma","TX_Pashchata Karma",
              "TX_comments_Purvakarma","TX_comments_Pradhana Karma","TX_comments_Pashchata Karma","Medicines"}
        ecols=[c for c in OPD_COLS if c not in skip]
        df_exp=pd.DataFrame([{k:clean(str(r.get(k,""))) for k in ecols} for r in filtered])
        buf=io.BytesIO()
        with pd.ExcelWriter(buf,engine="openpyxl") as w:
            df_exp.to_excel(w,index=False,sheet_name="OPD_Records")
        buf.seek(0)
        st.download_button("Download Excel",data=buf,
                            file_name=f"SKAMCSHRC_{d_from}_{d_to}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        csv_d=df_exp.to_csv(index=False).encode("utf-8-sig")
        st.download_button("Download CSV",data=csv_d,
                            file_name=f"SKAMCSHRC_{d_from}_{d_to}.csv",mime="text/csv")

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.72rem;color:#888'>"
        "Conceptized by: Dr. Kiran M Goud, MD (Ay.)<br>"
        "Developed by: Dr. Prasanna Kulkarni, MD (Ay.), MS (DS)"
        "</div>",unsafe_allow_html=True)

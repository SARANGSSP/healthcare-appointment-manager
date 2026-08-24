"""
seed_demo.py — Standalone demo data seeder for Healthcare Appointment Manager.

Run from the backend/ directory:
    python seed_demo.py

Safe to run multiple times — skips if demo data already exists.
All demo accounts use password: Demo@1234
"""
import os
import sys
import bcrypt
from datetime import date, time, datetime, timezone, timedelta

# Bootstrap Flask app
sys.path.insert(0, os.path.dirname(__file__))
from app import create_app, db
from app.models.user import User
from app.models.doctor_profile import DoctorProfile
from app.models.patient_profile import PatientProfile
from app.models.appointment import Appointment
from app.models.symptom_summary import SymptomSummary
from app.models.visit_note import VisitNote
from app.models.prescription_item import PrescriptionItem
from app.models.medication_reminder import MedicationReminder
from app.models.notification import Notification

app = create_app()

# ---------------------------------------------------------------------------
# Demo data definitions
# ---------------------------------------------------------------------------

DEMO_PASSWORD = bcrypt.hashpw(b"Demo@1234", bcrypt.gensalt()).decode("utf-8")
TODAY = date.today()
NOW = datetime.now(timezone.utc)


DOCTORS = [
    {
        "email": "dr.sarah.johnson@healthdemo.com",
        "full_name": "Dr. Sarah Johnson",
        "specialisation": "Cardiology",
        "working_hours": {"mon": ["09:00-13:00", "14:00-17:00"], "tue": ["09:00-13:00", "14:00-17:00"], "wed": ["09:00-13:00"], "thu": ["09:00-13:00", "14:00-17:00"], "fri": ["09:00-12:00"]},
        "slot_duration_minutes": 20,
    },
    {
        "email": "dr.michael.chen@healthdemo.com",
        "full_name": "Dr. Michael Chen",
        "specialisation": "Orthopedics",
        "working_hours": {"mon": ["10:00-14:00"], "tue": ["10:00-14:00", "15:00-18:00"], "wed": ["10:00-14:00", "15:00-18:00"], "thu": ["10:00-14:00"], "fri": ["10:00-13:00"]},
        "slot_duration_minutes": 30,
    },
    {
        "email": "dr.emily.rodriguez@healthdemo.com",
        "full_name": "Dr. Emily Rodriguez",
        "specialisation": "General Practice",
        "working_hours": {"mon": ["08:00-12:00", "13:00-17:00"], "tue": ["08:00-12:00", "13:00-17:00"], "wed": ["08:00-12:00"], "thu": ["08:00-12:00", "13:00-17:00"], "fri": ["08:00-12:00"]},
        "slot_duration_minutes": 15,
    },
    {
        "email": "dr.james.wilson@healthdemo.com",
        "full_name": "Dr. James Wilson",
        "specialisation": "Neurology",
        "working_hours": {"mon": ["09:00-13:00"], "wed": ["09:00-13:00", "14:00-17:00"], "fri": ["09:00-13:00"]},
        "slot_duration_minutes": 30,
    },
    {
        "email": "dr.priya.sharma@healthdemo.com",
        "full_name": "Dr. Priya Sharma",
        "specialisation": "Dermatology",
        "working_hours": {"tue": ["09:00-13:00", "14:00-17:00"], "thu": ["09:00-13:00", "14:00-17:00"], "sat": ["09:00-13:00"]},
        "slot_duration_minutes": 20,
    },
    {
        "email": "dr.david.okafor@healthdemo.com",
        "full_name": "Dr. David Okafor",
        "specialisation": "Psychiatry",
        "working_hours": {"mon": ["10:00-14:00", "15:00-18:00"], "tue": ["10:00-14:00"], "thu": ["10:00-14:00", "15:00-18:00"], "fri": ["10:00-14:00"]},
        "slot_duration_minutes": 45,
    },
    {
        "email": "dr.lisa.park@healthdemo.com",
        "full_name": "Dr. Lisa Park",
        "specialisation": "Pediatrics",
        "working_hours": {"mon": ["09:00-13:00", "14:00-17:00"], "tue": ["09:00-13:00", "14:00-17:00"], "wed": ["09:00-13:00", "14:00-17:00"], "thu": ["09:00-13:00"], "fri": ["09:00-12:00"]},
        "slot_duration_minutes": 20,
    },
    {
        "email": "dr.ahmed.hassan@healthdemo.com",
        "full_name": "Dr. Ahmed Hassan",
        "specialisation": "Endocrinology",
        "working_hours": {"mon": ["09:00-13:00"], "wed": ["09:00-13:00", "14:00-16:00"], "thu": ["09:00-13:00", "14:00-16:00"], "fri": ["09:00-12:00"]},
        "slot_duration_minutes": 30,
    },
    {
        "email": "dr.natasha.petrov@healthdemo.com",
        "full_name": "Dr. Natasha Petrov",
        "specialisation": "Oncology",
        "working_hours": {"mon": ["08:00-12:00", "13:00-16:00"], "tue": ["08:00-12:00", "13:00-16:00"], "thu": ["08:00-12:00", "13:00-16:00"]},
        "slot_duration_minutes": 40,
    },
    {
        "email": "dr.carlos.mendez@healthdemo.com",
        "full_name": "Dr. Carlos Mendez",
        "specialisation": "Gastroenterology",
        "working_hours": {"tue": ["09:00-13:00", "14:00-17:00"], "wed": ["09:00-13:00"], "fri": ["09:00-13:00", "14:00-17:00"]},
        "slot_duration_minutes": 30,
    },
    {
        "email": "dr.yuki.tanaka@healthdemo.com",
        "full_name": "Dr. Yuki Tanaka",
        "specialisation": "Ophthalmology",
        "working_hours": {"mon": ["10:00-14:00"], "wed": ["10:00-14:00", "15:00-17:00"], "thu": ["10:00-14:00"], "fri": ["10:00-14:00"]},
        "slot_duration_minutes": 20,
    },
    {
        "email": "dr.amara.diallo@healthdemo.com",
        "full_name": "Dr. Amara Diallo",
        "specialisation": "Obstetrics & Gynaecology",
        "working_hours": {"mon": ["08:00-12:00", "13:00-17:00"], "tue": ["08:00-12:00", "13:00-17:00"], "thu": ["08:00-12:00", "13:00-17:00"], "fri": ["08:00-12:00"]},
        "slot_duration_minutes": 30,
    },
]

PATIENTS = [
    {"email": "john.smith@demo.com",        "full_name": "John Smith",        "phone": "+1-555-0101", "dob": date(1985,  3, 15)},
    {"email": "mary.williams@demo.com",     "full_name": "Mary Williams",     "phone": "+1-555-0102", "dob": date(1990,  7, 22)},
    {"email": "robert.brown@demo.com",      "full_name": "Robert Brown",      "phone": "+1-555-0103", "dob": date(1978, 11,  8)},
    {"email": "jennifer.davis@demo.com",    "full_name": "Jennifer Davis",    "phone": "+1-555-0104", "dob": date(1995,  1, 30)},
    {"email": "william.jones@demo.com",     "full_name": "William Jones",     "phone": "+1-555-0105", "dob": date(1960,  6, 14)},
    {"email": "linda.garcia@demo.com",      "full_name": "Linda Garcia",      "phone": "+1-555-0106", "dob": date(1988,  9,  5)},
    {"email": "charles.miller@demo.com",    "full_name": "Charles Miller",    "phone": "+1-555-0107", "dob": date(1972,  4, 19)},
    {"email": "patricia.wilson@demo.com",   "full_name": "Patricia Wilson",   "phone": "+1-555-0108", "dob": date(2000,  2, 28)},
    {"email": "thomas.moore@demo.com",      "full_name": "Thomas Moore",      "phone": "+1-555-0109", "dob": date(1968, 12,  3)},
    {"email": "barbara.taylor@demo.com",    "full_name": "Barbara Taylor",    "phone": "+1-555-0110", "dob": date(1993,  8, 17)},
    {"email": "james.anderson@demo.com",    "full_name": "James Anderson",    "phone": "+1-555-0111", "dob": date(1955, 10, 25)},
    {"email": "susan.thomas@demo.com",      "full_name": "Susan Thomas",      "phone": "+1-555-0112", "dob": date(1982,  5, 11)},
    {"email": "christopher.lee@demo.com",   "full_name": "Christopher Lee",   "phone": "+1-555-0113", "dob": date(1975,  8, 20)},
    {"email": "amanda.white@demo.com",      "full_name": "Amanda White",      "phone": "+1-555-0114", "dob": date(1998,  3,  7)},
    {"email": "daniel.harris@demo.com",     "full_name": "Daniel Harris",     "phone": "+1-555-0115", "dob": date(1963,  1, 18)},
    {"email": "lisa.martinez@demo.com",     "full_name": "Lisa Martinez",     "phone": "+1-555-0116", "dob": date(1987, 11, 29)},
    {"email": "mark.thompson@demo.com",     "full_name": "Mark Thompson",     "phone": "+1-555-0117", "dob": date(1970,  7,  4)},
    {"email": "nancy.jackson@demo.com",     "full_name": "Nancy Jackson",     "phone": "+1-555-0118", "dob": date(2002,  5, 16)},
    {"email": "kevin.clark@demo.com",       "full_name": "Kevin Clark",       "phone": "+1-555-0119", "dob": date(1958,  9, 12)},
    {"email": "dorothy.lewis@demo.com",     "full_name": "Dorothy Lewis",     "phone": "+1-555-0120", "dob": date(1945,  4,  3)},
]

# (patient_idx, doctor_idx, days_offset, slot_start, slot_end, status)
APPOINTMENTS_SPEC = [
    # --- Completed (past) ---
    (0,  0, -30, time(9,  0), time(9,  20), "completed"),
    (1,  2, -28, time(8,  0), time(8,  15), "completed"),
    (2,  1, -25, time(10, 0), time(10, 30), "completed"),
    (3,  3, -22, time(9,  0), time(9,  30), "completed"),
    (4,  0, -20, time(14, 0), time(14, 20), "completed"),
    (5,  2, -18, time(8,  0), time(8,  15), "completed"),
    (6,  4, -16, time(9,  0), time(9,  20), "completed"),
    (7,  5, -14, time(10, 0), time(10, 45), "completed"),
    (8,  0, -12, time(9,  20),time(9,  40), "completed"),
    (9,  2, -10, time(9,  0), time(9,  15), "completed"),
    (10, 1, -8,  time(10, 30),time(11,  0), "completed"),
    (11, 3, -7,  time(9,  30),time(10,  0), "completed"),
    (0,  4, -5,  time(14, 0), time(14, 20), "completed"),
    (1,  0, -4,  time(9,  40),time(10,  0), "completed"),
    (2,  2, -3,  time(13, 0), time(13, 15), "completed"),
    # --- Cancelled ---
    (3,  1, -20, time(11, 0), time(11, 30), "cancelled"),
    (4,  4, -15, time(14, 0), time(14, 20), "cancelled"),
    (5,  3, -10, time(9,  0), time(9,  30), "cancelled"),
    (6,  2, -6,  time(8,  0), time(8,  15), "cancelled"),
    (7,  0, -3,  time(14, 20),time(14, 40), "cancelled"),
    # --- Upcoming confirmed ---
    (0,  0,  1,  time(9,   0), time(9,  20), "confirmed"),
    (1,  2,  2,  time(8,   0), time(8,  15), "confirmed"),
    (2,  1,  3,  time(10,  0), time(10, 30), "confirmed"),
    (3,  3,  4,  time(9,   0), time(9,  30), "confirmed"),
    (4,  5,  5,  time(10,  0), time(10, 45), "confirmed"),
    (5,  0,  6,  time(9,  20), time(9,  40), "confirmed"),
    (6,  4,  7,  time(9,   0), time(9,  20), "confirmed"),
    (7,  2,  8,  time(13,  0), time(13, 15), "confirmed"),
    (8,  1,  9,  time(11,  0), time(11, 30), "confirmed"),
    (9,  0, 12,  time(14,  0), time(14, 20), "confirmed"),
    (10, 3, 14,  time(9,   0), time(9,  30), "confirmed"),
    (11, 5,  16, time(15,  0), time(15, 45), "confirmed"),
    (0,  2,  18, time(8,   0), time(8,  15), "confirmed"),
    (1,  4,  20, time(14,  0), time(14, 20), "confirmed"),
    (2,  0,  22, time(9,  40), time(10,  0), "confirmed"),
    # Extra completed — covering new doctors (6–11)
    (12, 6,  -28, time(9,  0), time(9,  20), "completed"),   # Christopher → Pediatrics
    (13, 7,  -26, time(9,  0), time(9,  30), "completed"),   # Amanda → Endocrinology
    (14, 8,  -24, time(8,  0), time(8,  40), "completed"),   # Daniel → Oncology
    (15, 9,  -22, time(9,  0), time(9,  30), "completed"),   # Lisa → Gastroenterology
    (16, 10, -20, time(10, 0), time(10, 20), "completed"),   # Mark → Ophthalmology
    (17, 11, -18, time(8,  0), time(8,  30), "completed"),   # Nancy → OB/GYN
    (18, 6,  -15, time(9, 20), time(9,  40), "completed"),   # Kevin → Pediatrics
    (19, 7,  -13, time(9, 30), time(10,  0), "completed"),   # Dorothy → Endocrinology
    (12, 8,  -11, time(13, 0), time(13, 40), "completed"),   # Christopher → Oncology
    (13, 9,  -9,  time(14, 0), time(14, 30), "completed"),   # Amanda → Gastroenterology
    (14, 10, -6,  time(10, 0), time(10, 20), "completed"),   # Daniel → Ophthalmology
    (15, 11, -4,  time(8,  0), time(8,  30), "completed"),   # Lisa → OB/GYN
    # Extra cancelled — new doctors
    (16, 6,  -18, time(14, 0), time(14, 20), "cancelled"),
    (17, 9,  -12, time(9,  0), time(9,  30), "cancelled"),
    (18, 11, -7,  time(13, 0), time(13, 30), "cancelled"),
    # Extra upcoming confirmed — new doctors & patients
    (12, 6,   3,  time(9,  0), time(9,  20), "confirmed"),
    (13, 7,   4,  time(9,  0), time(9,  30), "confirmed"),
    (14, 8,   6,  time(8,  0), time(8,  40), "confirmed"),
    (15, 9,   8,  time(9,  0), time(9,  30), "confirmed"),
    (16, 10, 10,  time(10, 0), time(10, 20), "confirmed"),
    (17, 11, 12,  time(8,  0), time(8,  30), "confirmed"),
    (18, 6,  14,  time(9, 20), time(9,  40), "confirmed"),
    (19, 7,  16,  time(9, 30), time(10,  0), "confirmed"),
    (0,  8,  19,  time(13, 0), time(13, 40), "confirmed"),
    (1,  9,  21,  time(14, 0), time(14, 30), "confirmed"),
    (2,  10, 24,  time(10, 0), time(10, 20), "confirmed"),
    (3,  11, 26,  time(8,  0), time(8,  30), "confirmed"),
]

# Symptom summaries for completed appointments (indexed by APPOINTMENTS_SPEC order)
SYMPTOM_SUMMARIES = {
    0:  ("Chest tightness and shortness of breath on exertion for 2 weeks.",      "Medium", "Exertional chest tightness",       ["Is it worse at rest?", "Any family history of heart disease?", "Any recent stress?"]),
    1:  ("Persistent cough with mild fever for 5 days.",                           "Low",    "Upper respiratory infection",      ["Is the cough productive?", "Any sore throat?", "Any recent travel?"]),
    2:  ("Left knee pain after playing football, swelling noted.",                 "Medium", "Acute knee injury",                ["When exactly did it start?", "Can you bear weight?", "Any previous knee issues?"]),
    3:  ("Recurring headaches, 3 times this week, mild visual disturbances.",      "High",   "Recurrent migraines with aura",    ["How long do they last?", "Any triggers identified?", "Any nausea or vomiting?"]),
    4:  ("Irregular heartbeat sensation noticed for 3 days, no chest pain.",       "High",   "Palpitations, possible arrhythmia",["How frequent are episodes?", "Any dizziness with episodes?", "Caffeine or stimulant intake?"]),
    5:  ("Sore throat and difficulty swallowing for 2 days.",                      "Low",    "Acute pharyngitis",                ["Any white patches on throat?", "Fever?", "Close contact with sick person?"]),
    6:  ("Skin rash on arms, itchy and red for 1 week.",                           "Low",    "Contact dermatitis",               ["Any new soaps or detergents?", "Does anything make it worse?", "Any similar episodes?"]),
    7:  ("Low mood, sleep disturbances, lack of motivation for 3 months.",         "High",   "Depression symptoms",              ["Any suicidal ideation?", "How is work/social life affected?", "Any prior mental health history?"]),
    8:  ("Chest pain on left side radiating to arm, sweating.",                    "High",   "Chest pain with radiation",        ["Duration of current episode?", "Any prior cardiac history?", "Any medications taken?"]),
    9:  ("Mild back pain, worse in the morning, improves with movement.",          "Low",    "Mechanical lower back pain",       ["Any bladder or bowel changes?", "Any injury recently?", "What relieves it?"]),
    10: ("Right shoulder pain after heavy lifting, limited range of motion.",      "Medium", "Shoulder strain/rotator cuff",     ["Point to the exact location?", "Any weakness in arm?", "Any prior injury?"]),
    11: ("Numbness in fingers of left hand, dropping objects frequently.",         "High",   "Peripheral neuropathy symptoms",   ["When did symptoms start?", "Bilateral or unilateral?", "Any diabetes or thyroid issues?"]),
    12: ("Sudden rash with hives, mild throat swelling after eating.",             "High",   "Allergic reaction",                ["What food was consumed?", "Any known allergies?", "Any difficulty breathing?"]),
    13: ("Blood pressure check, readings at home: 148/95.",                        "Medium", "Hypertension monitoring",          ["Currently on any BP meds?", "Diet and salt intake?", "Family history of hypertension?"]),
    14: ("Follow-up for chronic sinusitis, congestion and facial pressure.",       "Low",    "Chronic sinusitis follow-up",      ["Any improvement since last visit?", "Nasal spray used?", "Any new triggers?"]),
}

# Visit notes for completed appointments
VISIT_NOTES = {
    0:  ("ECG performed — normal sinus rhythm. Advised lifestyle modifications, low-sodium diet, daily 30-min walks. Referred for stress echocardiogram.",
         "Your heart rhythm looks normal. We recommend eating less salt, walking 30 minutes daily, and scheduling a follow-up heart scan for further evaluation."),
    1:  ("Throat clear, lungs clear on auscultation. Viral URTI likely. Advised rest, hydration, and paracetamol for fever.",
         "This looks like a common cold. Get plenty of rest, drink water, and take paracetamol if you have a fever. You should feel better in 5–7 days."),
    2:  ("Mild effusion noted on exam. X-ray ordered. Advised RICE therapy, prescribed ibuprofen 400mg TDS for 5 days, and physiotherapy referral.",
         "There is mild swelling in your knee. Rest it, apply ice, compress with a bandage, and keep it elevated. Take ibuprofen after meals and attend physiotherapy sessions."),
    3:  ("Diagnosed as migraine with aura. Prescribed sumatriptan 50mg PRN. Advised keeping a migraine diary and avoiding known triggers.",
         "You have migraines with visual disturbances. We've prescribed a medication to take at the start of a headache. Try to note your triggers (stress, certain foods, bright lights) in a diary."),
    4:  ("24-hour Holter monitor prescribed. Advised to reduce caffeine. Follow-up in 2 weeks with results.",
         "We want to monitor your heartbeat over 24 hours with a small device to wear. Please cut back on coffee and energy drinks until your follow-up."),
    5:  ("Rapid strep test negative. Viral pharyngitis. Advised warm salt gargles, lozenges, and adequate rest. No antibiotics required.",
         "Your throat swab test is negative. This is a viral infection — antibiotics won't help. Gargle with warm salt water, use throat lozenges, and rest up."),
    6:  ("Allergic contact dermatitis confirmed. Prescribed hydrocortisone 1% cream twice daily for 7 days. Advised to avoid the triggering detergent.",
         "This is an allergic reaction to something your skin touched. Apply the cream we prescribed twice daily and stop using the detergent that likely caused it."),
    7:  ("PHQ-9 score: 14 (moderate depression). Started sertraline 50mg daily. Referred for CBT. Follow-up in 4 weeks.",
         "Based on our assessment, you have moderate depression. We are starting you on a medication and referring you to a therapist. Please follow up in 4 weeks and reach out any time."),
    8:  ("Troponin normal, ECG: ST changes absent. Musculoskeletal chest pain likely. Prescribed naproxen 250mg BD. Advised to return immediately if symptoms worsen.",
         "The tests show no signs of a heart attack. Your chest pain is likely from a muscle. Take the prescribed anti-inflammatory after food. Return immediately if pain gets worse."),
    9:  ("Lumbar spine exam: no neurological deficits. Prescribed diclofenac gel and physiotherapy. Advised core strengthening exercises.",
         "Your back pain is muscular and not affecting your nerves. Use the gel on the painful area and attend physiotherapy. Simple core exercises will help prevent recurrence."),
    10: ("Rotator cuff strain confirmed. No full tear on assessment. Prescribed rest, NSAIDs and physiotherapy twice weekly for 4 weeks.",
         "Your shoulder muscle is strained but not torn. Rest it, take the anti-inflammatory medication, and attend physiotherapy sessions twice a week for a month."),
    11: ("Nerve conduction study ordered. B12 deficiency suspected. Prescribed B12 injections monthly and dietary counselling.",
         "Your symptoms may be due to a vitamin B12 deficiency. We are starting B12 injections and ordering a nerve test. Eat more eggs, meat, and dairy foods."),
    12: ("Anaphylaxis precaution taken. Epinephrine auto-injector prescribed (EpiPen). Referred to allergy specialist. Advised to carry EpiPen at all times.",
         "You had a serious allergic reaction. We have given you an EpiPen — always carry it. Avoid all shellfish until you see the allergy specialist."),
    13: ("BP today: 150/92. Lifestyle counselling given. Started amlodipine 5mg once daily. Follow-up in 4 weeks.",
         "Your blood pressure is a bit high. We have started a daily tablet to help control it. Reduce salt in your diet, exercise regularly, and come back in 4 weeks."),
    14: ("Nasal endoscopy showed mild mucosal thickening. Prescribed fluticasone nasal spray daily. Saline rinses recommended.",
         "Your sinuses are mildly inflamed. Use the nasal spray every morning and rinse your nose with saline solution daily. This will reduce the congestion over time."),
}

# Prescriptions for completed appointments (visit_note_idx -> list of prescriptions)
PRESCRIPTIONS = {
    0:  [("Ramipril", "5mg", "once daily", 90)],
    2:  [("Ibuprofen", "400mg", "three times daily with food", 5)],
    3:  [("Sumatriptan", "50mg", "as needed at onset of migraine", 30)],
    5:  [("Paracetamol", "500mg", "twice daily", 5)],
    6:  [("Hydrocortisone 1% cream", "thin layer", "twice daily", 7)],
    7:  [("Sertraline", "50mg", "once daily in the morning", 90)],
    8:  [("Naproxen", "250mg", "twice daily after meals", 7)],
    9:  [("Diclofenac gel", "apply 4cm", "three times daily", 14)],
    11: [("Cyanocobalamin (B12)", "1000mcg injection", "monthly", 90)],
    12: [("Epinephrine auto-injector (EpiPen)", "0.3mg", "as needed for anaphylaxis", 365),
         ("Cetirizine", "10mg", "once daily", 30)],
    13: [("Amlodipine", "5mg", "once daily", 90)],
    14: [("Fluticasone nasal spray", "2 sprays each nostril", "once daily", 60)],
}


def make_user(email, role):
    u = User(email=email, password_hash=DEMO_PASSWORD, role=role)
    db.session.add(u)
    db.session.flush()
    return u


def seed():
    with app.app_context():
        if DoctorProfile.query.count() > 0:
            print("Demo data already exists — skipping. Delete existing data first to re-seed.")
            return

        print("Seeding doctors...")
        doctor_profiles = []
        for d in DOCTORS:
            u = make_user(d["email"], "doctor")
            dp = DoctorProfile(
                user_id=u.id,
                full_name=d["full_name"],
                specialisation=d["specialisation"],
                working_hours=d["working_hours"],
                slot_duration_minutes=d["slot_duration_minutes"],
            )
            db.session.add(dp)
            db.session.flush()
            doctor_profiles.append(dp)
            print(f"  ✓ {d['full_name']} ({d['specialisation']})")

        print("Seeding patients...")
        patient_profiles = []
        for p in PATIENTS:
            u = make_user(p["email"], "patient")
            pp = PatientProfile(user_id=u.id, full_name=p["full_name"], phone=p["phone"], dob=p["dob"])
            db.session.add(pp)
            db.session.flush()
            patient_profiles.append(pp)
            print(f"  ✓ {p['full_name']}")

        print("Seeding appointments, clinical records & prescriptions...")
        for idx, (pat_i, doc_i, day_offset, slot_start, slot_end, status) in enumerate(APPOINTMENTS_SPEC):
            appt_date = TODAY + timedelta(days=day_offset)
            appt = Appointment(
                patient_id=patient_profiles[pat_i].id,
                doctor_id=doctor_profiles[doc_i].id,
                appt_date=appt_date,
                slot_start=slot_start,
                slot_end=slot_end,
                status=status,
                held_at=NOW - timedelta(days=abs(day_offset) + 1),
                confirmed_at=NOW - timedelta(days=abs(day_offset)) if status in ("confirmed", "completed") else None,
            )
            db.session.add(appt)
            db.session.flush()

            # Symptom summary
            if idx in SYMPTOM_SUMMARIES:
                raw, urgency, chief, questions = SYMPTOM_SUMMARIES[idx]
                ss = SymptomSummary(
                    appointment_id=appt.id,
                    raw_symptoms=raw,
                    urgency=urgency,
                    chief_complaint=chief,
                    suggested_questions=questions,
                    llm_status="ok",
                )
                db.session.add(ss)
                db.session.flush()

            # Visit note + prescriptions for completed appointments
            if status == "completed" and idx in VISIT_NOTES:
                clinical, friendly = VISIT_NOTES[idx]
                vn = VisitNote(
                    appointment_id=appt.id,
                    clinical_notes=clinical,
                    patient_friendly_summary=friendly,
                    llm_status="ok",
                )
                db.session.add(vn)
                db.session.flush()

                if idx in PRESCRIPTIONS:
                    for med_name, dosage, frequency, duration in PRESCRIPTIONS[idx]:
                        pi = PrescriptionItem(
                            visit_note_id=vn.id,
                            medication_name=med_name,
                            dosage=dosage,
                            frequency=frequency,
                            duration_days=duration,
                        )
                        db.session.add(pi)
                        db.session.flush()

                        # Add a sent medication reminder
                        reminder = MedicationReminder(
                            prescription_item_id=pi.id,
                            scheduled_for=NOW - timedelta(days=1),
                            status="sent",
                        )
                        db.session.add(reminder)

            # Notification for confirmed and completed appointments
            if status in ("confirmed", "completed", "cancelled"):
                notif_type = "confirmation" if status in ("confirmed", "completed") else "cancellation"
                patient_email = PATIENTS[pat_i]["email"]
                notif = Notification(
                    appointment_id=appt.id,
                    type=notif_type,
                    channel="email",
                    recipient=patient_email,
                    status="sent",
                    retry_count=0,
                    last_attempt_at=NOW - timedelta(days=abs(day_offset)),
                )
                db.session.add(notif)

        db.session.commit()
        print("\n✅ Demo data seeded successfully!")
        print(f"   Doctors      : {len(DOCTORS)}")
        print(f"   Patients     : {len(PATIENTS)}")
        print(f"   Appointments : {len(APPOINTMENTS_SPEC)}")
        print(f"   Password     : Demo@1234 (all accounts)")
        print("\nSample logins:")
        for d in DOCTORS:
            print(f"  [doctor]  {d['email']}")
        for p in PATIENTS[:3]:
            print(f"  [patient] {p['email']}")


if __name__ == "__main__":
    seed()

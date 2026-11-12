"""Curated precautions the assistant may quote (general guidance, not medical advice).

Written in plain language from widely published public-health guidance on air pollution
(India's CPCB AQI health statements, WHO and national guidance on masks and exposure).
Deliberately general: no medicines or doses; people with a condition are pointed to their
own doctor's plan. The assistant fetches one topic at a time with ``get_precautions``.
"""
from __future__ import annotations

TOPICS: dict[str, str] = {
    "aqi_categories": """India's AQI (CPCB scale) and what each band means:
- Good (0-50): minimal impact.
- Satisfactory (51-100): minor breathing discomfort for sensitive people.
- Moderate (101-200): breathing discomfort for people with lung disease such as asthma, and for people with heart disease, children and older adults.
- Poor (201-300): breathing discomfort for most people on prolonged exposure.
- Very Poor (301-400): respiratory illness on prolonged exposure.
- Severe (401+): affects healthy people and seriously affects people with existing disease.
The CPCB scale reads higher than the US-style AQI many apps show: PM2.5 of 100 µg/m³ is about 230 on CPCB's scale and about 174 on the US scale.""",

    "masks": """Masks and pollution:
- N95 / FFP2 (or better) respirators filter fine particles (PM2.5) well, but only when they fit closely: no gaps at the nose or cheeks. Beards and loose fits cut protection a lot.
- Cloth and surgical masks give little protection against PM2.5.
- Masks do not filter gases such as NO2 or ozone.
- Replace a respirator when it is dirty, damp, damaged or harder to breathe through.
- People with heart or lung disease, pregnant people, and children should ask a doctor before relying on a respirator for long periods, because they make breathing harder.""",

    "exercise_and_outdoor_activity": """Exercise and time outdoors:
- Satisfactory or better: normal activity is fine.
- Moderate: sensitive groups (lung or heart disease, children, older adults) should cut long or intense outdoor exertion.
- Poor: everyone should reduce prolonged or heavy exertion outdoors; sensitive groups should move exercise indoors.
- Very Poor or Severe: avoid outdoor exercise; keep essential trips short.
- Pollution is usually worst early in the morning and late at night in winter, when the air is still; mid-afternoon is often a little better. Busy roads are worse than parks or side streets.
- Indoors: exercise in a room with clean or filtered air, not one full of outdoor air on a bad day.""",

    "children": """Children:
- Children breathe faster than adults and their lungs are still developing, so they are more affected by polluted air.
- On Poor or worse days, keep outdoor play short and gentle; prefer indoor play.
- Watch for coughing, wheezing or fast breathing, and follow the child's asthma plan if they have one.
- Schools may move sports and assemblies indoors on Very Poor or Severe days.""",

    "older_adults": """Older adults:
- Older adults are more sensitive to polluted air, especially with heart or lung disease.
- On Moderate days with a condition, and on Poor or worse days generally, limit time outdoors and avoid exertion.
- Keep regular medicines on hand and follow the plan agreed with a doctor.
- Seek care quickly for new breathlessness, chest pain or confusion.""",

    "pregnancy": """Pregnancy:
- Exposure to fine particles in pregnancy is linked to lower birth weight and preterm birth, so reducing exposure is worthwhile.
- On Poor or worse days, limit time outdoors, avoid busy roads and keep indoor air clean.
- Ask a doctor before relying on a respirator mask for long periods.""",

    "asthma_copd": """Asthma and COPD:
- Polluted air can trigger flare-ups. Follow your personal asthma or COPD action plan from your doctor.
- Keep your reliever medicine with you, especially on Moderate or worse days.
- Reduce outdoor exertion from Moderate upwards; stay indoors with clean air on Very Poor or Severe days.
- Signs of a flare-up: more coughing, wheezing, chest tightness or needing the reliever more often. If it does not settle, contact a doctor.
- Get emergency help for severe breathlessness, difficulty speaking, or bluish lips.""",

    "heart_conditions": """Heart disease:
- Fine particles raise the risk of heart problems on high-pollution days.
- From Moderate upwards, avoid heavy exertion outdoors; on Poor or worse days keep outdoor time short.
- Keep taking prescribed medicines as advised by your doctor.
- Chest pain, pressure, an irregular heartbeat or sudden breathlessness need emergency help (call 112 or 108).""",

    "diabetes_hypertension": """Diabetes and high blood pressure:
- People with diabetes or high blood pressure are more sensitive to polluted air, mostly through effects on the heart and blood vessels.
- Treat Moderate days as a reason to cut heavy outdoor exertion, and Poor or worse days as a reason to stay mostly indoors.
- Keep up regular medicines and checks as advised by your doctor.""",

    "indoor_air": """Keeping indoor air cleaner:
- On bad days keep windows and doors closed, and air the house when outdoor AQI is lower (often the afternoon).
- An air purifier with a HEPA filter, sized for the room, removes fine particles well. Keep doors closed and run it continuously on bad days.
- Avoid adding pollution indoors: no smoking, incense, mosquito coils or burning; use the kitchen exhaust fan or open a window briefly when cooking on gas.
- Plants do not clean indoor air meaningfully.""",

    "commuting_and_travel": """Commuting and travel:
- Traffic exhaust makes roadsides the most polluted places. Choose quieter routes where you can.
- In a car on bad days, keep windows closed and set the air to recirculate.
- Walking or cycling: a well-fitted N95 helps; avoid peak traffic hours.
- Two-wheelers and auto-rickshaws expose riders to exhaust directly; a well-fitted respirator helps.""",

    "warning_signs": """When to get medical help:
- Call 112 (or 108 for an ambulance) at once for severe breathlessness, chest pain or pressure, difficulty speaking, bluish lips or face, fainting, or confusion.
- Contact a doctor soon for a cough or wheeze that keeps getting worse, needing a reliever inhaler more often than usual, or symptoms that do not settle after moving to cleaner air.
- Airware lists nearby hospitals with phone numbers; it cannot book appointments.""",
}


def get(topic: str) -> str | None:
    return TOPICS.get(topic)

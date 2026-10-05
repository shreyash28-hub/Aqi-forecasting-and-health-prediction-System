import type { Profile, RiskLevel } from "./api";

export const CITIES = ["Delhi", "Bengaluru", "Chennai", "Hyderabad", "Lucknow", "Ahmedabad"] as const;

export const DISCLAIMER = "Estimated risk for decision support only. This is not a medical diagnosis.";

/** Example profiles shown before a user signs in (verified with the deployed model). */
export const EXAMPLE_PROFILES: Record<"ramesh" | "aarav", { name: string; summary: string; tags: string[]; profile: Profile }> = {
  ramesh: {
    name: "Ramesh, 67",
    summary: "Retired",
    tags: ["67 yrs", "COPD", "Retired", "Industrial area", "No mask", "3 h outdoors/day"],
    profile: {
      age: 67, gender: "M", condition: "COPD", smoker: false, occupation: "Retired", area_type: "Industrial",
      mask_usage: "No", outdoor_hours: 3, bmi: 27.5, exercise_hours: 1, family_history: true,
    },
  },
  aarav: {
    name: "Aarav, 25",
    summary: "Office worker",
    tags: ["No condition", "Residential area", "Wears a mask", "1 h outdoors/day"],
    profile: {
      age: 25, gender: "M", condition: "No Condition", smoker: false, occupation: "Indoor Worker",
      area_type: "Residential", mask_usage: "Yes", outdoor_hours: 1, bmi: 23, exercise_hours: 4, family_history: false,
    },
  },
};

export interface Precaution { title: string; detail: string; icon: "activity" | "mask" | "window" | "pulse" | "home" | "phone" }

/** Curated precautions by risk level (the assistant builds on these later). */
export const PRECAUTIONS: Record<RiskLevel, Precaution[]> = {
  Low: [
    { title: "Enjoy outdoor activity", detail: "Air quality is unlikely to affect you today.", icon: "activity" },
    { title: "Keep an eye on the forecast", detail: "Check again if you plan a long day outside.", icon: "pulse" },
  ],
  Moderate: [
    { title: "Limit strenuous outdoor activity", detail: "Keep long walks or exercise short.", icon: "activity" },
    { title: "Wear a well-fitted N95 mask", detail: "When outdoors for more than an hour.", icon: "mask" },
    { title: "Keep windows closed at peak traffic", detail: "Early morning and evening.", icon: "window" },
    { title: "Watch for symptoms", detail: "Contact your doctor if breathing worsens.", icon: "pulse" },
  ],
  High: [
    { title: "Avoid strenuous outdoor activity", detail: "Move exercise indoors.", icon: "activity" },
    { title: "Wear an N95 mask outdoors", detail: "Even for short trips.", icon: "mask" },
    { title: "Keep medication within reach", detail: "Especially inhalers for asthma or COPD.", icon: "pulse" },
    { title: "Know your nearest hospital", detail: "Save its phone number in advance.", icon: "phone" },
  ],
  Severe: [
    { title: "Stay indoors as much as possible", detail: "Keep doors and windows closed.", icon: "home" },
    { title: "Wear an N95 mask if you go out", detail: "Keep trips short.", icon: "mask" },
    { title: "Follow your treatment plan", detail: "Keep rescue medication at hand.", icon: "pulse" },
    { title: "Seek medical help early", detail: "Contact a hospital if symptoms appear.", icon: "phone" },
  ],
};

export const labels = {
  en: {
    title: "A clearer next step",
    sub: "Tell us what care is needed. We will help you navigate the options.",
    input: "Describe the care need",
    start: "Find care options",
    next: "Continue",
    yes: "Yes",
    no: "No",
    unsure: "Not sure",
    reset: "Start a new case",
    match: "Suitable care options",
    warning: "Get emergency help now",
    demo: "Synthetic demo · no real dispatch",
    confirm: "Reserve demo slot",
    update: "Add or correct information",
    review: "A human assessment is needed",
  },
  hi: {
    title: "देखभाल का सही अगला कदम",
    sub: "बताएं किस तरह की मदद चाहिए। हम देखभाल के विकल्प समझने में मदद करेंगे।",
    input: "देखभाल की जरूरत बताएं",
    start: "देखभाल के विकल्प देखें",
    next: "आगे बढ़ें",
    yes: "हाँ",
    no: "नहीं",
    unsure: "पता नहीं",
    reset: "नया केस शुरू करें",
    match: "उपयुक्त देखभाल विकल्प",
    warning: "अभी आपातकालीन मदद लें",
    demo: "सिंथेटिक डेमो · वास्तविक सेवा नहीं",
    confirm: "डेमो स्लॉट बुक करें",
    update: "जानकारी जोड़ें या सुधारें",
    review: "मानव द्वारा मूल्यांकन जरूरी है",
  },
  hinglish: {
    title: "Care ka sahi agla kadam",
    sub: "Batayein kis tarah ki care chahiye. Hum options samajhne mein help karenge.",
    input: "Care ki zaroorat batayein",
    start: "Care options dekhein",
    next: "Aage badhein",
    yes: "Haan",
    no: "Nahi",
    unsure: "Pata nahi",
    reset: "Naya case shuru karein",
    match: "Suitable care options",
    warning: "Abhi emergency help lein",
    demo: "Synthetic demo · real dispatch nahi",
    confirm: "Demo slot reserve karein",
    update: "Information add ya correct karein",
    review: "Human assessment chahiye",
  },
};
export const names = {
  nurse_home_visit: "Nurse home visit",
  paramedic_home_visit: "Paramedic home visit",
  gp_teleconsult: "GP teleconsult",
  specialist_consult: "Specialist consultation",
};
export const time = (value) =>
  new Date(value).toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    weekday: "short",
    hour: "numeric",
    minute: "2-digit",
    day: "numeric",
    month: "short",
  });

export function careName(care, language) {
  const hindi = {
    nurse_home_visit: "घर पर नर्स की सेवा",
    paramedic_home_visit: "घर पर पैरामेडिक की सेवा",
    gp_teleconsult: "डॉक्टर से दूरस्थ परामर्श",
    specialist_consult: "विशेषज्ञ से परामर्श",
  };
  return language === "hi" ? hindi[care] : names[care];
}

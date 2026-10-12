const translations = {
  es: {
    eyebrow:"ESPACIO DE SEGURIDAD LOCAL · MVP 0.1.0",
    headline:"Inteligencia clara. Seguridad con evidencia.",
    lede:"Una base de trabajo para inventario autorizado e inteligencia de vulnerabilidades. Sin detecciones ficticias.",
    notice:"Prototipo: no realiza escaneos ni detecta malware.",
    assetsTitle:"Inventario de activos",
    assetsText:"Prepara un registro de sistemas y recursos que tienes autorización para revisar.",
    threatTitle:"Inteligencia de amenazas",
    threatText:"La integración de fuentes CVE y KEV está planificada; todavía no se muestran datos en vivo.",
    reportsTitle:"Informes verificables",
    reportsText:"Los futuros informes incluirán fuentes, fechas, evidencia y límites del análisis.",
    planned:"Base inicial",plannedNext:"Siguiente fase",principleLabel:"PRINCIPIO OPERATIVO",
    principleTitle:"La evidencia antes que la alarma.",
    principleText:"Una vulnerabilidad publicada no demuestra por sí sola que un sistema esté comprometido. Vanguard distinguirá los datos de inteligencia de los hallazgos realmente verificados.",
    footer:"Prototipo local · Sin telemetría ni análisis activo"
  },
  "pt-BR": {
    eyebrow:"AMBIENTE LOCAL DE SEGURANÇA · MVP 0.1.0",
    headline:"Inteligência clara. Segurança baseada em evidências.",
    lede:"Uma base para inventário autorizado e inteligência de vulnerabilidades. Sem detecções fictícias.",
    notice:"Protótipo: não realiza varreduras nem detecta malware.",
    assetsTitle:"Inventário de ativos",
    assetsText:"Prepare um registro dos sistemas e recursos que você tem autorização para avaliar.",
    threatTitle:"Inteligência de ameaças",
    threatText:"A integração com fontes CVE e KEV está planejada; ainda não há dados ao vivo.",
    reportsTitle:"Relatórios verificáveis",
    reportsText:"Os futuros relatórios incluirão fontes, datas, evidências e limitações da análise.",
    planned:"Base inicial",plannedNext:"Próxima etapa",principleLabel:"PRINCÍPIO OPERACIONAL",
    principleTitle:"Evidência antes do alarme.",
    principleText:"Uma vulnerabilidade publicada não prova, por si só, que um sistema foi comprometido. O Vanguard distinguirá inteligência de ameaças de descobertas realmente verificadas.",
    footer:"Protótipo local · Sem telemetria ou análise ativa"
  },
  en: {
    eyebrow:"LOCAL SECURITY WORKSPACE · MVP 0.1.0",
    headline:"Clear intelligence. Evidence-led security.",
    lede:"A starting point for authorized asset inventory and vulnerability intelligence. No fabricated detections.",
    notice:"Prototype: no scanning or malware detection is performed.",
    assetsTitle:"Asset inventory",
    assetsText:"Prepare a record of systems and resources you are authorized to assess.",
    threatTitle:"Threat intelligence",
    threatText:"CVE and KEV source integration is planned; no live data is shown yet.",
    reportsTitle:"Verifiable reports",
    reportsText:"Future reports will include sources, dates, evidence and analysis limitations.",
    planned:"Initial foundation",plannedNext:"Next phase",principleLabel:"OPERATING PRINCIPLE",
    principleTitle:"Evidence before alarm.",
    principleText:"A published vulnerability does not by itself prove that a system is compromised. Vanguard will distinguish threat intelligence from findings that have actually been verified.",
    footer:"Local prototype · No telemetry or active analysis"
  }
};
const languageSelect = document.querySelector("#language");
function applyLanguage(language) {
  const selected = translations[language] ? language : "es";
  document.documentElement.lang = selected;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    if (translations[selected][key]) element.textContent = translations[selected][key];
  });
  languageSelect.value = selected;
}
languageSelect.addEventListener("change", (event) => applyLanguage(event.target.value));
applyLanguage("es");
if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost")) {
  window.addEventListener("load", () => navigator.serviceWorker.register("./service-worker.js").catch(() => {}));
}

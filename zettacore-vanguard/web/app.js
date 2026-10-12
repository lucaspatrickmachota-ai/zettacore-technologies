const translations = {
  es: {
    eyebrow:"ESPACIO DE SEGURIDAD LOCAL · MVP 0.1.0",
    headline:"Inteligencia clara. Seguridad con evidencia.",
    lede:"Una base de trabajo para inventario autorizado e inteligencia de vulnerabilidades. Sin detecciones ficticias.",
    notice:"Prototipo: no realiza escaneos ni detecta malware.",
    assetsTitle:"Inventario de activos",
    assetsText:"Registra los sistemas y recursos que tienes autorización para revisar.",
    assetsEyebrow:"INVENTARIO LOCAL", localOnly:"Solo en este navegador",
    assetName:"Nombre del activo", assetNamePlaceholder:"Ej.: Servidor web de pruebas",
    assetType:"Tipo", assetOwner:"Propietario / equipo", assetOwnerPlaceholder:"Ej.: Equipo de TI",
    typeServer:"Servidor", typeWorkstation:"Equipo", typeWebsite:"Web / dominio", typeCloud:"Recurso cloud", typeOther:"Otro",
    addAsset:"Añadir activo", inventoryPrivacy:"Los registros se guardan localmente mediante el almacenamiento de este navegador. No se envían a un servidor.",
    assetEmpty:"Todavía no hay activos. Añade uno que estés autorizado a revisar.", assetActions:"Acciones", deleteAsset:"Eliminar",
    deleteConfirm:"¿Eliminar este activo del inventario local?", storageError:"No se pudo acceder al almacenamiento local de este navegador.",
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
    assetsText:"Registre os sistemas e recursos que você tem autorização para avaliar.",
    assetsEyebrow:"INVENTÁRIO LOCAL", localOnly:"Somente neste navegador",
    assetName:"Nome do ativo", assetNamePlaceholder:"Ex.: Servidor web de testes",
    assetType:"Tipo", assetOwner:"Responsável / equipe", assetOwnerPlaceholder:"Ex.: Equipe de TI",
    typeServer:"Servidor", typeWorkstation:"Computador", typeWebsite:"Site / domínio", typeCloud:"Recurso de nuvem", typeOther:"Outro",
    addAsset:"Adicionar ativo", inventoryPrivacy:"Os registros são salvos localmente no armazenamento deste navegador. Não são enviados a um servidor.",
    assetEmpty:"Ainda não há ativos. Adicione um que você tenha autorização para avaliar.", assetActions:"Ações", deleteAsset:"Excluir",
    deleteConfirm:"Excluir este ativo do inventário local?", storageError:"Não foi possível acessar o armazenamento local deste navegador.",
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
    assetsText:"Record systems and resources you are authorized to assess.",
    assetsEyebrow:"LOCAL INVENTORY", localOnly:"Stored in this browser only",
    assetName:"Asset name", assetNamePlaceholder:"e.g. Test web server",
    assetType:"Type", assetOwner:"Owner / team", assetOwnerPlaceholder:"e.g. IT team",
    typeServer:"Server", typeWorkstation:"Workstation", typeWebsite:"Website / domain", typeCloud:"Cloud resource", typeOther:"Other",
    addAsset:"Add asset", inventoryPrivacy:"Records are saved locally in this browser's storage. They are not sent to a server.",
    assetEmpty:"No assets yet. Add one you are authorized to assess.", assetActions:"Actions", deleteAsset:"Delete",
    deleteConfirm:"Delete this asset from the local inventory?", storageError:"This browser's local storage could not be accessed.",
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
const assetForm = document.querySelector("#asset-form");
const assetRows = document.querySelector("#asset-rows");
const assetTable = document.querySelector("#asset-table");
const assetEmpty = document.querySelector("#asset-empty");
const storageWarning = document.querySelector("#storage-warning");
const STORAGE_KEY = "zettacore-vanguard-assets-v1";
let assets = [];
let storageAvailable = true;

function applyLanguage(language) {
  const selected = translations[language] ? language : "es";
  document.documentElement.lang = selected;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    if (translations[selected][key]) element.textContent = translations[selected][key];
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    const key = element.dataset.i18nPlaceholder;
    if (translations[selected][key]) element.placeholder = translations[selected][key];
  });
  languageSelect.value = selected;
  renderAssets();
}
languageSelect.addEventListener("change", (event) => applyLanguage(event.target.value));

function currentLanguage() {
  return translations[languageSelect.value] ? languageSelect.value : "es";
}
function saveAssets() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(assets));
    storageAvailable = true;
    return true;
  } catch {
    storageAvailable = false;
    return false;
  }
}
function loadAssets() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    assets = Array.isArray(stored) ? stored.filter((item) =>
      item && typeof item.id === "string" && typeof item.name === "string" &&
      typeof item.type === "string" && typeof item.owner === "string"
    ) : [];
  } catch {
    assets = [];
    storageAvailable = false;
  }
}
function renderAssets() {
  if (!assetRows || !assetTable || !assetEmpty) return;
  assetRows.replaceChildren();
  const t = translations[currentLanguage()];
  for (const asset of assets) {
    const row = document.createElement("tr");
    const name = document.createElement("td");
    name.textContent = asset.name;
    const type = document.createElement("td");
    const typeKey = ({server:"typeServer",workstation:"typeWorkstation",website:"typeWebsite",cloud:"typeCloud",other:"typeOther"})[asset.type] || "typeOther";
    type.textContent = t[typeKey];
    const owner = document.createElement("td");
    owner.textContent = asset.owner || "—";
    const actions = document.createElement("td");
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "button-secondary delete-button";
    remove.dataset.deleteAsset = asset.id;
    remove.textContent = t.deleteAsset;
    remove.setAttribute("aria-label", t.deleteAsset + ": " + asset.name);
    actions.append(remove);
    row.append(name, type, owner, actions);
    assetRows.append(row);
  }
  assetTable.hidden = assets.length === 0;
  assetEmpty.hidden = assets.length !== 0;
  if (assets.length === 0 && storageAvailable) assetEmpty.textContent = t.assetEmpty;
  if (storageWarning) {
    storageWarning.hidden = storageAvailable;
    storageWarning.textContent = storageAvailable ? "" : t.storageError;
  }
}
if (assetForm) {
  assetForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const nameInput = document.querySelector("#asset-name");
    const typeInput = document.querySelector("#asset-type");
    const ownerInput = document.querySelector("#asset-owner");
    const name = nameInput.value.trim();
    if (!name) { nameInput.focus(); return; }
    assets.unshift({id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2), name, type:typeInput.value, owner:ownerInput.value.trim()});
    if (!saveAssets()) {
      assets.shift();
      renderAssets();
      return;
    }
    assetForm.reset();
    nameInput.focus();
    renderAssets();
  });
  assetRows.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-delete-asset]");
    if (!button) return;
    if (!window.confirm(translations[currentLanguage()].deleteConfirm)) return;
    const previousAssets = assets;
    assets = assets.filter((asset) => asset.id !== button.dataset.deleteAsset);
    if (!saveAssets()) assets = previousAssets;
    renderAssets();
  });
}
loadAssets();
applyLanguage("es");
if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost")) {
  window.addEventListener("load", () => navigator.serviceWorker.register("./service-worker.js").catch(() => {}));
}

# CoreAlpha — Insight & Signals UI (v1 Prototype)

**Beskrivning:**  
Denna lilla, helt statiska UI-prototyp visar hur CoreAlpha kan presentera FinGPT‑drivna insikter (sammanfattningar, sentiment, scenario‑sannolikheter), multi‑agent‑röster och ExplainVar. 
Allt kör lokalt i webbläsaren med mockdata. API-anrop är stubbade i UI:t och kan kopplas till ditt backend (Adapter-lager) när som helst.

## Funktioner
- **Insight Feed:** nyheter/rapporter → sammanfattning, sentiment, scenario (upp 48h).  
- **Detaljer:** källor, sentiment‑bar, scenario‑gauge, sammanlagd röst.  
- **Agent Votes:** lista över specialiserade agenter (Sentiment, Fundamental, Technical, Macro, PM/Risk) med vikt och rationale.  
- **ExplainVar Modal:** variabler/features som drev beslutet.  
- **Watchlist:** smidig överblick med micro‑sparklines.
- **Simulerade AI‑portföljer:** exempel med avkastning/volatilitet/DD och sparkline.  
- **Alerts (stub):** definiera regler — kopplas i produktion till /alerts.  
- **Tema (dark/light):** växla och spara i localStorage.

## Kör lokalt
1. Ladda ned zip och extrahera.
2. Öppna `index.html` i valfri modern webbläsare.

> Ingen byggkedja krävs (ingen npm). All CSS/JS är inbäddad i filen eller körs lokalt.

## Koppla till backend (Adapter-lager)
I denna prototyp finns endast mockdata. När du har dina endpoints redo (t.ex. från FinGPT‑adapter och AI‑Hedge‑Fund‑agenterna), kan du ersätta mock med riktiga anrop:

**Föreslagna endpoints:**
- `POST /summarize { ticker?, url?, text? } -> { summary, impact, sources[], latency_ms }`
- `POST /sentiment { ticker, texts[] } -> { score[-1..1], rationale, sources[] }`
- `POST /agent/propose { ticker, date } -> { proposal, used_features[], confidence, rationale }`
- `POST /vote { proposals[] } -> { decision, explain: { weights, features, meta }, calibrated_probs }`

Exempel (ersätt mock i `app.js`):  
```js
fetch(BASE_URL + '/summarize', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ ticker:'NVDA', url }) })
 .then(r=>r.json())
 .then(data => /* uppdatera UI */)
```

## Struktur
- **index.html** – UI + stil + logik (mock).  
- *(Endast en fil för att göra det superlätt att prova. I produktion bryter du ut CSS/JS i separata filer, lägger till riktiga API anrop och state‑hantering.)*

## Juridik
- Detta är en demo och **inte investeringsråd**.
- Säkerställ att datakällor följer respektive **TOS/licens** innan produktion.
- FinGPT/AI‑Hedge‑Fund är MIT‑licensierade — behåll licenstexter och följ respektive modell/data‑licens.

## Designrational
- **Snabb överblick**: feed + detaljpanel i två kolumner.
- **Explainability‑first**: källor, variabler, vikter synliga med ett klick.
- **Ljudlöst skal**: inga externa ramverk, funkar offline, lätt att koppla till riktiga endpoints.

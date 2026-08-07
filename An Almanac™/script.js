async function loadAlmanac() {
  const weather = await fetchWeather();
  const fuel = await fetchFuel();
  const lunar = getLunarPhase();

  document.getElementById("weather-text").innerText =
    `${weather.summary}. Demand signal: ${weather.impact}`;

  document.getElementById("fuel-text").innerText =
    `Fuel averaged $${fuel.price}/gal, ${fuel.trend} margins.`;

  document.getElementById("lunar-text").innerText =
    `${lunar.phase} moon correlated with ${lunar.effect}.`;

  updateTicker(weather, fuel, lunar);
}

/* --- DATA SOURCES (simple versions) --- */

async function fetchWeather() {
  return {
    summary: "Rain across the region",
    impact: "delivery demand increased"
  };
}

async function fetchFuel() {
  return {
    price: "3.80",
    trend: "reducing"
  };
}

function getLunarPhase() {
  return {
    phase: "Waning",
    effect: "lower late-night activity"
  };
}

/* --- TICKER --- */

function updateTicker(weather, fuel, lunar) {
  document.getElementById("ticker").innerText =
    `OIL ↑ ${fuel.price} | RAIN ↑ | DELIVERY ↑ | MOON ↓`;
}

loadAlmanac();

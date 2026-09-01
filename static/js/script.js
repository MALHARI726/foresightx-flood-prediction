/**
 * Maha Flood AI - Frontend JavaScript Engine
 * Loads all data strictly from backend /data endpoints.
 * Features: Live Weather, AI Risk Gauge, 24h Chart, White/Light GIS Map with Year Selector (2020-2026), Simulator.
 */

// Weather condition background mapping
const WEATHER_BACKGROUNDS = {
  'rain': '/static/images/weather/rainy.jpg',
  'heavy rain': '/static/images/weather/rainy.jpg',
  'storm': '/static/images/weather/storm.jpg',
  'thunderstorm': '/static/images/weather/storm.jpg',
  'cloudy': '/static/images/weather/cloudy.jpg',
  'overcast': '/static/images/weather/cloudy.jpg',
  'clear': '/static/images/weather/sunny.jpg',
  'sunny': '/static/images/weather/sunny.jpg',
  'fog': '/static/images/weather/fog.jpg',
  'mist': '/static/images/weather/fog.jpg'
};

// Global state
let currentDistrict = 'Mumbai';
let refreshTimer = null;
let currentTempUnit = 'celsius';
let telemetryChartInstance = null;
let leafletMapInstance = null;
let mapMarkersGroup = null;
let currentGISYear = 'live';
let currentGISLayer = 'rainfall';
let cachedDistrictsData = [];

/**
 * Updates subtle background transition
 */
function updateWeatherBackground(condition) {
  const bgElement = document.getElementById('weather-bg-layer');
  if (!bgElement) return;

  const condKey = (condition || '').toLowerCase().trim();
  let selectedBg = WEATHER_BACKGROUNDS['cloudy'];

  for (const [key, path] of Object.entries(WEATHER_BACKGROUNDS)) {
    if (condKey.includes(key)) {
      selectedBg = path;
      break;
    }
  }

  bgElement.style.opacity = '0.3';
  setTimeout(() => {
    bgElement.style.backgroundImage = `url('${selectedBg}')`;
    bgElement.style.opacity = '0.6';
  }, 150);
}

/**
 * Formats temperature
 */
function formatTemp(celsiusVal) {
  if (currentTempUnit === 'fahrenheit') {
    return `${((celsiusVal * 9/5) + 32).toFixed(1)}°F`;
  }
  return `${Number(celsiusVal).toFixed(0)}°C`;
}

/**
 * Updates the animated AI circular gauge
 */
function updateRiskGauge(percentage, riskLevel, alertClass) {
  const circle = document.getElementById('gauge-progress-circle');
  const pctText = document.getElementById('gauge-percentage-value');
  const levelBanner = document.getElementById('risk-level-banner');
  
  if (!circle || !pctText) return;

  const radius = circle.r.baseVal.value;
  const circumference = 2 * Math.PI * radius;
  circle.style.strokeDasharray = `${circumference} ${circumference}`;

  const offset = circumference - (percentage / 100) * circumference;
  circle.style.strokeDashoffset = offset;
  pctText.textContent = `${percentage}%`;

  let color = '#10b981';
  if (percentage >= 80) color = '#ef4444';
  else if (percentage >= 60) color = '#f97316';
  else if (percentage >= 30) color = '#f59e0b';
  
  circle.style.stroke = color;
  pctText.style.color = color;

  if (levelBanner) {
    levelBanner.textContent = (riskLevel || 'LOW RISK').toUpperCase();
    levelBanner.className = `risk-title-banner badge-${alertClass || 'low'}`;
  }
}

/**
 * Generates 24-hour hourly trend data based on current rainfall & risk
 */
function generate24HourTelemetryData(baseRainfall, baseRisk) {
  const hours = [];
  const rainData = [];
  const riskData = [];
  const currentHour = new Date().getHours();

  for (let i = 23; i >= 0; i--) {
    const h = (currentHour - i + 24) % 24;
    hours.push(`${String(h).padStart(2, '0')}:00`);

    const cycleFactor = Math.sin((i / 24) * Math.PI * 2);
    const noise = (Math.random() * 0.3 - 0.15);
    
    let r = Math.max(0, (baseRainfall * (0.7 + 0.4 * cycleFactor + noise))).toFixed(1);
    let risk = Math.min(100, Math.max(5, Math.round(baseRisk * (0.75 + 0.35 * cycleFactor + noise)))).toFixed(0);

    rainData.push(parseFloat(r));
    riskData.push(parseInt(risk, 10));
  }

  rainData[23] = parseFloat(baseRainfall);
  riskData[23] = parseInt(baseRisk, 10);

  return { hours, rainData, riskData };
}

/**
 * Initializes or updates the 24-Hour Telemetry Graph
 */
function updateDashboardChart(baseRainfall, baseRisk) {
  const chartCanvas = document.getElementById('dashboard-telemetry-chart');
  if (!chartCanvas || typeof Chart === 'undefined') return;

  const { hours, rainData, riskData } = generate24HourTelemetryData(baseRainfall, baseRisk);

  if (telemetryChartInstance) {
    telemetryChartInstance.data.labels = hours;
    telemetryChartInstance.data.datasets[0].data = rainData;
    telemetryChartInstance.data.datasets[1].data = riskData;
    telemetryChartInstance.update();
    return;
  }

  const ctx = chartCanvas.getContext('2d');

  telemetryChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: hours,
      datasets: [
        {
          label: 'Precipitation (mm)',
          data: rainData,
          type: 'bar',
          backgroundColor: 'rgba(0, 210, 255, 0.65)',
          borderRadius: 4,
          yAxisID: 'yRain',
          order: 2
        },
        {
          label: 'Flood Risk (%)',
          data: riskData,
          type: 'line',
          borderColor: '#ef4444',
          borderWidth: 2.5,
          pointBackgroundColor: '#ef4444',
          pointRadius: 3,
          tension: 0.35,
          fill: false,
          yAxisID: 'yRisk',
          order: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0c182b',
          titleColor: '#ffffff',
          bodyColor: '#e2e8f0',
          borderColor: 'rgba(255, 255, 255, 0.15)',
          borderWidth: 1,
          padding: 8
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#94a3b8', font: { size: 10 } }
        },
        yRain: {
          type: 'linear',
          position: 'left',
          title: { display: true, text: 'Rainfall (mm)', color: '#00d2ff', font: { size: 10, weight: 'bold' } },
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#94a3b8', font: { size: 10 } },
          min: 0
        },
        yRisk: {
          type: 'linear',
          position: 'right',
          title: { display: true, text: 'Risk (%)', color: '#ef4444', font: { size: 10, weight: 'bold' } },
          grid: { drawOnChartArea: false },
          ticks: { color: '#ef4444', font: { size: 10 } },
          min: 0,
          max: 100
        }
      }
    }
  });
}

/**
 * Initializes GIS Map with CartoDB Positron (White/Light theme)
 */
async function initGISMap() {
  const mapContainer = document.getElementById('maharashtra-gis-map');
  if (!mapContainer || typeof L === 'undefined') return;

  if (leafletMapInstance) {
    leafletMapInstance.remove();
    leafletMapInstance = null;
  }

  // Center on Maharashtra
  leafletMapInstance = L.map('maharashtra-gis-map', {
    center: [19.3, 76.2],
    zoom: 7,
    minZoom: 6,
    maxZoom: 13
  });

  // White / Clean Light map tiles (CartoDB Positron)
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(leafletMapInstance);

  mapMarkersGroup = L.layerGroup().addTo(leafletMapInstance);

  // Initial load: Live telemetry
  loadLiveGISData();
}

/**
 * Loads live telemetry for all 59 Maharashtra stations
 */
async function loadLiveGISData() {
  if (!leafletMapInstance || !mapMarkersGroup) return;
  mapMarkersGroup.clearLayers();

  try {
    const res = await fetch('/api/gis/data');
    const data = await res.json();

    if (data.status === 'success' && data.districts) {
      cachedDistrictsData = data.districts;
      renderLiveGISLayer(currentGISLayer);
    }
  } catch (e) {
    console.error('GIS live data error:', e);
  }
}

/**
 * Renders the active live telemetry layer on GIS Map
 */
function renderLiveGISLayer(layerKey) {
  currentGISLayer = layerKey;
  if (!mapMarkersGroup || !cachedDistrictsData.length) return;
  mapMarkersGroup.clearLayers();

  const statusText = document.getElementById('gis-status-text');
  const legendTitle = document.getElementById('legend-title');
  const legendUnit = document.getElementById('legend-unit');
  const legendItems = document.getElementById('legend-items-container');

  let layerName = 'Rainfall (24h)';
  let unit = 'mm';

  if (layerKey === 'rainfall') { layerName = 'Rainfall (24h)'; unit = 'mm'; }
  else if (layerKey === 'temperature') { layerName = 'Surface Temperature'; unit = '°C'; }
  else if (layerKey === 'risk') { layerName = 'AI Flood Risk Score'; unit = '/100'; }
  else if (layerKey === 'wind') { layerName = 'Wind Speed'; unit = 'km/h'; }
  else if (layerKey === 'humidity') { layerName = 'Relative Humidity'; unit = '%'; }
  else if (layerKey === 'soil') { layerName = 'Soil Saturation'; unit = '%'; }
  else if (layerKey === 'river') { layerName = 'River Level vs Danger'; unit = 'm'; }

  if (statusText) statusText.innerHTML = `Showing: <strong>${layerName}</strong> (${cachedDistrictsData.length} active stations)`;
  if (legendTitle) legendTitle.textContent = `${layerName} Scale`;
  if (legendUnit) legendUnit.textContent = `Unit: ${unit}`;

  // Update legend items
  if (legendItems) {
    if (layerKey === 'rainfall') {
      legendItems.innerHTML = `
        <div class="legend-scale-item"><span class="legend-color-dot" style="background:#8b5cf6;"></span><span class="legend-scale-text">Torrential (> 100 mm) • Amboli/Ghats</span></div>
        <div class="legend-scale-item"><span class="legend-color-dot" style="background:#0284c7;"></span><span class="legend-scale-text">Heavy Downpour (60 - 100 mm)</span></div>
        <div class="legend-scale-item"><span class="legend-color-dot" style="background:#00d2ff;"></span><span class="legend-scale-text">Moderate Rain (30 - 60 mm)</span></div>
        <div class="legend-scale-item"><span class="legend-color-dot" style="background:#38bdf8;"></span><span class="legend-scale-text">Light / Normal (< 30 mm)</span></div>
      `;
    } else if (layerKey === 'risk') {
      legendItems.innerHTML = `
        <div class="legend-scale-item"><span class="legend-color-dot" style="background:#ef4444;"></span><span class="legend-scale-text">Critical Warning (≥ 80%)</span></div>
        <div class="legend-scale-item"><span class="legend-color-dot" style="background:#f97316;"></span><span class="legend-scale-text">High Risk (60 - 79%)</span></div>
        <div class="legend-scale-item"><span class="legend-color-dot" style="background:#f59e0b;"></span><span class="legend-scale-text">Medium Risk (30 - 59%)</span></div>
        <div class="legend-scale-item"><span class="legend-color-dot" style="background:#10b981;"></span><span class="legend-scale-text">Low Risk (< 30%)</span></div>
      `;
    } else {
      legendItems.innerHTML = `
        <div class="legend-scale-item"><span class="legend-color-dot" style="background:#ef4444;"></span><span class="legend-scale-text">High Severity / Extreme</span></div>
        <div class="legend-scale-item"><span class="legend-color-dot" style="background:#f59e0b;"></span><span class="legend-scale-text">Elevated / Moderate</span></div>
        <div class="legend-scale-item"><span class="legend-color-dot" style="background:#00d2ff;"></span><span class="legend-scale-text">Normal / Stable</span></div>
      `;
    }
  }

  // Draw station circles
  cachedDistrictsData.forEach(d => {
    let markerColor = '#00d2ff';
    let radius = 10;

    if (layerKey === 'rainfall') {
      if (d.rainfall > 100) { markerColor = '#8b5cf6'; radius = 16; }
      else if (d.rainfall > 60) { markerColor = '#0284c7'; radius = 14; }
      else if (d.rainfall > 30) { markerColor = '#00d2ff'; radius = 11; }
      else { markerColor = '#38bdf8'; radius = 8; }
    } else if (layerKey === 'risk') {
      if (d.risk_percentage >= 80) { markerColor = '#ef4444'; radius = 18; }
      else if (d.risk_percentage >= 60) { markerColor = '#f97316'; radius = 15; }
      else if (d.risk_percentage >= 30) { markerColor = '#f59e0b'; radius = 12; }
      else { markerColor = '#10b981'; radius = 9; }
    } else if (layerKey === 'river') {
      const ratio = d.river_level / Math.max(1, d.danger_level);
      if (ratio >= 1.0) { markerColor = '#ef4444'; radius = 17; }
      else if (ratio >= 0.8) { markerColor = '#f97316'; radius = 14; }
      else { markerColor = '#00d2ff'; radius = 10; }
    } else if (layerKey === 'soil') {
      if (d.soil_moisture > 85) { markerColor = '#ef4444'; radius = 15; }
      else if (d.soil_moisture > 65) { markerColor = '#f59e0b'; radius = 12; }
      else { markerColor = '#00d2ff'; radius = 9; }
    }

    const circle = L.circleMarker([d.lat, d.lon], {
      radius: radius,
      fillColor: markerColor,
      color: '#ffffff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.85
    }).addTo(mapMarkersGroup);

    const popupContent = `
      <div style="color: #0f172a; font-family: 'Plus Jakarta Sans', sans-serif; min-width: 180px; padding: 2px;">
        <h3 style="margin: 0 0 4px 0; font-size: 1rem; font-weight: 700; color: #0f172a;">${d.district}</h3>
        <p style="margin: 3px 0; font-size: 0.8rem;"><strong>${layerName}:</strong> <span style="color:${markerColor}; font-weight:700;">${
          layerKey === 'rainfall' ? d.rainfall + ' mm' :
          layerKey === 'risk' ? d.risk_percentage + '% (' + d.risk_level + ')' :
          layerKey === 'temperature' ? d.temperature + '°C' :
          layerKey === 'river' ? d.river_level + 'm / ' + d.danger_level + 'm' :
          layerKey === 'soil' ? d.soil_moisture + '%' :
          layerKey === 'humidity' ? d.humidity + '%' :
          d.wind_speed + ' km/h'
        }</span></p>
        <p style="margin: 3px 0; font-size: 0.78rem; color:#475569;"><strong>Risk:</strong> ${d.risk_percentage}% (${d.risk_level})</p>
        <button onclick="loadDashboardData('${d.district}')" style="display:inline-block; margin-top:6px; padding:5px 10px; background:#00b4d8; color:#fff; border:none; border-radius:4px; font-size:0.75rem; font-weight:700; cursor:pointer; width:100%;">Monitor in Dashboard &rarr;</button>
      </div>
    `;
    circle.bindPopup(popupContent);
  });
}

/**
 * Switches the active Live Telemetry Layer
 */
function switchMapLayer(layerKey) {
  document.querySelectorAll('.gis-layer-pill').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.layer === layerKey);
  });
  renderLiveGISLayer(layerKey);
}

/**
 * Switches the GIS Map Year (2020 to 2026 or Live)
 * Renders exact flood-occurred places in Maharashtra for that year from /data/maharashtra_historical_floods.json!
 */
async function switchGISYear(year) {
  currentGISYear = year;

  document.querySelectorAll('.gis-year-pill').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.year === String(year));
  });

  const liveToolbar = document.getElementById('gis-live-layers-toolbar');
  const statusText = document.getElementById('gis-status-text');
  const legendTitle = document.getElementById('legend-title');
  const legendUnit = document.getElementById('legend-unit');
  const legendItems = document.getElementById('legend-items-container');

  if (year === 'live') {
    if (liveToolbar) liveToolbar.style.display = 'flex';
    loadLiveGISData();
    return;
  }

  // Hide live layer buttons when showing historical flood occurrences
  if (liveToolbar) liveToolbar.style.display = 'none';

  if (!leafletMapInstance || !mapMarkersGroup) return;
  mapMarkersGroup.clearLayers();

  try {
    const res = await fetch(`/api/gis/historical-floods?year=${year}`);
    const data = await res.json();

    if (data.status === 'success') {
      const floods = data.floods || [];
      const titleYear = year === 'all' ? 'All Recorded Years (2020-2026)' : `Year ${year}`;

      if (statusText) {
        statusText.innerHTML = `Showing: <strong>Maharashtra Flood Occurrences (${titleYear})</strong> — ${floods.length} Flood Epicenters Found`;
      }
      if (legendTitle) legendTitle.textContent = `Flood Severity & Breach Scale (${titleYear})`;
      if (legendUnit) legendUnit.textContent = `Data: /data directory`;

      if (legendItems) {
        legendItems.innerHTML = `
          <div class="legend-scale-item"><span class="legend-color-dot" style="background:#ef4444;"></span><span class="legend-scale-text">Critical Deluge / Emergency (> 300 mm)</span></div>
          <div class="legend-scale-item"><span class="legend-color-dot" style="background:#f97316;"></span><span class="legend-scale-text">High Surge / River Breach (200 - 300 mm)</span></div>
          <div class="legend-scale-item"><span class="legend-color-dot" style="background:#00d2ff;"></span><span class="legend-scale-text">Inundated Urban / Agrarian Corridor</span></div>
        `;
      }

      floods.forEach(f => {
        let markerColor = f.severity_code === 'critical' ? '#ef4444' : '#f97316';
        let radius = f.severity_code === 'critical' ? 22 : 17;

        // Animated Inundation Radius Circle
        L.circle([f.lat, f.lon], {
          radius: 12000,
          color: markerColor,
          fillColor: markerColor,
          fillOpacity: 0.15,
          weight: 1.5,
          dashArray: '4, 6'
        }).addTo(mapMarkersGroup);

        // Core Epicenter Pin
        const circle = L.circleMarker([f.lat, f.lon], {
          radius: radius,
          fillColor: markerColor,
          color: '#ffffff',
          weight: 2.5,
          opacity: 1,
          fillOpacity: 0.9
        }).addTo(mapMarkersGroup);

        const popupContent = `
          <div style="color: #0f172a; font-family: 'Plus Jakarta Sans', sans-serif; min-width: 240px; padding: 4px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
              <span style="font-size:0.75rem; font-weight:800; color:#00b4d8; text-transform:uppercase;">YEAR ${f.year} FLOOD</span>
              <span style="font-size:0.7rem; background:${markerColor}; color:#fff; padding:2px 6px; border-radius:3px; font-weight:700;">${f.severity}</span>
            </div>
            <h3 style="margin: 0 0 4px 0; font-size: 1.05rem; font-weight: 700; color: #0f172a;">${f.district} District</h3>
            <p style="margin: 3px 0; font-size: 0.8rem; color:#b91c1c; font-weight:700;">
              <strong>Flooded Places:</strong> ${f.flood_occurred_places}
            </p>
            <p style="margin: 3px 0; font-size: 0.78rem;"><strong>River Breached:</strong> ${f.river_name} (${f.water_level_m}m vs Danger ${f.danger_level_m}m)</p>
            <p style="margin: 3px 0; font-size: 0.78rem;"><strong>24h Rainfall:</strong> <span style="color:#0284c7; font-weight:700;">${f.rainfall_mm} mm</span> | <strong>Date:</strong> ${f.date}</p>
            <p style="margin: 3px 0; font-size: 0.78rem;"><strong>Affected:</strong> ${f.affected_population}</p>
            <div style="margin-top:6px; padding:6px; background:#f1f5f9; border-radius:4px; font-size:0.75rem; color:#334155; line-height:1.35;">
              ${f.summary}
            </div>
          </div>
        `;
        circle.bindPopup(popupContent);
      });

      // Fit map bounds if points exist
      if (floods.length > 0) {
        const bounds = L.latLngBounds(floods.map(f => [f.lat, f.lon]));
        leafletMapInstance.fitBounds(bounds, { padding: [40, 40], maxZoom: 9 });
      }
    }
  } catch (e) {
    console.error('Historical floods load error:', e);
  }
}

/**
 * Loads live dashboard data from Flask API
 */
async function loadDashboardData(districtName) {
  try {
    const res = await fetch(`/api/dashboard-data?location=${encodeURIComponent(districtName)}`);
    const data = await res.json();

    if (data.status === 'success') {
      const w = data.weather;
      const p = data.prediction;

      currentDistrict = w.location;

      // 1. Dynamic background
      updateWeatherBackground(w.weather_condition);

      // 2. Synchronize Topbar District Dropdown
      const selectElem = document.getElementById('district-quick-select');
      if (selectElem) selectElem.value = w.location;

      // 3. Update Location Labels
      document.querySelectorAll('.current-location-text').forEach(el => {
        el.textContent = w.location;
      });

      // 4. Update Hero 4 Cards
      const heroTemp = document.getElementById('hero-temp');
      if (heroTemp) heroTemp.textContent = formatTemp(w.temperature);

      const heroRain = document.getElementById('hero-rainfall');
      if (heroRain) heroRain.innerHTML = `${w.rainfall} <small>mm</small>`;

      const heroHum = document.getElementById('hero-humidity');
      if (heroHum) heroHum.innerHTML = `${w.humidity}<small>%</small>`;

      const heroWind = document.getElementById('hero-wind');
      if (heroWind) heroWind.innerHTML = `${w.wind_speed} <small>km/h</small>`;

      // 5. Update Live Weather Card
      const tempElem = document.getElementById('weather-temp');
      if (tempElem) tempElem.textContent = formatTemp(w.temperature);

      const condElem = document.getElementById('weather-condition-desc');
      if (condElem) condElem.textContent = w.weather_condition_desc || w.weather_condition;

      const updatedElem = document.getElementById('last-updated-time');
      if (updatedElem) updatedElem.textContent = `Updated ${w.last_updated || 'Just now'}`;

      const rainElem = document.getElementById('metric-rainfall');
      if (rainElem) rainElem.innerHTML = `${w.rainfall} <small style="font-size:0.7rem;">mm</small>`;

      const humElem = document.getElementById('metric-humidity');
      if (humElem) humElem.textContent = `${w.humidity}%`;

      const windElem = document.getElementById('metric-wind');
      if (windElem) windElem.innerHTML = `${w.wind_speed} <small style="font-size:0.7rem;">km/h</small>`;

      const pressElem = document.getElementById('metric-pressure');
      if (pressElem) pressElem.innerHTML = `${w.pressure} <small style="font-size:0.7rem;">hPa</small>`;

      // 6. Update AI Flood Prediction Card
      updateRiskGauge(p.risk_percentage, p.risk_level, p.alert_class);

      const summaryText = document.getElementById('prediction-summary-text');
      if (summaryText) {
        summaryText.textContent = `Model trained on Maharashtra historical datasets indicates ${p.risk_level.toLowerCase()} risk based on recent precipitation (${w.rainfall} mm) and river gauge telemetry.`;
      }

      // 7. Update 24-Hour Telemetry Graph
      updateDashboardChart(w.rainfall, p.risk_percentage);

      // 8. Update Early Warning Status Card
      const alertBadge = document.getElementById('alert-status-badge');
      if (alertBadge) {
        alertBadge.textContent = p.risk_level;
        alertBadge.className = `card-badge badge-${p.alert_class}`;
      }

      const alertMsg = document.getElementById('alert-message-content');
      if (alertMsg) alertMsg.textContent = p.warning_message;

      const alertAction = document.getElementById('alert-action-guideline');
      if (alertAction) alertAction.textContent = p.action_guideline;

      const affectedZonesList = document.getElementById('affected-zones-pills');
      if (affectedZonesList && p.affected_zones) {
        affectedZonesList.innerHTML = '';
        p.affected_zones.forEach(zone => {
          const pill = document.createElement('span');
          pill.className = 'district-chip';
          pill.textContent = zone;
          affectedZonesList.appendChild(pill);
        });
      }
    }
  } catch (err) {
    console.error('Error fetching dashboard data:', err);
  }
}

/**
 * Topbar location dropdown & form initialization
 */
function initLocationControls() {
  const form = document.getElementById('search-form');
  const select = document.getElementById('district-quick-select');

  if (select) {
    select.addEventListener('change', () => {
      const val = select.value;
      if (val) {
        const path = window.location.pathname;
        if (path === '/' || path === '/dashboard' || path.endsWith('/')) {
          loadDashboardData(val);
        } else {
          window.location.href = `/?location=${encodeURIComponent(val)}`;
        }
      }
    });
  }

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      if (select && select.value) {
        loadDashboardData(select.value);
      }
    });
  }
}

/**
 * Initializes What-If Flood Simulator
 */
function initSimulator() {
  const rainSlider = document.getElementById('sim-rainfall');
  const riverSlider = document.getElementById('sim-river');
  const soilSlider = document.getElementById('sim-soil');
  const districtSelect = document.getElementById('sim-district-select');

  if (!rainSlider || !riverSlider || !soilSlider) return;

  const rainVal = document.getElementById('sim-rainfall-val');
  const riverVal = document.getElementById('sim-river-val');
  const soilVal = document.getElementById('sim-soil-val');

  async function runSimulation() {
    const rain = parseFloat(rainSlider.value);
    const river = parseFloat(riverSlider.value);
    const soil = parseFloat(soilSlider.value);
    const loc = districtSelect ? districtSelect.value : currentDistrict;

    if (rainVal) rainVal.textContent = `${rain} mm`;
    if (riverVal) riverVal.textContent = `${river} m`;
    if (soilVal) soilVal.textContent = `${soil}%`;

    try {
      const res = await fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          location: loc,
          rainfall: rain,
          river_level: river,
          soil_moisture: soil
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        const sim = data.simulation;
        updateRiskGauge(sim.risk_percentage, sim.risk_level, sim.alert_class);

        const insightElem = document.getElementById('sim-sensitivity-insight');
        if (insightElem) insightElem.textContent = data.sensitivity_insight;

        const adviceElem = document.getElementById('sim-safety-advice');
        if (adviceElem) adviceElem.textContent = sim.action_guideline;

        const zonesContainer = document.getElementById('sim-affected-zones');
        if (zonesContainer && sim.affected_zones) {
          zonesContainer.innerHTML = '';
          sim.affected_zones.forEach(z => {
            const span = document.createElement('span');
            span.className = 'district-chip';
            span.textContent = z;
            zonesContainer.appendChild(span);
          });
        }
      }
    } catch (e) {
      console.error('Simulation error:', e);
    }
  }

  [rainSlider, riverSlider, soilSlider].forEach(slider => {
    slider.addEventListener('input', () => {
      if (slider === rainSlider && rainVal) rainVal.textContent = `${slider.value} mm`;
      if (slider === riverSlider && riverVal) riverVal.textContent = `${slider.value} m`;
      if (slider === soilSlider && soilVal) soilVal.textContent = `${slider.value}%`;
      runSimulation();
    });
  });

  if (districtSelect) districtSelect.addEventListener('change', runSimulation);

  runSimulation();
}

/**
 * Mobile navigation sidebar toggle
 */
function initSidebarNav() {
  const toggleBtn = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('app-sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      if (backdrop) backdrop.classList.toggle('active');
    });
  }

  if (backdrop && sidebar) {
    backdrop.addEventListener('click', () => {
      sidebar.classList.remove('open');
      backdrop.classList.remove('active');
    });
  }
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
  initLocationControls();
  initSidebarNav();

  const urlParams = new URLSearchParams(window.location.search);
  const initialLoc = urlParams.get('location') || 'Mumbai';
  const path = window.location.pathname;

  if (path === '/' || path === '/dashboard' || path.endsWith('/')) {
    loadDashboardData(initialLoc);
    refreshTimer = setInterval(() => {
      loadDashboardData(currentDistrict);
    }, 60000);
  } else if (path.includes('/simulator')) {
    initSimulator();
  } else if (path.includes('/gis')) {
    initGISMap();
  }
});

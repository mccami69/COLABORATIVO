// Use existing `socket` if declared elsewhere (e.g. in app.js).
const sock = (typeof socket !== 'undefined') ? socket : (typeof io !== 'undefined' ? io() : null);
const trackingRoot = document.querySelector('.tracking-layout');
const statusText = document.getElementById('order-status-text');
const orderId = trackingRoot ? trackingRoot.dataset.orderId : '';
const googleMapsKey = trackingRoot ? trackingRoot.dataset.googleMapsKey : '';
const startLat = trackingRoot ? parseFloat(trackingRoot.dataset.startLat || '11.2410') : 11.2410;
const startLng = trackingRoot ? parseFloat(trackingRoot.dataset.startLng || '-74.2000') : -74.2;
const endLat = trackingRoot ? parseFloat(trackingRoot.dataset.endLat || '11.2450') : 11.2450;
const endLng = trackingRoot ? parseFloat(trackingRoot.dataset.endLng || '-74.1950') : -74.195;

let map = null;
let marker = null;
let routePath = null;
let animationHandle = null;
let animationIndex = 0;
let animatedPoints = [];
// Leaflet fallback variables
let leafletMap = null;
let leafletMarker = null;
let leafletRoute = null;
let leafletAnimatedPoints = [];
let leafletAnimationHandle = null;

function loadGoogleMaps(key) {
  if (!key) return Promise.reject(new Error('No Google Maps API key'));
  return new Promise((resolve, reject) => {
    if (window.google && window.google.maps) return resolve();
    window.initMap = () => resolve();
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${key}&callback=initMap`;
    script.async = true;
    script.defer = true;
    script.onerror = () => reject(new Error('Failed to load Google Maps'));
    document.head.appendChild(script);
  });
}

function loadLeaflet() {
  return new Promise((resolve, reject) => {
    if (window.L) return resolve();
    // load css
    const css = document.createElement('link');
    css.rel = 'stylesheet';
    css.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(css);
    // load script
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Leaflet'));
    document.head.appendChild(script);
  });
}

function initLeafletInternal() {
  const container = document.getElementById('delivery-map');
  const center = [(startLat + endLat) / 2, (startLng + endLng) / 2];
  leafletMap = L.map(container).setView(center, 14);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(leafletMap);

  const start = [startLat, startLng];
  const end = [endLat, endLng];
  leafletRoute = L.polyline([start, end], { color: '#3333ff', weight: 4 }).addTo(leafletMap);
  leafletMarker = L.marker(start).addTo(leafletMap).bindPopup('Repartidor');
  leafletAnimatedPoints = buildRoutePoints({ lat: startLat, lng: startLng }, { lat: endLat, lng: endLng }, 240);
}

function startLeafletAnimation() {
  if (!leafletMap || !leafletMarker || leafletAnimatedPoints.length === 0) return;
  stopLeafletAnimation();
  let idx = 0;
  leafletAnimationHandle = setInterval(() => {
    idx++;
    if (idx >= leafletAnimatedPoints.length) { clearInterval(leafletAnimationHandle); leafletAnimationHandle = null; return; }
    const p = leafletAnimatedPoints[idx];
    leafletMarker.setLatLng([p.lat, p.lng]);
  }, 100);
}

function stopLeafletAnimation() {
  if (leafletAnimationHandle) { clearInterval(leafletAnimationHandle); leafletAnimationHandle = null; }
}

function linearInterpolate(a, b, t) {
  return a + (b - a) * t;
}

function buildRoutePoints(from, to, steps = 200) {
  const pts = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    pts.push({ lat: linearInterpolate(from.lat, to.lat, t), lng: linearInterpolate(from.lng, to.lng, t) });
  }
  return pts;
}

function initMapInternal() {
  const center = { lat: (startLat + endLat) / 2, lng: (startLng + endLng) / 2 };
  map = new google.maps.Map(document.getElementById('delivery-map'), {
    center,
    zoom: 14,
    disableDefaultUI: true,
  });

  const start = { lat: startLat, lng: startLng };
  const end = { lat: endLat, lng: endLng };

  // Draw route line
  routePath = new google.maps.Polyline({
    path: [start, end],
    strokeColor: '#3333ff',
    strokeOpacity: 0.8,
    strokeWeight: 4,
    map,
  });

  // Marker
  marker = new google.maps.Marker({
    position: start,
    map,
    title: 'Repartidor',
  });

  // Prepare interpolated route points
  animatedPoints = buildRoutePoints(start, end, 240);
}

function showDomStatic() {
  const container = document.getElementById('delivery-map');
  if (!container) return;
  container.style.position = 'relative';
  let moto = document.getElementById('motorcycle-fallback');
  if (!moto) {
    moto = document.createElement('div');
    moto.id = 'motorcycle-fallback';
    moto.style.position = 'absolute';
    moto.style.top = '50%';
    moto.style.transform = 'translate(-12px, -50%)';
    moto.style.fontSize = '24px';
    moto.style.zIndex = 30;
    moto.textContent = '🏍️';
    container.appendChild(moto);
  }
  // position at start
  const padding = 24;
  moto.style.left = `${padding}px`;
}

function initDisplay() {
  // Prefer Google Maps if key provided; otherwise try Leaflet; finally DOM fallback
  if (googleMapsKey) {
    loadGoogleMaps(googleMapsKey)
      .then(() => {
        console.log('Google Maps cargado (init display).');
        if (!map) initMapInternal();
      })
      .catch((err) => {
        console.warn('Google Maps falló, intentando Leaflet:', err && err.message);
        loadLeaflet().then(() => initLeafletInternal()).catch(() => showDomStatic());
      });
  } else {
    loadLeaflet().then(() => initLeafletInternal()).catch((err) => { console.warn('Leaflet no disponible, usando fallback DOM:', err && err.message); showDomStatic(); });
  }
}

function startAnimation() {
  if (!map || !marker || animatedPoints.length === 0) return;
  stopAnimation();
  animationIndex = 0;
  animationHandle = setInterval(() => {
    animationIndex++;
    if (animationIndex >= animatedPoints.length) {
      clearInterval(animationHandle);
      animationHandle = null;
      return;
    }
    const p = animatedPoints[animationIndex];
    marker.setPosition(p);
  }, 100); // control speed here (ms per step)
}

function stopAnimation() {
  if (animationHandle) {
    clearInterval(animationHandle);
    animationHandle = null;
  }
}

// Fallback DOM animation when Google Maps is not available
let domAnimationHandle = null;
let domAnimationIndex = 0;
function startDomAnimation() {
  const container = document.getElementById('delivery-map');
  if (!container) return;
  stopDomAnimation();
  container.style.position = 'relative';

  // create or reuse motorcycle element
  let moto = document.getElementById('motorcycle-fallback');
  if (!moto) {
    moto = document.createElement('div');
    moto.id = 'motorcycle-fallback';
    moto.style.position = 'absolute';
    moto.style.top = '50%';
    moto.style.transform = 'translate(-12px, -50%)';
    moto.style.fontSize = '24px';
    moto.style.zIndex = 30;
    moto.textContent = '🏍️';
    container.appendChild(moto);
  }

  const padding = 24;
  const startX = padding;
  const endX = container.clientWidth - padding;
  const steps = 240;
  domAnimationIndex = 0;
  domAnimationHandle = setInterval(() => {
    domAnimationIndex++;
    if (domAnimationIndex > steps) {
      clearInterval(domAnimationHandle);
      domAnimationHandle = null;
      return;
    }
    const t = domAnimationIndex / steps;
    const x = startX + (endX - startX) * t;
    moto.style.left = `${x}px`;
  }, 80);
}

function stopDomAnimation() {
  if (domAnimationHandle) {
    clearInterval(domAnimationHandle);
    domAnimationHandle = null;
  }
}

// React to socket updates
function ensureAnimationForStatus() {
  // prefer Google Maps animation
  if (googleMapsKey && window.google && window.google.maps && map) {
    startAnimation();
    return;
  }
  // if leaflet available
  if (leafletMap && leafletMarker) {
    startLeafletAnimation();
    return;
  }
  // try to load leaflet then animate
  loadLeaflet()
    .then(() => {
      if (!leafletMap) initLeafletInternal();
      startLeafletAnimation();
    })
    .catch(() => {
      startDomAnimation();
    });
}

if (sock && orderId) {
  sock.on('order_status_updated', (payload) => {
    if (String(payload.order_id) !== String(orderId)) return;
    if (statusText) statusText.textContent = payload.status;
    const s = payload.status && payload.status.toLowerCase();
    if (s === 'en camino' || s === 'ruta') {
      ensureAnimationForStatus();
    } else {
      stopAnimation();
      stopLeafletAnimation();
      stopDomAnimation();
    }
  });
}

// Initialize on page load: if status already en camino/ruta, load maps and animate
if (statusText) {
  const s = statusText.textContent && statusText.textContent.trim().toLowerCase();
  if (s === 'en camino' || s === 'ruta') {
    ensureAnimationForStatus();
  }
}

// Debug helper to show current config in console
console.debug('tracking init', { orderId, googleMapsKey: !!googleMapsKey, startLat, startLng, endLat, endLng });

// Initialize visible display (map or fallback) immediately
initDisplay();
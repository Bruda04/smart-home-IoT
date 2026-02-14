// ================================================================
// SOCKET.IO OBJAŠNJENJE:
// Socket.io omogućava real-time двоправцима komunikaciju između veb aplikacije
// i servera. Koristi WebSocket protokol za brzu i efikasnu komunikaciju.
//
// 1. socket.emit() - Šalje podatke SA veb aplikacije NA server
//    Primer: socket.emit("deactivate_alarm", { pin: "1234" })
//
// 2. socket.on() - Prima podatke SA servera NA veb aplikaciju
//    Primer: socket.on("state_update", (data) => { ... })
//
// 3. Tok komunikacije:
//    WebApp --emit--> Server --on--> Obradi --emit--> WebApp --on-->
// ================================================================

// ===== INICIJALIZACIJA SOCKET.IO KONEKCIJE =====
const socket = io("http://localhost:5000");

// Objekat za skladištenje stanja aktuatora za sve PI računare
const actuatorData = {
  pi1: { dl_active: false, db_active: false },
  pi2: { dl_active: false, db_active: false },
  pi3: { dl_active: false, db_active: false },
};

// Objekat za RGB sijalicu
const rgbData = {
  power: false,
  color: "#ff0000", // Crvena
};

// ================================================================
// SOCKET EVENTI - PRIMANJE PODATAKA IZ SERVERA
// ================================================================

// Događaj: Konekcija sa serverom uspostavljena
socket.on("connect", () => {
  document.getElementById("connection-status").innerText = "Online";
  document
    .getElementById("connection-status")
    .classList.replace("text-red-500", "text-green-500");
  logEvent("✅ Veza sa serverom uspostavljena.");
});

// Događaj: Primanje ažuriranja stanja iz servera
socket.on("state_update", (data) => {
  // Odredi koji PI je poslao podatke (podrazumevano PI1)
  const pi = data.pi || "pi1";

  // Update: Broj osoba u objektu
  if (data.people_count !== undefined) {
    document.getElementById("people-count").innerText = data.people_count;
  }

  // Update: Status alarma (ON/OFF)
  const banner = document.getElementById("alarm-banner");
  const alarmStatusSection = document.getElementById("alarm-status-section");
  const alarmStatusText = document.getElementById("alarm-status-text");
  const alarmToggleBtn = document.getElementById("alarm-toggle-btn");

  if (data.alarm_active !== undefined) {
    if (data.alarm_active) {
      banner.classList.remove("hidden");
      alarmStatusSection.classList.replace("bg-gray-700", "bg-red-900/50");
      alarmStatusText.innerText = "Alarm ON";
      alarmStatusText.classList.replace("text-gray-400", "text-red-400");
      alarmToggleBtn.classList.remove("hidden");
      logEvent("🚨 ALARM je AKTIVIRAN!");
    } else {
      banner.classList.add("hidden");
      alarmStatusSection.classList.replace("bg-red-900/50", "bg-gray-700");
      alarmStatusText.innerText = "Alarm OFF";
      alarmStatusText.classList.replace("text-red-400", "text-gray-400");
      alarmToggleBtn.classList.add("hidden");
      logEvent("✅ Alarm je DEAKTIVIRAN.");
    }
  }

  // Update: Svetlo (DL) za određeni PI
  if (data.dl_active !== undefined) {
    actuatorData[pi].dl_active = data.dl_active;
    updateActuatorLEDs(pi);
  }

  // Update: Buzzer (DB) za određeni PI
  if (data.db_active !== undefined) {
    actuatorData[pi].db_active = data.db_active;
    updateActuatorLEDs(pi);
  }

  // Update: Status sistema (Aktiviran/Deaktiviran)
  const secStatus = document.getElementById("security-status");
  if (data.armed !== undefined) {
    if (data.armed) {
      secStatus.innerText = "AKTIVIRAN";
      secStatus.classList.replace("text-green-400", "text-red-400");
      logEvent("🔒 Sistem AKTIVIRAN");
    } else {
      secStatus.innerText = "DEAKTIVIRAN";
      secStatus.classList.replace("text-red-400", "text-green-400");
      logEvent("🔓 Sistem DEAKTIVIRAN");
    }
  }

  // Update: RGB Sijalica status
  if (data.rgb_active !== undefined) {
    rgbData.power = data.rgb_active;
    updateRGBStatus();
  }

  if (data.rgb_color !== undefined) {
    rgbData.color = data.rgb_color;
    document.getElementById("rgb-color-picker").value = data.rgb_color;
    updateRGBPreview();
  }

  // Log poruke sa servera
  if (data.msg) logEvent(data.msg);
});

// ================================================================
// FUNKCIJE ZA AKTUATORE (Svetla i Buzzer)
// ================================================================

// Prosledi izbor PI - poziva se kada korisnik promeni PI iz dropdown-a
function changeActuatorPI() {
  const selected = document.getElementById("actuator-pi-selector").value;
  logEvent(`📍 Prikazani aktuatori: ${selected.toUpperCase()}`);
  showActuatorDisplay(selected);
}

// Prikaži LED indikatore za odabrani PI
function showActuatorDisplay(pi) {
  // Sakrij sve displeje
  document.getElementById("pi1-actuator-display").classList.add("hidden");
  document.getElementById("pi2-actuator-display").classList.add("hidden");
  document.getElementById("pi3-actuator-display").classList.add("hidden");

  // Prikaži odabrani displej
  const displayElement = document.getElementById(`${pi}-actuator-display`);
  if (displayElement) {
    displayElement.classList.remove("hidden");
  }

  // Ažuriraj LED stanja za odabrani PI
  updateActuatorLEDs(pi);
}

// Ažuriraj LED indikatore - postavi boju zelena/siva na osnovu stanja
function updateActuatorLEDs(pi) {
  const data = actuatorData[pi] || { dl_active: false, db_active: false };

  // Mapa PI na ID elemente LED indikacija
  const ledMap = {
    pi1: { dl: "status-dl", db: "status-db" },
    pi2: { dl: "status-dl-pi2", db: "status-db-pi2" },
    pi3: { dl: "status-dl-pi3", db: "status-db-pi3" },
  };

  const ids = ledMap[pi];

  // Update DL LED (Svetlo)
  const dlLed = document.getElementById(ids.dl);
  if (dlLed) {
    if (data.dl_active) {
      dlLed.classList.add("led-active");
    } else {
      dlLed.classList.remove("led-active");
    }
  }

  // Update DB LED (Buzzer)
  const dbLed = document.getElementById(ids.db);
  if (dbLed) {
    if (data.db_active) {
      dbLed.classList.add("led-active");
    } else {
      dbLed.classList.remove("led-active");
    }
  }
}

// ================================================================
// FUNKCIJE ZA RGB SIJALICU
// ================================================================

// Ažuriraj prikaz boje u UI-u
function updateRGBPreview() {
  const color = document.getElementById("rgb-color-picker").value;
  rgbData.color = color;
  document.getElementById("rgb-preview").style.backgroundColor = color;
}

// Pošalji RGB komandu na server
function sendRGBCommand(command) {
  const color = document.getElementById("rgb-color-picker").value;
  const payload = {
    command: command,
    color: color,
  };

  socket.emit("rgb_control", payload);
  logEvent(`💡 RGB komanda poslana: ${command.toUpperCase()}`);

  if (command === "on") {
    rgbData.power = true;
    updateRGBStatus();
  } else if (command === "off") {
    rgbData.power = false;
    updateRGBStatus();
  } else if (command === "set") {
    rgbData.color = color;
    updateRGBStatus();
  }
}

// Ažuriraj status RGB sijalice u UI-u
function updateRGBStatus() {
  const status = document.getElementById("rgb-status");
  if (rgbData.power) {
    status.innerHTML = `Status: <span class="text-green-400">Uključeno</span> (${rgbData.color})`;
  } else {
    status.innerHTML = `Status: <span class="text-gray-400">Isključeno</span>`;
  }
}

// ================================================================
// FUNKCIJE ZA WEB KAMERU
// ================================================================

// Rukuj greškama pri učitavanju web kamere
function handleWebcamError() {
  const status = document.getElementById("webcam-status");
  status.innerHTML =
    '<span class="text-red-400">❌ Stream nije dostupan. Proveri URL.</span>';
}

// ================================================================
// FUNKCIJE ZA ALARME I SIGURNOST
// ================================================================

// Deaktiviraj alarm unošenjem PIN-a
function deactivateAlarm() {
  const pin = prompt("Unesite četvorocifreni PIN:");
  if (pin) {
    socket.emit("deactivate_alarm", { pin: pin });
    logEvent("🔓 PIN unesen za deaktiviranje alarma.");
  }
}

// Prikaži/sakrij dugme za gašenje alarma
function toggleAlarmUI() {
  const banner = document.getElementById("alarm-banner");
  if (!banner.classList.contains("hidden")) {
    deactivateAlarm();
  }
}

// ================================================================
// FUNKCIJE ZA KUHINJSKU ŠTOPERICU (TIMER)
// ================================================================

// Varijable za tracker vremena
let timerInterval = null;
let timerSeconds = 0;
let isRunning = false;
let isExpired = false;

// Parsiranje vremenske vrednosti iz input polja (MM:SS)
function parseTimeInput(input) {
  const parts = input.split(":");
  if (parts.length === 2) {
    const minutes = parseInt(parts[0]) || 0;
    const seconds = parseInt(parts[1]) || 0;
    return minutes * 60 + seconds;
  }
  return 0;
}

// Formatiranje vremenske vrednosti u MM:SS format
function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

// Ažuriraj prikaz vremena na ekranu
function updateTimerDisplay() {
  const display = document.getElementById("timer-display");
  const blinkDiv = document.getElementById("timer-blink");

  if (timerSeconds <= 0 && isRunning) {
    isRunning = false;
    isExpired = true;
    clearInterval(timerInterval);
    blinkDiv.classList.remove("hidden");
    document.getElementById("timer-status").innerText =
      "Status: ⏰ VRIJEME ISTEKLO!";
  }

  display.innerText = formatTime(timerSeconds);
}

// Pokreni brojanje vremena unazad
function startTimer() {
  if (isRunning) return;

  if (timerSeconds === 0) {
    const input = document.getElementById("timer-input").value;
    timerSeconds = parseTimeInput(input);
    if (timerSeconds === 0) {
      alert("Molimo unesite vreme u formatu MM:SS");
      return;
    }
  }

  isRunning = true;
  isExpired = false;
  document.getElementById("timer-blink").classList.add("hidden");
  document.getElementById("timer-status").innerText = "Status: ▶ POKRENUT";

  timerInterval = setInterval(() => {
    if (timerSeconds > 0) {
      timerSeconds--;
      updateTimerDisplay();
    }
  }, 1000);
}



// Pošalji podatke štoperice serveru
function sendTimerToServer() {
  if (timerSeconds > 0) {
    const payload = {
      time_remaining: timerSeconds,
      formatted_time: formatTime(timerSeconds),
      is_running: isRunning,
    };
    socket.emit("timer_update", payload);
    logEvent(`📤 Štoperica poslana serveru: ${formatTime(timerSeconds)}`);
  } else {
    alert("Postavite vreme pre nego što pošaljete na server!");
  }
}

// ================================================================
// FUNKCIJE ZA DEMO SCENARIJE (PI1 Prezentacija)
// ================================================================

// Pokretanje demo scenarija
function triggerScenario(type) {
  socket.emit("trigger_scenario", { scenario: type });
  logEvent(`🎬 Komanda: Pokretanje scenarija ${type}`);
}

// ================================================================
// FUNKCIJE ZA LOGOVANJE DOGAĐAJA
// ================================================================

// Log događaja sa vremenskom obeležavanjem
function logEvent(msg) {
  console.log(`[${new Date().toLocaleTimeString()}] ${msg}`);
  // Ako trebate prikazati u UI-u, odkomentarite:
  // const log = document.getElementById("event-log");
  // if (log) {
  //   const entry = document.createElement("div");
  //   entry.innerHTML = `<span class="text-blue-500">[${new Date().toLocaleTimeString()}]</span> ${msg}`;
  //   log.prepend(entry);
  // }
}

// ================================================================
// INICIJALIZACIJA PRI UČITAVANJU STRANICE
// ================================================================

document.addEventListener("DOMContentLoaded", () => {
  // Postavi PI1 kao podrazumevano
  const actuatorSelector = document.getElementById("actuator-pi-selector");
  if (actuatorSelector) {
    actuatorSelector.value = "pi1";
    showActuatorDisplay("pi1");
  }

  // Inicijalizuj RGB prikaz
  updateRGBPreview();
  updateRGBStatus();

  logEvent("✅ Veb aplikacija učitana i spremna.");
});

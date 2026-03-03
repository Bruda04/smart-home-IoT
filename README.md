# Smart Home IoT Project

This project is a smart home simulation platform designed for educational purposes, demonstrating the integration of sensors, actuators, and IoT communication using Python, MQTT, InfluxDB, and Grafana. The system is modular, simulating multiple Raspberry Pi nodes (PI1, PI2, PI3), each with its own set of sensors and actuators, and a central server for data collection and visualization.

## Features
- **Multiple simulated Raspberry Pi nodes** (PI1, PI2, PI3) with unique sensors and actuators
- **MQTT communication** via Mosquitto broker
- **Data storage** using InfluxDB
- **Real-time monitoring** and visualization with Grafana
- **Web interface** for user interaction
- **Docker Compose** for easy infrastructure setup

## Project Structure
```
├── infrastructure/         # Docker Compose, broker, InfluxDB, Grafana configs
├── PI1/                   # Node 1: sensors, actuators, logic
├── PI2/                   # Node 2: sensors, actuators, logic
├── PI3/                   # Node 3: sensors, actuators, logic
├── server/                # Central server, API, and settings
├── webapp/                # Web interface (HTML, JS, CSS)
└── README.md              # Project documentation
```

## Getting Started

### Prerequisites
- Python 3.x
- Docker & Docker Compose
- (Optional) Raspberry Pi hardware for real deployment

### Setup Instructions
1. **Clone the repository**
2. **Start infrastructure**
	```sh
	cd infrastructure
	docker-compose up -d
	```
3. **Install Python dependencies**
	```sh
	cd server
	pip install -r requirements.txt
	```
4. **Run the server**
	```sh
	python server.py
	```
5. **Run node simulations**
	- Each PI folder (PI1, PI2, PI3) contains a `main.py` to simulate a node:
	  ```sh
	  cd PI1
	  python main.py
	  ```
	- Repeat for PI2 and PI3 as needed.
6. **Access Grafana dashboard**
	- Open [http://localhost:3000](http://localhost:3000) (default credentials: admin/admin_password)
    - Import the dashboard from `infrastructure/grafana_dashboard_conf/grafana_dashboard.json` if not already set up.
7. **Access the web interface**
	- Open `webapp/index.html` in your browser

## Main Components

- **Sensors**: PIR, Ultrasonic, Button, DHT, Gyroscope, WebCam, etc.
- **Actuators**: Buzzer, DoorLight, SegmentDisplay, LCD, RGBLed, etc.
- **Communication**: MQTT (Mosquitto)
- **Database**: InfluxDB
- **Visualization**: Grafana
- **Web Interface**: HTML/JS/CSS frontend

## Configuration
- All settings for brokers, nodes, and server are in the respective `settings/` folders.
- MQTT broker config: `infrastructure/broker-config/mosquitto.conf`
- Grafana dashboard config: `infrastructure/grafana_dashboard_conf/grafana_dashboard.json`

## Useful Commands
- Start all services: `docker-compose up -d`
- Stop all services: `docker-compose down`
- View logs: `docker-compose logs`

## Authors
- [Luka Bradić](https://github.com/bruda04)
- [Marija Parežanin](https:///github.com/marijaparezanin)

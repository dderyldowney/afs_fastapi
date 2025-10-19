# AFS Equipment Support Reference  
*Version 1.0 — Verified October 2025*

This document lists **real-world agricultural equipment**—tractors, controllers, implements, and sensors—that can interoperate with the **AFS FastAPI** framework.  
Compatibility is determined by compliance with the **CAN 2.0B**, **SAE J1939**, and **ISO 11783 (ISOBUS)** network standards used in AFS equipment abstractions.

---

## 1 · Supported Network Standards

| Standard | Description | Typical Use in AFS |
|-----------|--------------|--------------------|
| **CAN 2.0B** | Base physical layer; 250 kbit/s or 500 kbit/s bus. | Low-level signal transport. |
| **SAE J1939** | High-level protocol on CAN for powertrain & machine control. | Tractor/ECU communications; diagnostic frames. |
| **ISO 11783 (ISOBUS)** | Agricultural extension of J1939; defines UT (Task Controller, Section Control, Variable Rate). | Tractor ↔ implement ↔ sensor integration. |

> AFS FastAPI’s `FarmTractor` and `ImplementInterface` classes conform to these standards.  
> Any hardware that properly implements ISOBUS will be directly addressable.

---

## 2 · Compatible Tractor Families

Any **AEF-certified ISOBUS tractor** can interoperate with AFS.  
Below are proven, field-validated families:

| Manufacturer | Example Models | Notes |
|---------------|----------------|-------|
| **John Deere** | 7R, 8R, 9R, 9RX series (Gen 4 / G5 displays) | Full AEF ISOBUS UT & TC support. |
| **Fendt** | 700, 800, 900 Vario series (FendtONE / Varioterminal) | Native ISOBUS TIM, Section Control, Variable Rate. |
| **New Holland** | T7, T8 Genesis (IntelliView IV/12) | PLM ecosystem, AEF-listed UT/TC. |
| **Case IH** | Magnum, Optum AFS Connect | Same AEF core as New Holland. |
| **Massey Ferguson** | MF 8700 S, MF 8S (Datatronic 5) | ISOBUS gateway and AEF-certified implement control. |

> ✅ Use the **AEF ISOBUS Database** (https://www.aef-isobus-database.org) to validate any specific tractor–implement pairing.

---

## 3 · Compatible ECUs / Controllers

AFS FastAPI can interface with ECUs that speak J1939 or ISOBUS and expose configurable I/O for valves, sensors, and actuators.

| Manufacturer | Model Family | Key Features |
|---------------|--------------|---------------|
| **STW Technik** | ESX-3XL / 3xm | Mobile I/O controller; J1939; CODESYS support. |
| **Danfoss** | PLUS+1 MC050-110 / MC010-110 | Rugged mobile controller; J1939; hydraulic control focus. |
| **ifm electronic** | ecomat R / CR1081 | Mobile PLC + HMI; native J1939 stack. |
| **Kvaser** | DIN Rail SE400S-X10 | Programmable CAN/CAN-FD gateway; J1939-compatible. |
| **PEAK System** | PCAN-Router Pro FD | 6-channel CAN/FD router for J1939/ISOBUS bridging. |

> Typical use in AFS: as tractor-mounted adapter nodes or implement controllers bridging physical I/O to AFS API endpoints.

---

## 4 · Supported Implements and Controllers

| Category | Example Model | Protocol | Capability |
|-----------|---------------|-----------|-------------|
| **Sprayer Controller** | Topcon Apollo CM-40 | ISOBUS UT / TC | Section Control & Multi-Product Rate Control |
| **Seeder/Spreader** | Any AEF-certified implement (John Deere, Amazone, Horsch, etc.) | ISOBUS UT / TC | Prescription map execution |
| **Hydraulic Control** | Danfoss PLUS+1 Hydraulic Blocks | J1939 / ISOBUS | Valve & pump actuation |
| **Generic Implement** | Custom I/O via STW ESX or ifm ecomat | J1939 | Custom device integration |

---

## 5 · Soil Sampling Systems

| Manufacturer | Model | Integration Method | Depth Capability |
|---------------|--------|--------------------|------------------|
| **Wintex Agro** | 1000 / 1000s / 2000 / 3000 | Hydraulic or electric control via J1939 ECU; GPS metadata logged through AFS FastAPI. | Up to 90 cm (W3000) |
| **Custom Probe Assemblies** | (AF compatible implement mount) | AFS adapter node controls hydraulics and sensors over CAN. | Variable by design |

> Note: AFS FastAPI does not ship OEM drivers for Wintex; integration is via standardized I/O control and GPS telemetry.

---

## 6 · Air / Atmospheric Sensors

| Manufacturer | Model | Protocol | Parameters Measured |
|---------------|--------|-----------|----------------------|
| **Müller-Elektronik** | ISOBUS Weather Station | ISOBUS UT / TC | Wind speed, temp, humidity, pressure |
| **Trimble** | Field-IQ ISOBUS Weather Station | ISOBUS UT / TC | Spray conditions monitoring |
| **Generic Environmental Sensors** | PM / gas / humidity sensors via J1939 ECU | J1939 | Air quality, temperature, CO₂, dust |

---

## 7 · Integration Mapping

| AFS Component | Physical Layer | Real-World Hardware Examples |
|----------------|----------------|-------------------------------|
| `FarmTractor` | ISOBUS / J1939 | Fendt Vario 700-900, JD 7R-9R, CNH T7/T8, MF 8700 S |
| `ImplementInterface` | ISOBUS | Topcon Apollo CM-40 sprayer, AEF-certified seeders/spreaders |
| `EquipmentECU` | J1939 | STW ESX-3XL, Danfoss MC050, ifm ecomat |
| `SoilSamplerNode` | J1939 + Hydraulics | Wintex 2000/3000 core samplers |
| `AtmosphericNode` | ISOBUS Sensor | Müller-Elektronik / Trimble weather stations |

---

## 8 · Validation Resources

- **AEF ISOBUS Database:** <https://www.aef-isobus-database.org>  
  Check compatibility of any tractor ↔ implement pairing.  
- **SAE J1939 Standard:** <https://www.sae.org/standards/content/j1939/>  
- **ISO 11783 Overview:** <https://www.iso.org/standard/71557.html>  

---

## 9 · Summary

The AFS FastAPI system supports any modern, AEF-certified tractor and implement built on **ISOBUS (ISO 11783)** or **SAE J1939**.  
Its abstraction layer maps cleanly onto real hardware from **John Deere**, **Fendt**, **Case IH**, **New Holland**, and **Massey Ferguson**, and it can drive controllers such as **STW ESX**, **Danfoss PLUS+1**, and **ifm ecomat**.  
Soil and atmospheric sensors (Wintex, Müller-Elektronik, Trimble) integrate through the same bus architecture.

---

*© 2025 CyberSpace Technologies Group — AFS Project Documentation*


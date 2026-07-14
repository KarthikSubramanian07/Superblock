# SuperBlock: A Decentralized Urban Nervous System for Climate Resilience

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

**SuperBlock** is a hardware-verified, privacy-preserving infrastructure for human-centered, climate-resilient cities. By turning citizen physiological stress into a real-time diagnostic engine, we identify **Urban Heat Islands (UHI)** and automate the deployment of nature-based cooling to save lives and optimize energy grids.

---

## 🏆 Prize Track Alignment

### 🍃 Sustain the Spark (Climate & Energy)
*   **The Vision**: Satellites measure air temperature; SuperBlock measures **Human Thermal Stress**.
*   **Grid Optimization**: Every 1°C reduction in a "Red Zone" results in a massive decrease in building HVAC energy demand, cutting carbon emissions and stabilizing the grid.
*   **Interventions**: AI-driven simulations for Shade Canopies, Vertical Gardens, and Cool Pavement with predicted **Biological Relief Coefficients**.

### 📱 ZETIC (On-Device AI) — NPU-First
*   **Melange SDK Integration**: Model deployed to ZETIC Melange platform (`winnerkarthik/superblock-stressnet v1`).
*   **REST API Integration**: Edge node uses ZETIC REST API for inference with CPU fallback.
*   **Note**: Full on-device Melange SDK requires mobile app (iOS/Android) for on-device NPU inference. Current implementation uses REST API from backend for hackathon demo.
*   **Performance**: Model optimized for NPU deployment with <50ms latency benchmarks.

### 🤖 Fetch.ai (Agentverse & ASI:One)
*   **Multi-Agent Orchestration**: A 6-agent reasoning chain discoverable via the **Almanac**.
*   **ASI:One Compatibility**: Fully compatible with the ASI:One Chat Protocol. Ask: *"What's the best $10k fix for the heat island in DTLA?"*
*   **Agent Address**: `agent1qfdrae3ezj3d6tghhu9q4fwglzkqr7cmkhg8lffqdfurm52hkc7xz2a5cgr`
*   **Agent Profile**: https://agentverse.ai/agents/details/agent1qfdrae3ezj3d6tghhu9q4fwglzkqr7cmkhg8lffqdfurm52hkc7xz2a5cgr

### 🆔 World ID (Proof of Human)
*   **Intent**: Use World ID so ingest can prefer verified unique humans.
*   **Hackathon note**: Demo mode accepts mock proofs; turn `DEMO_MODE=false` for fail-closed verification before public use.
*   **Why It Matters**:
    1. Prevents bot/sybil attacks on citizen sensor data - ensures each data point comes from a real human
    2. Fair resource allocation - prevents gaming of intervention prioritization
    3. Trust in public infrastructure - citizens can trust data driving city decisions comes from real humans
    4. Democratic participation - enables verified citizen feedback loop for urban planning

### 🔌 Arista Networks (High-Performance Networking)
*   **Data Routing**: Multi-agent orchestration routes citizen sensor data through specialized agents (Ingestion → Mapping → Diagnosis → Simulation → Planner → Narrator).
*   **Real-Time Networking**: WebSocket + REST fallback ensures low-latency data flow from edge devices to city intelligence backend.
*   **Resource Connection**: Connects people to resources by routing stress data to appropriate interventions (shade, cooling, traffic flow).

---

## 📂 Project Structure
- [**Master README (Technical)**](./LA_Hacks/backend_service/README.md): Full technical breakdown, API contracts, and install guides.
- [**Frontend Dashboard**](./superblock-ui): Live 3D Digital Twin (Deck.gl) and Agent Panel.
- [**ZETIC Edge Node**](./LA_Hacks/backend_service/scripts/zetic_mac_edge_node.py): Hardware simulator for NPU inference.
- [**ASI:One Skill**](./LA_Hacks/backend_service/scripts/asi1_superblock_skill.py): Discoverable chat agent for Agentverse.

### Demo vs production security
Local runs default to `DEMO_MODE=true` (open write routes for judges). Set `DEMO_MODE=false`, configure Auth0, and require real World ID proofs before any public deployment. Rotate any credentials that ever appeared in git history (ASI / Mongo / agent seeds).

---

## 🛠️ Built With
- **ZETIC Melange**: NPU-optimized AI infrastructure.
- **Fetch.ai uAgents**: Multi-agent orchestration and Almanac discovery.
- **World ID**: Proof-of-Humanity protocol.
- **Auth0**: Secure Agent-to-User identity.
- **MongoDB Atlas**: Durable telemetry persistence.
- **Mapbox & Deck.gl**: 3D Digital Twin visualization.
- **H3**: Uber's Hexagonal Hierarchical Spatial Index.

---

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

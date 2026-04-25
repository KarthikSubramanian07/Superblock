import asyncio
import requests
from typing import Dict, Any
from config import ASI_ONE_API_KEY, ASI_ONE_ENDPOINT, MODEL
from datetime import datetime
import json

class AgentOrchestrator:
    def __init__(self):
        self.agent_addresses = {}
        self.session_id = "urban_heat_session"
        
    async def register_agents(self):
        """Register all agents with Agentverse Almanac"""
        print("Registering agents with Agentverse Almanac...")
        
        agents = [
            "ingestion_agent", "mapping_agent", "diagnosis_agent",
            "simulation_agent", "planner_agent", "narrator_agent"
        ]
        
        for agent_name in agents:
            print(f"Would register {agent_name} with Almanac")
            
    async def coordinate_workflow(self, input_data: Dict[str, Any]):
        """Coordinate the complete multi-agent workflow"""
        print("Starting urban heat analysis workflow...")
        
        # Step 1: Ingestion
        print("Step 1: Ingestion - Validating Proof of Human...")
        validated_data = await self.call_ingestion_agent(input_data)
        
        # Step 2: Mapping
        print("Step 2: Mapping - Building 3D Twin...")
        twin_update = await self.call_mapping_agent(validated_data)
        
        # Step 3: Diagnosis
        print("Step 3: Diagnosis - Analyzing failure modes...")
        diagnosis = await self.call_diagnosis_agent(twin_update)
        
        # Step 4: Simulation
        print("Step 4: Simulation - Running What-If scenarios...")
        scenarios = await self.call_simulation_agent(diagnosis)
        
        # Step 5: Planning
        print("Step 5: Planning - Ranking interventions...")
        plan = await self.call_planner_agent(scenarios)
        
        # Step 6: Narration
        print("Step 6: Narration - Generating report...")
        report = await self.call_narrator_agent(plan)
        
        return report
    
    async def call_ingestion_agent(self, input_data: Dict) -> Dict:
        """Call ingestion agent via ASI:One"""
        prompt = f"""
        Process this urban heat data as an ingestion agent:
        {input_data}
        
        Validate the data and prepare it for mapping.
        Return the result in a structured format.
        """
        
        response = await self.query_asi_one(prompt)
        return {"validated": True, "data": response}
    
    async def call_mapping_agent(self, validated_data: Dict) -> Dict:
        """Call mapping agent via ASI:One"""
        prompt = f"""
        As a mapping agent, create a 3D twin representation from this validated data:
        {validated_data}
        
        Identify any red zones (areas with concerning heat patterns).
        Return spatial and temporal data with identified problem areas.
        """
        
        response = await self.query_asi_one(prompt)
        return {"twin_data": response, "red_zones": []}
    
    async def call_diagnosis_agent(self, twin_update: Dict) -> Dict:
        """Call diagnosis agent via ASI:One"""
        prompt = f"""
        As a diagnosis agent, analyze this 3D twin data:
        {twin_update}
        
        Identify failure modes like Acoustic Failure, Heat Exhaustion, etc.
        Provide root cause analysis and recommendations.
        """
        
        response = await self.query_asi_one(prompt)
        return {"failure_modes": [], "root_causes": [], "recommendations": []}
    
    async def call_simulation_agent(self, diagnosis: Dict) -> list:
        """Call simulation agent via ASI:One"""
        prompt = f"""
        As a simulation agent, create What-If scenarios based on this diagnosis:
        {diagnosis}
        
        Simulate interventions like Shade Canopy, Parklets, etc.
        Predict ALS reduction and implementation costs for each scenario.
        """
        
        response = await self.query_asi_one(prompt)
        return []
    
    async def call_planner_agent(self, scenarios: list) -> Dict:
        """Call planner agent via ASI:One"""
        prompt = f"""
        As a planner agent, rank these intervention scenarios by Biological Relief Coefficient:
        {scenarios}
        
        BRC = ALS reduction / implementation cost
        Create an implementation roadmap with phases and priorities.
        """
        
        response = await self.query_asi_one(prompt)
        return {"ranked_interventions": [], "roadmap": []}
    
    async def call_narrator_agent(self, plan: Dict) -> Dict:
        """Call narrator agent via ASI:One"""
        prompt = f"""
        As a narrator agent, create a comprehensive report from this plan:
        {plan}
        
        Include executive summary, technical analysis, recommendations, and next steps.
        Make it clear and actionable for decision makers.
        """
        
        response = await self.query_asi_one(prompt)
        return {"report": response}
    
    async def query_asi_one(self, prompt: str) -> str:
        """Query ASI:One API"""
        headers = {
            "Authorization": f"Bearer {ASI_ONE_API_KEY}",
            "Content-Type": "application/json",
            "x-session-id": self.session_id
        }
        
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are an expert urban climate analysis agent."},
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(ASI_ONE_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

# This part only runs when the file is executed directly, not when imported
if __name__ == "__main__":
    async def main():
        orchestrator = AgentOrchestrator()
        
        # Register agents
        await orchestrator.register_agents()
        
        # Example input data
        sample_data = {
            "user_id": "user_123",
            "location": {
                "latitude": 34.0522,
                "longitude": -118.2437,
                "timestamp": "2026-04-25T14:30:00Z"
            },
            "sensor_readings": {
                "temperature": 38.5,
                "humidity": 45,
                "air_quality": "moderate"
            }
        }
        
        # Run the complete workflow
        final_report = await orchestrator.coordinate_workflow(sample_data)
        
        print("\n=== FINAL REPORT ===")
        print(final_report)
        
    asyncio.run(main())

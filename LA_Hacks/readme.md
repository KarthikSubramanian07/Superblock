# Running The Script
remember to create virutal environment and pip the requirements 

python config.py
python orchestrator.py 

# Using The Dataset File
Dataset Features for Each Agent:
Ingestion Agent:
user_id, biometric_verified - Proof of Human validation
timestamp - Temporal data validation
All raw sensor readings for initial processing
Mapping Agent:
latitude, longitude - Spatial coordinates for 3D twin
temperature, humidity, air_quality - Environmental data
surface_material, vegetation_density - Surface characteristics
building_height, population_density - Urban density factors
Diagnosis Agent:
temperature trends - Heat exhaustion patterns
noise_level - Acoustic failure analysis
air_quality - Ventilation issues
wind_speed - Air circulation problems
heat_stress_level - Overall stress indicators
Simulation Agent:
surface_material - For testing cool roof scenarios
vegetation_density - For green space simulation
building_height - For shade structure placement
population_density - For parklet location planning
Planner Agent:
All numerical values for BRC calculation
activity_type - For intervention prioritization
Location data for implementation planning
Narrator Agent:
Complete dataset for comprehensive reporting
Temporal patterns for trend analysis
Spatial distribution for area-specific recommendations
import asyncio
import csv
from orchestrator import AgentOrchestrator
from typing import Dict, Any

def parse_csv_line(line: str) -> Dict[str, Any]:
    """Parse a single line from the dataset"""
    parts = line.strip().split(',')
    
    return {
        "timestamp": parts[0],
        "user_id": parts[1],
        "latitude": float(parts[2]),
        "longitude": float(parts[3]),
        "temperature": float(parts[4]),
        "humidity": float(parts[5]),
        "air_quality": parts[6],
        "noise_level": float(parts[7]),
        "wind_speed": float(parts[8]),
        "surface_material": parts[9],
        "vegetation_density": parts[10],
        "building_height": float(parts[11]),
        "population_density": parts[12],
        "biometric_verified": parts[13] == "yes",
        "activity_type": parts[14],
        "heat_stress_level": parts[15]
    }

def format_for_orchestrator(data: Dict[str, Any]) -> Dict[str, Any]:
    """Format the parsed data for the orchestrator"""
    return {
        "user_id": data["user_id"],
        "location": {
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "timestamp": data["timestamp"]
        },
        "sensor_readings": {
            "temperature": data["temperature"],
            "humidity": data["humidity"],
            "air_quality": data["air_quality"],
            "noise_level": data["noise_level"],
            "wind_speed": data["wind_speed"]
        },
        "biometric_verified": data["biometric_verified"]
    }

def save_results_to_csv(results, filename='results.csv'):
    """Save processing results to CSV file"""
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user_id', 'temperature', 'status', 'error'])
        
        for result in results:
            writer.writerow([
                result['user_id'],
                result.get('temperature', ''),
                result['status'],
                result.get('error', '')
            ])
    
    print(f"💾 Results saved to {filename}")

async def process_dataset():
    """Process the entire dataset"""
    print("🌡️  Urban Heat Island Dataset Processor")
    print("=" * 70)
    
    orchestrator = AgentOrchestrator()
    
    # Read from CSV file
    try:
        with open('dataset.csv', 'r') as f:
            dataset = f.read().strip().split('\n')

        # Skip header row if your CSV has one
        if dataset and dataset[0].startswith('timestamp'):
            dataset = dataset[1:]  # Skip the header
        
        print(f"📂 Loaded {len(dataset)} records from dataset.csv")
        
    except FileNotFoundError:
        print("❌ Error: dataset.csv not found!")
        print("   Make sure dataset.csv is in the same directory")
        return []
    except Exception as e:
        print(f"❌ Error reading dataset.csv: {e}")
        return []
    
    results = []
    total = len(dataset)
    
    for i, line in enumerate(dataset, 1):
        print(f"\n📍 Processing record {i}/{total}...")
        print("-" * 70)
        
        try:
            # Parse the line
            data = parse_csv_line(line)
            input_data = format_for_orchestrator(data)
            
            print(f"   User: {data['user_id']}")
            print(f"   Temperature: {data['temperature']}°C")
            print(f"   Air Quality: {data['air_quality']}")
            print(f"   Activity: {data['activity_type']}")
            
            # Run the orchestrator workflow
            report = await orchestrator.coordinate_workflow(input_data)
            
            results.append({
                "user_id": data['user_id'],
                "temperature": data['temperature'],
                "status": "success",
                "report": report
            })
            
            print(f"   ✅ Record {i} processed successfully")
            
        except Exception as e:
            print(f"   ❌ Record {i} failed: {e}")
            results.append({
                "user_id": data['user_id'] if 'data' in locals() else f"unknown_{i}",
                "temperature": data.get('temperature', '') if 'data' in locals() else '',
                "status": "failed",
                "error": str(e)
            })
        
        # Add a small delay to avoid overwhelming the API
        if i < total:
            await asyncio.sleep(1)
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 PROCESSING SUMMARY")
    print("=" * 70)
    
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'failed')
    
    print(f"✅ Successfully processed: {successful}/{total}")
    print(f"❌ Failed: {failed}/{total}")
    
    # Temperature analysis
    temps = [r['temperature'] for r in results if 'temperature' in r and r['temperature']]
    if temps:
        print(f"\n🌡️  Temperature Statistics:")
        print(f"   Average: {sum(temps)/len(temps):.1f}°C")
        print(f"   Max: {max(temps):.1f}°C")
        print(f"   Min: {min(temps):.1f}°C")
        
        # Count heat stress levels
        high_stress = sum(1 for t in temps if t > 40)
        print(f"   High heat stress incidents (>40°C): {high_stress}")
    
    print("\n" + "=" * 70)
    
    # Save results to CSV
    save_results_to_csv(results, 'results.csv')
    
    return results

if __name__ == "__main__":
    try:
        results = asyncio.run(process_dataset())
        print("\n🎉 Dataset processing complete!")
    except KeyboardInterrupt:
        print("\n\n⏹️  Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

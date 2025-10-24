from afs_fastapi.equipment.farm_tractors import FarmTractor

# Example usage:
tractor: FarmTractor = FarmTractor(
    "John Deere", "9RX", 2023, manual_url="https://www.example.com/manual"
)
print(
    f"Make: {tractor.make}, Model: {tractor.model}, Year: {tractor.year}, Manual: {tractor.manual_url}"
)
print(tractor.start_engine())
print(tractor.change_gear(1))
print(tractor.accelerate(10))
print(tractor.engage_power_takeoff())
print(tractor.accelerate(10))
print(tractor.disengage_power_takeoff())
print(tractor.accelerate(10))
print(tractor.change_gear(2))
print(tractor.activate_hydraulics())
print(tractor.brake(10))
print(tractor.stop_engine())

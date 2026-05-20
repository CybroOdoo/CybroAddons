# For testing measurement from scada ignition to odoo
# the daily production data will only register if corresponding tag has production boolean checked

import OdooClient

all_readings = []
# ==========================================
# 1. Prepare measurements for the FIRST tag
# ==========================================
tag1_path = "tag1"

# Standard measurements (Temperature & Pressure)
tag1_measurements = {
    "pressure": 1450.0,
    "temperature": 95.5,
}

for mtype, val in tag1_measurements.items():
    all_readings.append({
        "tag_path": tag1_path,
        "measurement_type": mtype,
        "value": float(val),
        "quality": "good"
    })

# Production Data (Produced Quantity)
all_readings.append({
    "tag_path": tag1_path,
    "measurement_type": "production",
    "scada_key": "tag1",
    "value": 250.5,
    "quality": "good"
})


# ==========================================
# 2. Prepare measurements for the SECOND tag
# ==========================================
tag2_path = "tag2"

# Standard measurements (Temperature & Pressure)
tag2_measurements = {
    "pressure": 1200.0,
    "temperature": 88.2,
}

for mtype, val in tag2_measurements.items():
    all_readings.append({
        "tag_path": tag2_path,
        "measurement_type": mtype,
        "value": float(val),
        "quality": "good"
    })

# Production Data (Produced Quantity)
all_readings.append({
    "tag_path": tag2_path,
    "measurement_type": "production",
    "scada_key": "tag1",
    "value": 180.0,
    "quality": "good"
})

# ==========================================
# 3. Push EVERYTHING in a single batch
# ==========================================
result = OdooClient.push_readings(all_readings)
print(result)

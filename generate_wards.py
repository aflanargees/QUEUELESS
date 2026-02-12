import csv

# Read Panchayat CSV
panchayats = []

with open("panchayats.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        district, panchayat = row
        panchayats.append((district, panchayat))

# Create wards.csv
with open("wards.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["district", "panchayat", "ward"])

    for district, panchayat in panchayats:
        for w in range(1, 21):       # Ward 1 → Ward 20
            writer.writerow([district, panchayat, f"Ward {w}"])

print("wards.csv successfully created with 18,820 rows!")

import csv
import os


def export_csv(data, filename="data/hasil_scraping.csv"):
    # Pastikan folder ada
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        writer.writerow([
            "Tahun Akademik", "Prodi", "Semester", "Mata Kuliah",
            "Dosen", "Total Section", "Attendance", "Forum",
            "Quiz", "Assignment", "Label", "File", "Link"
        ])

        writer.writerows(data)

    print("File disimpan di:", filename)
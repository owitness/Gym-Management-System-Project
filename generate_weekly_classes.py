from datetime import timedelta, datetime
from db import get_db

def generate_weekly_classes():
    with get_db() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM classes WHERE is_recurring = TRUE")
        recurring_classes = cursor.fetchall()

        for cls in recurring_classes:
            base_time = cls["schedule_time"]
            for weeks_out in range(1, 5):  # next 4 weeks
                new_time = base_time + timedelta(weeks=weeks_out)

                # Check if class already exists for that datetime
                cursor.execute("""
                    SELECT id FROM classes 
                    WHERE class_name = %s AND trainer_id = %s AND schedule_time = %s
                """, (cls["class_name"], cls["trainer_id"], new_time))

                existing = cursor.fetchone()
                if not existing:
                    cursor.execute("""
                        INSERT INTO classes (class_name, trainer_id, schedule_time, capacity, is_recurring)
                        VALUES (%s, %s, %s, %s, TRUE)
                    """, (cls["class_name"], cls["trainer_id"], new_time, cls["capacity"]))

        conn.commit()
        
if __name__ == "__main__":
    generate_weekly_classes()


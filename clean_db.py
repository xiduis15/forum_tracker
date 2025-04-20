# Script pour réinitialiser les last_post_id
import sqlite3

conn = sqlite3.connect('forum_tracker.db')
cursor = conn.cursor()
cursor.execute("UPDATE threads SET last_post_id = NULL")
conn.commit()
conn.close()

print("Tous les last_post_id ont été réinitialisés. Vous pouvez maintenant tester la récupération complète des posts.")
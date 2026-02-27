import sqlite3
from datetime import datetime, timedelta
import os

class Database:
    def __init__(self):
        self.db_path = "data/database.db"
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS config (
            guild_id INTEGER,
            key TEXT,
            value TEXT,
            PRIMARY KEY (guild_id, key)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS rates (
            guild_id INTEGER,
            category TEXT,
            rate REAL,
            PRIMARY KEY (guild_id, category)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS exchanger_limits (
            user_id INTEGER,
            guild_id INTEGER,
            limit REAL,
            PRIMARY KEY (user_id, guild_id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            channel_id INTEGER,
            owner_id INTEGER,
            category TEXT,
            inr_amount REAL,
            coin TEXT,
            claimed_by INTEGER,
            usd_amount REAL,
            completed INTEGER DEFAULT 0,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS upi_ids (
            user_id INTEGER,
            guild_id INTEGER,
            slot INTEGER,
            upi_id TEXT,
            PRIMARY KEY (user_id, guild_id, slot)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS volume (
            user_id INTEGER,
            guild_id INTEGER,
            category TEXT,
            amount REAL,
            date DATE,
            PRIMARY KEY (user_id, guild_id, category, date)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS staff_profit (
            user_id INTEGER,
            guild_id INTEGER,
            profit REAL DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS staff_join_date (
            user_id INTEGER,
            guild_id INTEGER,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, guild_id)
        )''')

        conn.commit()
        conn.close()

    def set_config(self, guild_id, key, value):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO config (guild_id, key, value) VALUES (?, ?, ?)''',
                  (guild_id, key, value))
        conn.commit()
        conn.close()

    def get_config(self, guild_id, key):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT value FROM config WHERE guild_id = ? AND key = ?''', (guild_id, key))
        result = c.fetchone()
        conn.close()
        return int(result[0]) if result else None

    def set_rate(self, guild_id, category, rate):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO rates (guild_id, category, rate) VALUES (?, ?, ?)''',
                  (guild_id, category, rate))
        conn.commit()
        conn.close()

    def get_rate(self, guild_id, category):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT rate FROM rates WHERE guild_id = ? AND category = ?''', (guild_id, category))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    def set_exchanger_limit(self, user_id, guild_id, limit):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO exchanger_limits (user_id, guild_id, limit) VALUES (?, ?, ?)''',
                  (user_id, guild_id, limit))
        conn.commit()
        conn.close()

    def get_exchanger_limit(self, user_id, guild_id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT limit FROM exchanger_limits WHERE user_id = ? AND guild_id = ?''',
                  (user_id, guild_id))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 1000.0

    def create_ticket(self, guild_id, channel_id, owner_id, category, coin):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO tickets (guild_id, channel_id, owner_id, category, coin)
                     VALUES (?, ?, ?, ?, ?)''',
                  (guild_id, channel_id, owner_id, category, coin))
        conn.commit()
        ticket_id = c.lastrowid
        conn.close()
        return ticket_id

    def get_ticket(self, ticket_id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT * FROM tickets WHERE ticket_id = ?''', (ticket_id,))
        result = c.fetchone()
        conn.close()
        return dict(result) if result else None

    def set_ticket_inr(self, ticket_id, inr_amount):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''UPDATE tickets SET inr_amount = ? WHERE ticket_id = ?''', (inr_amount, ticket_id))
        conn.commit()
        conn.close()

    def claim_ticket(self, ticket_id, user_id, usd_amount):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''UPDATE tickets SET claimed_by = ?, usd_amount = ? WHERE ticket_id = ?''',
                  (user_id, usd_amount, ticket_id))
        conn.commit()
        conn.close()

    def complete_ticket(self, ticket_id, user_id, guild_id, usd_amount, category):
        conn = self.get_connection()
        c = conn.cursor()

        c.execute('''UPDATE tickets SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE ticket_id = ?''',
                  (ticket_id,))

        today = datetime.utcnow().date()
        c.execute('''INSERT OR REPLACE INTO volume (user_id, guild_id, category, amount, date)
                     VALUES (?, ?, ?, 
                     COALESCE((SELECT amount FROM volume WHERE user_id = ? AND guild_id = ? AND category = ? AND date = ?), 0) + ?,
                     ?)''',
                  (user_id, guild_id, category, user_id, guild_id, category, today, usd_amount, today))

        c.execute('''INSERT OR REPLACE INTO staff_profit (user_id, guild_id, profit)
                     VALUES (?, ?,
                     COALESCE((SELECT profit FROM staff_profit WHERE user_id = ? AND guild_id = ?), 0) + ?)''',
                  (user_id, guild_id, user_id, guild_id, usd_amount))

        conn.commit()
        conn.close()

    def set_upi_id(self, user_id, guild_id, slot, upi_id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO upi_ids (user_id, guild_id, slot, upi_id) VALUES (?, ?, ?, ?)''',
                  (user_id, guild_id, slot, upi_id))
        conn.commit()
        conn.close()

    def get_upi_id(self, user_id, guild_id, slot):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT upi_id FROM upi_ids WHERE user_id = ? AND guild_id = ? AND slot = ?''',
                  (user_id, guild_id, slot))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    def get_volume_stats(self, guild_id):
        conn = self.get_connection()
        c = conn.cursor()
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        stats = {}
        for category in ["I2C", "C2I", "P2C", "C2P"]:
            c.execute('''SELECT SUM(amount) FROM volume WHERE guild_id = ? AND category = ? AND date = ?''',
                      (guild_id, category, today))
            daily = c.fetchone()[0] or 0
            stats[f"{category}_daily"] = daily

            c.execute('''SELECT SUM(amount) FROM volume WHERE guild_id = ? AND category = ? AND date >= ?''',
                      (guild_id, category, week_ago))
            weekly = c.fetchone()[0] or 0
            stats[f"{category}_weekly"] = weekly

            c.execute('''SELECT SUM(amount) FROM volume WHERE guild_id = ? AND category = ? AND date >= ?''',
                      (guild_id, category, month_ago))
            monthly = c.fetchone()[0] or 0
            stats[f"{category}_monthly"] = monthly

            c.execute('''SELECT SUM(amount) FROM volume WHERE guild_id = ? AND category = ?''',
                      (guild_id, category))
            alltime = c.fetchone()[0] or 0
            stats[f"{category}_alltime"] = alltime

        conn.close()
        return stats

    def get_leaderboard(self, guild_id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT user_id, 
                     COALESCE((SELECT SUM(amount) FROM volume WHERE volume.user_id = staff_profit.user_id AND volume.guild_id = staff_profit.guild_id), 0) as volume,
                     COALESCE(profit, 0) as profit,
                     (SELECT COUNT(*) FROM tickets WHERE claimed_by = staff_profit.user_id AND guild_id = staff_profit.guild_id AND completed = 1) as completed
                     FROM staff_profit WHERE guild_id = ?
                     ORDER BY volume DESC''',
                  (guild_id,))
        results = c.fetchall()
        conn.close()
        return [(r[0], r[1], r[2], r[3]) for r in results]

    def get_staff_profile(self, user_id, guild_id):
        conn = self.get_connection()
        c = conn.cursor()

        c.execute('''SELECT limit FROM exchanger_limits WHERE user_id = ? AND guild_id = ?''',
                  (user_id, guild_id))
        limit_result = c.fetchone()
        limit = limit_result[0] if limit_result else 0

        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        c.execute('''SELECT SUM(amount) FROM volume WHERE user_id = ? AND guild_id = ? AND date = ?''',
                  (user_id, guild_id, today))
        daily_volume = c.fetchone()[0] or 0

        c.execute('''SELECT SUM(amount) FROM volume WHERE user_id = ? AND guild_id = ? AND date >= ?''',
                  (user_id, guild_id, week_ago))
        weekly_volume = c.fetchone()[0] or 0

        c.execute('''SELECT SUM(amount) FROM volume WHERE user_id = ? AND guild_id = ? AND date >= ?''',
                  (user_id, guild_id, month_ago))
        monthly_volume = c.fetchone()[0] or 0

        c.execute('''SELECT SUM(amount) FROM volume WHERE user_id = ? AND guild_id = ?''',
                  (user_id, guild_id))
        alltime_volume = c.fetchone()[0] or 0

        c.execute('''SELECT COUNT(*) FROM tickets WHERE claimed_by = ? AND guild_id = ? AND completed = 1''',
                  (user_id, guild_id))
        completed = c.fetchone()[0]

        c.execute('''SELECT profit FROM staff_profit WHERE user_id = ? AND guild_id = ?''',
                  (user_id, guild_id))
        profit_result = c.fetchone()
        profit = profit_result[0] if profit_result else 0

        c.execute('''SELECT join_date FROM staff_join_date WHERE user_id = ? AND guild_id = ?''',
                  (user_id, guild_id))
        join_date_result = c.fetchone()
        join_date = join_date_result[0] if join_date_result else "Unknown"

        conn.close()

        return {
            'limit': limit,
            'daily_volume': daily_volume,
            'weekly_volume': weekly_volume,
            'monthly_volume': monthly_volume,
            'alltime_volume': alltime_volume,
            'completed': completed,
            'profit': profit,
            'join_date': join_date
        }

    def get_user_profile(self, user_id, guild_id):
        conn = self.get_connection()
        c = conn.cursor()

        c.execute('''SELECT COUNT(*) FROM tickets WHERE owner_id = ? AND guild_id = ? AND completed = 1''',
                  (user_id, guild_id))
        total_exchanges = c.fetchone()[0]

        c.execute('''SELECT SUM(usd_amount) FROM tickets WHERE owner_id = ? AND guild_id = ? AND completed = 1''',
                  (user_id, guild_id))
        total_volume_result = c.fetchone()[0]
        total_volume = total_volume_result if total_volume_result else 0

        c.execute('''SELECT completed_at FROM tickets WHERE owner_id = ? AND guild_id = ? AND completed = 1 ORDER BY completed_at DESC LIMIT 1''',
                  (user_id, guild_id))
        last_exchange_result = c.fetchone()
        last_exchange = last_exchange_result[0] if last_exchange_result else "Never"

        conn.close()

        return {
            'total_exchanges': total_exchanges,
            'total_volume': total_volume,
            'last_exchange': last_exchange
        }

    def set_staff_join_date(self, user_id, guild_id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''INSERT OR IGNORE INTO staff_join_date (user_id, guild_id) VALUES (?, ?)''',
                  (user_id, guild_id))
        conn.commit()
        conn.close()

    def get_next_ticket_id(self, guild_id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''SELECT MAX(ticket_id) FROM tickets WHERE guild_id = ?''', (guild_id,))
        result = c.fetchone()[0]
        conn.close()
        return (result + 1) if result else 1
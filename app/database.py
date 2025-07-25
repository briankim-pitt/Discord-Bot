import sqlite3
import os
from typing import List, Optional, Tuple
import json

class Database:
    def __init__(self, db_path: str = "discord_bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create user_settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    guild_id INTEGER,
                    auto_translate BOOLEAN DEFAULT FALSE,
                    transliterate BOOLEAN DEFAULT FALSE,
                    default_language TEXT DEFAULT 'Spanish',
                    target_language TEXT DEFAULT 'English',
                    current_card_index INTEGER DEFAULT 0,
                    quiz_mode BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create flashcards table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS flashcards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_settings (user_id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_flashcards_user_id ON flashcards(user_id)')
            
            conn.commit()
    
    def get_user_settings(self, user_id: int, guild_id: int = 0) -> dict:
        """Get user settings, create default if doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, guild_id, auto_translate, transliterate, 
                       default_language, target_language, current_card_index, quiz_mode
                FROM user_settings WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            
            if result is None:
                # Create default settings
                cursor.execute('''
                    INSERT INTO user_settings (user_id, guild_id, auto_translate, transliterate, 
                                             default_language, target_language)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, guild_id, False, False, 'Spanish', 'English'))
                conn.commit()
                
                return {
                    'user_id': user_id,
                    'guild_id': guild_id,
                    'auto_translate': False,
                    'transliterate': False,
                    'default_language': 'Spanish',
                    'target_language': 'English',
                    'current_card_index': 0,
                    'quiz_mode': False
                }
            
            return {
                'user_id': result[0],
                'guild_id': result[1],
                'auto_translate': bool(result[2]),
                'transliterate': bool(result[3]),
                'default_language': result[4],
                'target_language': result[5],
                'current_card_index': result[6],
                'quiz_mode': bool(result[7])
            }
    
    def update_user_setting(self, user_id: int, setting_name: str, value):
        """Update a specific user setting"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Ensure user exists first
            self.get_user_settings(user_id)
            
            # Map setting names to database columns
            column_map = {
                'auto_translate': 'auto_translate',
                'transliterate': 'transliterate',
                'default_language': 'default_language',
                'target_language': 'target_language',
                'current_card_index': 'current_card_index',
                'quiz_mode': 'quiz_mode'
            }
            
            if setting_name in column_map:
                column = column_map[setting_name]
                cursor.execute(f'''
                    UPDATE user_settings 
                    SET {column} = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                ''', (value, user_id))
                conn.commit()
    
    def add_flashcard(self, user_id: int, question: str, answer: str) -> int:
        """Add a new flashcard for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO flashcards (user_id, question, answer)
                VALUES (?, ?, ?)
            ''', (user_id, question, answer))
            conn.commit()
            return cursor.lastrowid
    
    def get_user_flashcards(self, user_id: int) -> List[dict]:
        """Get all flashcards for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, question, answer, created_at
                FROM flashcards 
                WHERE user_id = ?
                ORDER BY created_at ASC
            ''', (user_id,))
            
            results = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'question': row[1],
                    'answer': row[2],
                    'created_at': row[3]
                }
                for row in results
            ]
    
    def delete_flashcard(self, card_id: int, user_id: int) -> bool:
        """Delete a specific flashcard"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM flashcards 
                WHERE id = ? AND user_id = ?
            ''', (card_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_flashcard_count(self, user_id: int) -> int:
        """Get the number of flashcards for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM flashcards WHERE user_id = ?
            ''', (user_id,))
            return cursor.fetchone()[0]
    
    def clear_user_flashcards(self, user_id: int) -> int:
        """Clear all flashcards for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM flashcards WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
            return cursor.rowcount
    
    def get_database_stats(self) -> dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM user_settings')
            user_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM flashcards')
            card_count = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT user_id, COUNT(*) as card_count 
                FROM flashcards 
                GROUP BY user_id 
                ORDER BY card_count DESC 
                LIMIT 5
            ''')
            top_users = cursor.fetchall()
            
            return {
                'total_users': user_count,
                'total_flashcards': card_count,
                'top_users': [{'user_id': row[0], 'card_count': row[1]} for row in top_users]
            }

# Wrapper classes to maintain compatibility with existing code
class DatabaseSettings:
    """Wrapper class to maintain compatibility with existing Settings class"""
    
    def __init__(self, guild_id: int, user_id: int, db: Database):
        self.guild_id = guild_id
        self.user_id = user_id
        self.db = db
        self._settings = self.db.get_user_settings(user_id, guild_id)
    
    def _refresh_settings(self):
        """Refresh settings from database"""
        self._settings = self.db.get_user_settings(self.user_id, self.guild_id)
    
    def set_auto_t(self, value: bool):
        self.db.update_user_setting(self.user_id, 'auto_translate', value)
        self._settings['auto_translate'] = value
    
    def set_translit(self, value: bool):
        self.db.update_user_setting(self.user_id, 'transliterate', value)
        self._settings['transliterate'] = value
    
    def set_def_lang(self, value: str):
        self.db.update_user_setting(self.user_id, 'default_language', value)
        self._settings['default_language'] = value
    
    def set_tgt_lang(self, value: str):
        self.db.update_user_setting(self.user_id, 'target_language', value)
        self._settings['target_language'] = value
    
    def get_auto_t(self) -> bool:
        self._refresh_settings()
        return self._settings['auto_translate']
    
    def get_translit(self) -> bool:
        self._refresh_settings()
        return self._settings['transliterate']
    
    def get_def_lang(self) -> str:
        self._refresh_settings()
        return self._settings['default_language']
    
    def get_tgt_lang(self) -> str:
        self._refresh_settings()
        return self._settings['target_language']
    
    @property
    def current_card_index(self) -> int:
        self._refresh_settings()
        return self._settings['current_card_index']
    
    @current_card_index.setter
    def current_card_index(self, value: int):
        self.db.update_user_setting(self.user_id, 'current_card_index', value)
        self._settings['current_card_index'] = value
    
    @property
    def quiz_mode(self) -> bool:
        self._refresh_settings()
        return self._settings['quiz_mode']
    
    @quiz_mode.setter
    def quiz_mode(self, value: bool):
        self.db.update_user_setting(self.user_id, 'quiz_mode', value)
        self._settings['quiz_mode'] = value

class DatabaseCard:
    """Wrapper class to maintain compatibility with existing Card class"""
    
    def __init__(self, question: str, answer: str, card_id: int = None):
        self.question = question
        self.answer = answer
        self.id = card_id
    
    def get_question(self) -> str:
        return self.question
    
    def get_answer(self) -> str:
        return self.answer
    
    def set_question(self, question: str):
        self.question = question
    
    def set_answer(self, answer: str):
        self.answer = answer

# Global database instance
db = Database()

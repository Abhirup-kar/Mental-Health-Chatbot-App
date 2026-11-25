CREATE DATABASE IF NOT EXISTS mental_health_chatbot
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE mental_health_chatbot;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    username VARCHAR(60) NOT NULL UNIQUE,
    email VARCHAR(160) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS chat_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(160) NOT NULL DEFAULT 'New Check-In',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_sessions_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_sessions_user_updated (user_id, updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS videos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    channel VARCHAR(120) NOT NULL,
    youtube_id VARCHAR(32) NOT NULL UNIQUE,
    url VARCHAR(255) NOT NULL,
    sentiment ENUM('positive', 'negative', 'neutral') NOT NULL,
    emotion_tag VARCHAR(60) NOT NULL,
    duration_label VARCHAR(40) NOT NULL,
    description TEXT NOT NULL,
    INDEX idx_videos_sentiment (sentiment, emotion_tag)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    user_id INT NOT NULL,
    sender ENUM('user', 'bot') NOT NULL,
    message_text TEXT NOT NULL,
    sentiment ENUM('positive', 'negative', 'neutral') DEFAULT NULL,
    sentiment_score DECIMAL(5, 4) DEFAULT NULL,
    emotion VARCHAR(60) DEFAULT NULL,
    detected_intent VARCHAR(80) DEFAULT NULL,
    engine_used VARCHAR(40) DEFAULT NULL,
    recommended_video_ids TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_messages_session FOREIGN KEY (session_id)
        REFERENCES chat_sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_messages_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_messages_session_created (session_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sentiment_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_id INT NOT NULL,
    message_id INT NOT NULL,
    sentiment ENUM('positive', 'negative', 'neutral') NOT NULL,
    score DECIMAL(5, 4) NOT NULL,
    emotion VARCHAR(60) NOT NULL,
    pattern_trend VARCHAR(40) NOT NULL DEFAULT 'stable',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_logs_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_logs_session FOREIGN KEY (session_id)
        REFERENCES chat_sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_logs_message FOREIGN KEY (message_id)
        REFERENCES chat_messages(id) ON DELETE CASCADE,
    INDEX idx_logs_user_created (user_id, created_at),
    INDEX idx_logs_session_created (session_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO videos
    (title, channel, youtube_id, url, sentiment, emotion_tag, duration_label, description)
VALUES
    ('How to practice emotional first aid', 'TED (Guy Winch)', 'F2hc2FLOdhI', 'https://www.youtube.com/watch?v=F2hc2FLOdhI', 'negative', 'sadness', '17 min', 'Psychologist Guy Winch explains practical ways to care for emotional wounds like rejection, loneliness, and rumination.'),
    ('How to cope with anxiety', 'TEDx Talks (Olivia Remes)', 'WWloIAQpMcQ', 'https://www.youtube.com/watch?v=WWloIAQpMcQ', 'negative', 'anxiety', '15 min', 'Evidence-based coping strategies for regaining control, quieting anxious loops, and finding purpose.'),
    ('How to Make Anxiety Your Friend', 'TED (David H. Rosmarin)', 'cTnPqgL8ZPs', 'https://www.youtube.com/watch?v=cTnPqgL8ZPs', 'negative', 'anxiety', '12 min', 'Clinical psychologist David H. Rosmarin shares how accepting anxiety can build emotional resilience.'),
    ('Box breathing relaxation technique: how to calm feelings of stress or anxiety', 'Sunnybrook Hospital', 'tEmt1Znux58', 'https://www.youtube.com/watch?v=tEmt1Znux58', 'negative', 'anxiety', '4 min', 'A quick guided 4-4-4-4 box breathing exercise to calm your nervous system during acute stress or anxiety.'),
    ('How to Make Stress Your Friend', 'TED (Kelly McGonigal)', 'RcGyVTAoXEU', 'https://www.youtube.com/watch?v=RcGyVTAoXEU', 'negative', 'stress', '14 min', 'Health psychologist Kelly McGonigal shows how reframing stress responses supports resilience and connection.'),
    ('STRESS BUSTER! - Guided Meditation & Exercise to Release Tension & Stress', 'New Horizon', 'Poy9UE3xM6w', 'https://www.youtube.com/watch?v=Poy9UE3xM6w', 'negative', 'stress', '10 min', 'A soothing guided relaxation and tension-release exercise for unwinding after a demanding day.'),
    ('Relieve Stress & Anxiety with Simple Breathing Techniques', 'AskDoctorJo', 'odADwWzHR24', 'https://www.youtube.com/watch?v=odADwWzHR24', 'negative', 'anger', '7 min', 'Practical paced-breathing routines to release physical agitation, frustration, and acute tension.'),
    ('15 Minute Deep Breathing Exercise', 'City of Hope', 'F28MGLlpP90', 'https://www.youtube.com/watch?v=F28MGLlpP90', 'negative', 'sleep', '15 min', 'A gentle 15-minute deep breathing session ideal for easing restlessness and preparing for rest.'),
    ('All it takes is 10 mindful minutes', 'TED (Andy Puddicombe)', 'qzR62JJCMBQ', 'https://www.youtube.com/watch?v=qzR62JJCMBQ', 'neutral', 'mindfulness', '10 min', 'Mindfulness expert Andy Puddicombe introduces how ten quiet minutes a day can refresh perspective.'),
    ('Daily Calm | 10 Minute Mindfulness Meditation | Be Present', 'Calm', 'ZToicYcHIOU', 'https://www.youtube.com/watch?v=ZToicYcHIOU', 'neutral', 'mindfulness', '10 min', 'A steady 10-minute guided mindfulness practice focused on breath awareness and staying present.'),
    ('5-Minute Meditation You Can Do Anywhere', 'Goodful', 'inpok4MKVLM', 'https://www.youtube.com/watch?v=inpok4MKVLM', 'neutral', 'neutral', '5 min', 'A short, accessible five-minute reset for centering yourself anytime during a routine day.'),
    ('The Power of Vulnerability', 'TED (Brené Brown)', 'iCvmsMzlF7o', 'https://www.youtube.com/watch?v=iCvmsMzlF7o', 'neutral', 'self_reflection', '20 min', 'Researcher Brené Brown explores human connection, authenticity, and reflective self-compassion.'),
    ('Want to be happy? Be grateful', 'TED (David Steindl-Rast)', 'UtBsl3j0YRQ', 'https://www.youtube.com/watch?v=UtBsl3j0YRQ', 'positive', 'gratitude', '14 min', 'Brother David Steindl-Rast reflects on how slowing down to notice gratitude deepens everyday joy.'),
    ('The happy secret to better work', 'TED (Shawn Achor)', 'fLJsdqxnZb0', 'https://www.youtube.com/watch?v=fLJsdqxnZb0', 'positive', 'happiness', '12 min', 'Psychologist Shawn Achor shares upbeat research on how positive mindset fuels resilience and creativity.'),
    ('What Makes a Good Life? Lessons from the Longest Study on Happiness', 'TED (Robert Waldinger)', '8KkKuTCFvzI', 'https://www.youtube.com/watch?v=8KkKuTCFvzI', 'positive', 'flourishing', '13 min', 'Insights from the Harvard Study of Adult Development on nurturing warm relationships and long-term well-being.');

USE task_manager;

CREATE TABLE IF NOT EXISTS tasks (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT NULL,
    status ENUM('pending', 'in_progress', 'completed') NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_tasks_status (status),
    INDEX idx_tasks_created_at (created_at)
);

INSERT INTO tasks (title, description, status)
SELECT 'Welcome to your task manager',
       'Create, update, and complete tasks using this sample application.',
       'pending'
WHERE NOT EXISTS (SELECT 1 FROM tasks);

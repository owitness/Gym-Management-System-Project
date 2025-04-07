CREATE DATABASE `gym_management_test` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

CREATE TABLE `attendance` (
  `id` int NOT NULL AUTO_INCREMENT,
  `member_id` int NOT NULL,
  `check_in_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `check_out_time` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_attendance_member_id` (`member_id`),
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`member_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `class_bookings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `member_id` int NOT NULL,
  `class_id` int NOT NULL,
  `booking_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_class_bookings_member_id` (`member_id`),
  KEY `idx_class_bookings_class_id` (`class_id`),
  CONSTRAINT `class_bookings_ibfk_1` FOREIGN KEY (`member_id`) REFERENCES `users` (`id`),
  CONSTRAINT `class_bookings_ibfk_2` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `classes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` text,
  `instructor_id` int DEFAULT NULL,
  `schedule` datetime DEFAULT NULL,
  `capacity` int DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `instructor_id` (`instructor_id`),
  CONSTRAINT `classes_ibfk_1` FOREIGN KEY (`instructor_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `memberships` (
  `id` int NOT NULL AUTO_INCREMENT,
  `member_id` int NOT NULL,
  `start_date` date NOT NULL,
  `expiry_date` date NOT NULL,
  `status` enum('active','expired','pending') DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_memberships_user_id` (`member_id`),
  CONSTRAINT `memberships_ibfk_1` FOREIGN KEY (`member_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `payment_methods` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `card_number` varchar(16) NOT NULL,
  `exp` date NOT NULL,
  `cvv` varchar(3) NOT NULL,
  `card_holder_name` varchar(100) NOT NULL,
  `saved` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `payment_methods_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `payments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `status` enum('Completed','Pending','Failed') DEFAULT NULL,
  `transaction_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `payment_method_id` int DEFAULT NULL,
  `membership_duration` int NOT NULL,
  `membership_expiry` date NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_payments_user_id` (`user_id`),
  KEY `idx_payments_payment_method_id` (`payment_method_id`),
  CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `payments_ibfk_2` FOREIGN KEY (`payment_method_id`) REFERENCES `payment_methods` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','member','non_member') DEFAULT 'non_member',
  `dob` date DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `city` varchar(255) DEFAULT NULL,
  `state` varchar(50) DEFAULT NULL,
  `zipcode` varchar(20) DEFAULT NULL,
  `membership_expiry` datetime DEFAULT NULL,
  `auto_payment` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
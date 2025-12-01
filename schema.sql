SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";



CREATE DATABASE IF NOT EXISTS `progkeeper` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `progkeeper`;




CREATE TABLE `users` (
	`id` int(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
	`username` varchar(50) NOT NULL UNIQUE,
	`nickname` varchar(50) DEFAULT '',
	`password` varchar(255) NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
	`profile_image` tinytext NOT NULL DEFAULT '',
	`banner_image` tinytext NOT NULL DEFAULT '',
	`about` text NOT NULL DEFAULT '',
	`timezone` tinytext NOT NULL DEFAULT 'UTC'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `collections` (
  `id` int(11) NOT NULL PRIMARY KEY AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `type` varchar(50) NOT NULL,
  `display_image` tinyint NOT NULL DEFAULT 1,
  `display_score` tinyint NOT NULL DEFAULT 1,
  `display_progress` tinyint NOT NULL DEFAULT 1,
  `display_user_started` tinyint NOT NULL DEFAULT 1,
  `display_user_finished` tinyint NOT NULL DEFAULT 1,
  `display_days` tinyint NOT NULL DEFAULT 1,
  `rating_system` tinyint NOT NULL DEFAULT 10,
  `private` tinyint NOT NULL DEFAULT 0,
  `deleted` tinyint NOT NULL DEFAULT 0,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  INDEX `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `media` (
  `id` int(15) NOT NULL PRIMARY KEY AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `collection_id` int(11) NOT NULL,
  `status` tinytext NOT NULL DEFAULT 'planned',
  `name` tinytext NOT NULL,
  `image` tinytext NOT NULL DEFAULT '',
  `score` int(3) DEFAULT 0,
  `episodes` smallint(6) DEFAULT 0,
  `progress` smallint(6) NOT NULL DEFAULT 0,
  `rewatched` smallint(6) NOT NULL DEFAULT 0,
  `user_started_at` date DEFAULT NULL,
  `user_finished_at` date DEFAULT NULL,
  `started_at` date DEFAULT NULL,
  `finished_at` date DEFAULT NULL,
  `description` text NOT NULL DEFAULT '',
  `comments` text NOT NULL DEFAULT '',
  `anilist` tinytext DEFAULT NULL,
  `myanimelist` tinytext DEFAULT NULL,
  `imdb` tinytext DEFAULT NULL,
  `tmdb` tinytext DEFAULT NULL,
  `adult` boolean NOT NULL DEFAULT FALSE,
  `favourite` boolean NOT NULL DEFAULT FALSE,
  `private` tinyint NOT NULL DEFAULT 0,
  `deleted` boolean NOT NULL DEFAULT FALSE,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  FOREIGN KEY (`collection_id`) REFERENCES `collections`(`id`),
  INDEX `user_id` (`user_id`),
  INDEX `collection_id` (`collection_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `activity` (
  `user_id` int(11) NOT NULL,
  `type` tinyint NOT NULL DEFAULT 0,
  `media_id` int(15) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp(),
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  INDEX `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `jobs` (
  `id` int(11) PRIMARY KEY AUTO_INCREMENT,
  `user_id` int(11),
  `type` text NOT NULL,
  `progress` int(2) NOT NULL DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `started_at` timestamp DEFAULT NULL,
  `completed_at` timestamp DEFAULT NULL,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  INDEX `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


CREATE TABLE `sessions` (
  `id` varchar(64) NOT NULL PRIMARY KEY,
  `started` timestamp NOT NULL DEFAULT current_timestamp(),
  `expiry` int(11) NOT NULL DEFAULT 0,
  `user_id` int(11) NOT NULL,
  `user_ip` json NOT NULL,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  INDEX `user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
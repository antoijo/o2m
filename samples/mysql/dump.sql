-- phpMyAdmin SQL Dump
-- version 5.0.2
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Aug 04, 2023 at 04:50 PM
-- Server version: 10.6.14-MariaDB
-- PHP Version: 7.4.33

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `joan4181_o2m`
--

-- --------------------------------------------------------

--
-- Table structure for table `stats`
--

CREATE TABLE `stats` (
  `uri` varchar(255) NOT NULL,
  `last_read_date` bigint(20) NOT NULL,
  `read_position` int(11) NOT NULL DEFAULT 0 COMMENT 'Last read position',
  `read_end` tinyint(1) NOT NULL DEFAULT 0 COMMENT 'Is last read gone to end ? (Boolean)',
  `read_count` tinyint(11) NOT NULL DEFAULT 0 COMMENT 'Count total read',
  `read_count_end` tinyint(11) NOT NULL DEFAULT 0 COMMENT 'Count total read to end',
  `skipped_count` tinyint(11) NOT NULL DEFAULT 0 COMMENT 'Count total skipped actions',
  `in_library` varchar(16) DEFAULT NULL COMMENT 'Is track in library ? If yes : uri cntainer value',
  `day_time_average` tinyint(2) DEFAULT NULL COMMENT 'Compute each read end day time average (1-24)',
  `option_type` varchar(16) NOT NULL,
  `username` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `stats`
--

-- --------------------------------------------------------

--
-- Table structure for table `stats_raw`
--

CREATE TABLE `stats_raw` (
  `Id` int(11) NOT NULL,
  `read_date` bigint(20) NOT NULL,
  `uri` varchar(255) NOT NULL,
  `read_hour` tinyint(2) NOT NULL,
  `username` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;

--
-- Dumping data for table `stats_raw`
--


-- --------------------------------------------------------

--
-- Table structure for table `tag`
--

CREATE TABLE `tag` (
  `uid` varchar(14) DEFAULT NULL,
  `user` varchar(16) DEFAULT NULL,
  `tag_type` varchar(29) DEFAULT NULL COMMENT 'Can be : spotify:playlist,artist,album,genre / podcast: or tunein:station or local:artist,album or iris:playlist (meta box)',
  `data` varchar(92) DEFAULT '' COMMENT 'Examples : local:album:md5:e431c158da4fbb855da74cc68e2c845\r\nspotify:album:3gPOWmWT0q7Ygp95Xiuw1v\r\nm3u:iris.m3u8\r\npodcast+https://feed.pippa.io/public/shows/5b0030a',
  `data_alt` text DEFAULT NULL,
  `description` varchar(53) DEFAULT NULL,
  `read_count` smallint(6) DEFAULT NULL,
  `last_read_date` bigint(20) DEFAULT NULL,
  `option_type` varchar(16) DEFAULT 'normal' COMMENT 'option card type : normal (default), new (discover card:only play new tracks), favorites (preferred tracks), hidden (not considered by stats)',
  `option_new` int(2) DEFAULT NULL COMMENT 'depreciated',
  `option_sort` varchar(16) DEFAULT NULL COMMENT 'shuffle, desc, asc',
  `option_duration` int(16) DEFAULT NULL COMMENT 'in sec',
  `option_max_results` int(16) DEFAULT NULL COMMENT 'in tracks numbers',
  `option_discover_level` int(16) DEFAULT 5 COMMENT 'from 0-10',
  `option_last_unread` smallint(6) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tag`
--

INSERT INTO `tag` (`uid`, `user`, `tag_type`, `data`, `data_alt`, `description`, `read_count`, `last_read_date`, `option_type`, `option_new`, `option_sort`, `option_duration`, `option_max_results`, `option_discover_level`, `option_last_unread`) VALUES
('beta_news', '1181464119', 'spotify:playlist', 'spotify:playlist:37i9dQZEVXcFRmKfy3mdyu', '', 'Mes decouvertes de la semaine', 0, 1686827507, 'new', 0, 'shuffle', 0, 30, 0, NULL),
('beta_podcast', '1181464119', 'podcast', 'infos:library', '', 'Podcasts', 171, 1682678797, 'podcast', 0, 'shuffle', 0, 10, 5, NULL),
('beta_favorites', '1181464119', 'spotify:playlist', 'spotify:playlist:4oXELBuV9B6QtxYwMdzsoE', '', 'Beta Favorites', 0, 1686472653, 'favorites', 0, 'shuffle', 0, 30, 4, NULL),
('beta_trash', '1181464119', 'spotify:playlist', 'spotify:playlist:4CAjrciXNfqiDdr757UwBx', NULL, 'Trash', 0, 1608365810, 'trash', 0, NULL, NULL, 15, 5, NULL),
('beta_incoming', '1181464119', 'spotify:playlist', 'spotify:playlist:0zM5DUb7FYRVvVjBg3ULp3', NULL, 'Incoming', 1, 1686824105, 'incoming', 0, 'shuffle', NULL, 15, 5, NULL),
('mopidy_tag', '1181464119', 'mopidy_tag', ' mopidy_tag', NULL, 'mopidy_tag', 0, 1621086457, 'new_mopidy', NULL, NULL, NULL, 30, 3, NULL);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `stats`
--
ALTER TABLE `stats`
  ADD UNIQUE KEY `uri` (`uri`);

--
-- Indexes for table `stats_raw`
--
ALTER TABLE `stats_raw`
  ADD PRIMARY KEY (`Id`),
  ADD KEY `read_date` (`read_date`) USING BTREE;

--
-- Indexes for table `tag`
--
ALTER TABLE `tag`
  ADD UNIQUE KEY `uid_index` (`uid`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `stats_raw`
--
ALTER TABLE `stats_raw`
  MODIFY `Id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
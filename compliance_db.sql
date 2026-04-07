-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 07, 2026 at 10:20 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `compliance_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `otp_codes`
--

CREATE TABLE `otp_codes` (
  `id` int(11) NOT NULL,
  `email` varchar(255) NOT NULL,
  `otp` varchar(6) NOT NULL,
  `created_at` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `otp_codes`
--

INSERT INTO `otp_codes` (`id`, `email`, `otp`, `created_at`) VALUES
(19, 'ganeshkumarreddyp1219.sse@saveetha.com', '825851', '2026-03-12 08:58:34'),
(23, 'ganeshpampula.sse@saveetha.com', '223722', '2026-03-14 07:01:46'),
(39, 'mahaboobsubhanisk1745.sse@saveetha.com', '292495', '2026-03-14 07:03:10'),
(59, 'nithinkumarch1625.sse@saveetha.com', '507816', '2026-03-26 05:18:36'),
(66, 'rajashekharr1205.sse@saveetha.com', '733020', '2026-03-30 03:38:07');

-- --------------------------------------------------------

--
-- Table structure for table `reports`
--

CREATE TABLE `reports` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `report_name` varchar(255) DEFAULT NULL,
  `transcript` text DEFAULT NULL,
  `score` int(11) DEFAULT NULL,
  `verdict` varchar(255) DEFAULT NULL,
  `duration` varchar(20) DEFAULT NULL,
  `recording_url` varchar(255) DEFAULT NULL,
  `patient_info` text DEFAULT NULL,
  `folder_name` varchar(100) DEFAULT 'Audits',
  `timestamp` bigint(20) DEFAULT NULL,
  `department` varchar(255) DEFAULT NULL,
  `date_of_consultation` varchar(50) DEFAULT NULL,
  `remarks` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `reports`
--

INSERT INTO `reports` (`id`, `user_id`, `report_name`, `transcript`, `score`, `verdict`, `duration`, `recording_url`, `patient_info`, `folder_name`, `timestamp`, `department`, `date_of_consultation`, `remarks`) VALUES
(14, 4, 'Test Report', 'Test transcript', 85, 'Interested', '05 : 30', NULL, NULL, 'Audits', 1234567890, NULL, NULL, NULL),
(31, 1, 'sanjay', 'yes doctor I understand the treatment plan and I will definitely come for the next appointment the medicine you gave is helping and the pain has reduced a lot you taking the medicine and following all your instruction I will come tomorrow for the check up and I will arrive on time thank you doctor for the treatment ', 97, 'Interested', '00:00', NULL, 'Dept: Prosthodintics | Date: 27 Mar 2026', 'Consultation Audits', 1774582911895, 'Prosthodintics', '27 Mar 2026', 'Mostly willing to attend'),
(32, 1, 'Kiran', 'the pain is not very serious now and I will a bit busy it work I cannot come for the appointment this week maybe I will visit later if the paining crisis I will skip the appointment ', 0, 'Not Interested', '00:23', NULL, 'Dept: Oral Surgery | Date: 27 Mar 2026', 'Consultation Audits', 1774583006266, 'Oral Surgery', '27 Mar 2026', 'cannot visit'),
(33, 1, 'sateesh', 'Dr I am feeling a little better now but I still have some oil pain sometimes I think the medicine is helping try to come next week for the check up but I need to check my work schedule for I\'ll come from the appointment later', 87, 'Interested', '00:00', NULL, 'Dept: Prosthodontic | Date: 24 Mar 2026', 'Consultation Audits', 1774583107381, 'Prosthodontic', '24 Mar 2026', 'communicating well'),
(34, 1, 'Sai', 'I feel slightly better now but sometimes the tooth still hurts when I drink cold water I\'ll try to follow the treatment instructions and continue the medicine if possible I will try to visit the clinic sometime Nagar check up ', 55, 'Not Interested', '00:29', NULL, 'Dept: oral surgery | Date: 08 Mar 2026', 'Consultation Audits', 1774583838621, 'oral surgery', '08 Mar 2026', 'NA'),
(35, 1, 'kohli', 'sure doctor thank you for explaining the treatment clearly I feel much better after using the mouthwash and the swelling has reduced I will follow all the instructions he gave me and I will take the medicine regularly clinic tomorrow for the follow appointment and continue the treatment ', 95, 'Interested', '00:23', NULL, 'Dept: Prosthodontic | Date: 17 Mar 2026', 'Consultation Audits', 1774585571835, 'Prosthodontic', '17 Mar 2026', 'more interested'),
(36, 1, 'e', 'today went for dental surgery it went good ', 54, 'Not Interested', '00:06', NULL, 'Dept: Prosthodontic  | Date: 16 Mar 2026', 'Consultation Audits', 1774841263492, 'Prosthodontic ', '16 Mar 2026', 'hi'),
(37, 1, 'Vijay', 'good morning doctor event for dental check up it went good and it looks pit confusion ', 75, 'Interested', '00:10', NULL, 'Dept: oral surgery | Date: 30 Mar 2026', 'Consultation Audits', 1774841839156, 'oral surgery', '30 Mar 2026', 'NA'),
(38, 8, 'g', 'doctor Anderson recruitment and I will definitely come to next appointment you give helping the pain that is a lot ', 83, 'Interested', '00:15', NULL, 'Dept: y | Date: 30 Mar 2026', 'Consultation Audits', 1774849947960, 'y', '30 Mar 2026', 'g');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `designation` varchar(255) DEFAULT NULL,
  `registration_id` varchar(255) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `profile_photo` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `name`, `email`, `designation`, `registration_id`, `password`, `created_at`, `profile_photo`) VALUES
(1, 'Raja Shekhar Rayanuthala', 'rajashekharr1205.sse@saveetha.com', 'Consultant', '192211205', 'Rajashekharr1205@', '2026-03-11 08:13:27', '/uploads/profile_photos/user_1_1775430403_temp_profile_photo.jpg'),
(3, 'Subhan', 'mahaboobsubhanisk1745.sse@saveetha.com', 'Doctor', '192211745', 'Subhani@123', '2026-03-12 09:01:11', '/uploads/profile_photos/user_3_1773317392_temp_profile_photo.jpg'),
(4, 'Single Click Test', 'test@example.com', 'Doctor', '99999', 'password', '2026-03-14 17:38:51', NULL),
(6, 'Raviteja', 'ravitejareddy0667.sse@saveetha.com', 'Doctor', '192210667', 'Raviteja@0667', '2026-03-24 04:56:49', NULL),
(7, 'Nithin', 'nithinkumarch1625.sse@saveetha.com', 'Doctor', '192211625', 'Qwer@1234', '2026-03-26 05:04:33', '/uploads/profile_photos/user_7_1774481729_temp_profile_photo.jpg'),
(8, '87656789', '1@12', 'gkjhgjh', 'vhjv,hj', 'fcgkhcf,gj', '2026-03-30 05:40:40', '/uploads/profile_photos/user_8_1774829882_temp_profile_photo.jpg');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `otp_codes`
--
ALTER TABLE `otp_codes`
  ADD PRIMARY KEY (`id`),
  ADD KEY `email` (`email`);

--
-- Indexes for table `reports`
--
ALTER TABLE `reports`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `otp_codes`
--
ALTER TABLE `otp_codes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=67;

--
-- AUTO_INCREMENT for table `reports`
--
ALTER TABLE `reports`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=39;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `reports`
--
ALTER TABLE `reports`
  ADD CONSTRAINT `reports_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

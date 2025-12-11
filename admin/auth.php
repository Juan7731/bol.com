<?php
/**
 * Authentication check - Include this at the top of protected pages
 */

session_start();

// Check if user is logged in
if (!isset($_SESSION['admin_logged_in']) || $_SESSION['admin_logged_in'] !== true) {
    header('Location: login.php');
    exit;
}

// Refresh session
$_SESSION['last_activity'] = time();


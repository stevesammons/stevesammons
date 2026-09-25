<?php
require_once ABSPATH . 'wp-admin/includes/misc.php';
$ht = ABSPATH . '.htaccess';
if ( file_exists( $ht ) && is_writable( $ht ) ) {
	copy( $ht, $ht . '.ss-backup-' . gmdate( 'Ymd-His' ) );
	insert_with_markers( $ht, 'SS Browser Caching', ["<IfModule mod_expires.c>", "ExpiresActive On", "ExpiresByType image/jpeg \"access plus 30 days\"", "ExpiresByType image/png \"access plus 30 days\"", "ExpiresByType image/webp \"access plus 30 days\"", "ExpiresByType image/svg+xml \"access plus 30 days\"", "ExpiresByType image/x-icon \"access plus 30 days\"", "ExpiresByType text/css \"access plus 30 days\"", "ExpiresByType application/javascript \"access plus 30 days\"", "ExpiresByType text/javascript \"access plus 30 days\"", "ExpiresByType font/woff2 \"access plus 1 year\"", "ExpiresByType font/woff \"access plus 1 year\"", "ExpiresByType text/plain \"access plus 1 day\"", "</IfModule>", "<IfModule mod_headers.c>", "<FilesMatch \"\\.(jpe?g|png|webp|svg|ico|css|js|woff2?)$\">", "Header set Cache-Control \"public, max-age=2592000\"", "</FilesMatch>", "</IfModule>"] );
}
$u = wp_upload_dir();
foreach ( array( 'ss-cache-test', 'ss-cache-control' ) as $d ) {
	$p = trailingslashit( $u['basedir'] ) . $d;
	foreach ( (array) glob( $p . '/{,.}*', GLOB_BRACE ) as $f ) { if ( is_file( $f ) ) { unlink( $f ); } }
	@rmdir( $p );
}

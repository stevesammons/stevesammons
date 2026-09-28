<?php
// Single-use snippet (2026-09-25): rename the primary menu's "Deep Dives" item (4019) to "Podcast".
// Menu items can't be edited over REST on this site, so this runs once inside WordPress.
if ( ! get_option( 'ss_menu_podcast_rename' ) ) {
	update_option( 'ss_menu_podcast_rename', 1, false );
	remove_all_actions( 'wp_update_nav_menu_item' );
	$item = get_post( 4019 );
	if ( $item && 'nav_menu_item' === $item->post_type && 'Deep Dives' === $item->post_title ) {
		wp_update_post( array( 'ID' => 4019, 'post_title' => 'Podcast' ) );
	}
}

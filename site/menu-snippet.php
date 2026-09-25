<?php
// Single-use snippet: rebuild the primary menu (id 14, also the mobile menu) and the footer bottom bar.
// Menu items can't be created over REST on this site (a hook on wp_update_nav_menu_item demands an
// admin nonce), so this runs inside WordPress with that hook removed. Pages are found by path.
remove_all_actions( 'wp_update_nav_menu_item' );
$menu = 14;
foreach ( (array) wp_get_nav_menu_items( $menu, array( 'post_status' => 'any' ) ) as $old ) {
	wp_delete_post( $old->ID, true );
}
$pos   = 0;
$items = array(
	array( 'Characters', 'bible-characters', '', '' ),
	array( 'Songs', 'songs', '', '' ),
	array( 'Maps', 'bible-maps', '', '' ),
	array( 'Deep Dives', '', 'https://sammons.substack.com/podcast', '' ),
	array( 'About', 'about', '', '' ),
	array( 'Subscribe', 'subscribe', '', 'ss-menu-subscribe' ),
);
foreach ( $items as $it ) {
	list( $title, $path, $url, $class ) = $it;
	$pos++;
	$args = array( 'menu-item-title' => $title, 'menu-item-status' => 'publish', 'menu-item-position' => $pos, 'menu-item-classes' => $class );
	if ( $path ) {
		$page = get_page_by_path( $path );
		if ( ! $page ) {
			continue;
		}
		$args += array( 'menu-item-object' => 'page', 'menu-item-object-id' => $page->ID, 'menu-item-type' => 'post_type' );
	} else {
		$args += array( 'menu-item-type' => 'custom', 'menu-item-url' => $url, 'menu-item-target' => '_blank' );
	}
	wp_update_nav_menu_item( $menu, 0, $args );
}
set_theme_mod( 'footer_text', "&copy; 2026 Steve Sammons &middot; <a href=\"https://stevesammons.com/privacy-policy/\">Privacy Policy</a> &middot; <a href=\"https://stevesammons.com/about/\">About</a> &middot; <a href=\"https://stevesammons.com/subscribe/\">Subscribe</a>" );

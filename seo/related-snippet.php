<?php
/**
 * "Keep reading" block after each post: four related published posts (same category,
 * ranked by shared tags, then recency), plus hub links for Bible character posts.
 * Installed as a Code Snippets snippet (front-end scope). Source: seo/related-snippet.php.
 */

if ( ! function_exists( 'ss_related_posts' ) ) {

	function ss_related_posts( $post_id, $limit = 4 ) {
		$key    = 'ss_rel_v1_' . $post_id;
		$cached = get_transient( $key );
		if ( is_array( $cached ) ) {
			return $cached;
		}
		$cats = wp_get_post_categories( $post_id );
		$tags = wp_get_post_tags( $post_id, array( 'fields' => 'ids' ) );
		$cand = get_posts( array(
			'post_type'           => 'post',
			'post_status'         => 'publish',
			'posts_per_page'      => 40,
			'post__not_in'        => array( $post_id ),
			'category__in'        => $cats ? $cats : array( 0 ),
			'ignore_sticky_posts' => true,
			'no_found_rows'       => true,
			'fields'              => 'ids',
		) );
		$scored = array();
		foreach ( $cand as $i => $cid ) {
			$shared = $tags ? count( array_intersect( $tags, wp_get_post_tags( $cid, array( 'fields' => 'ids' ) ) ) ) : 0;
			$scored[ $cid ] = $shared * 10 - $i * 0.1; // tags first, then newest
		}
		arsort( $scored );
		$ids = array_slice( array_keys( $scored ), 0, $limit );
		if ( count( $ids ) < $limit ) {
			$more = get_posts( array( 'post_status' => 'publish', 'posts_per_page' => $limit, 'post__not_in' => array_merge( array( $post_id ), $ids ), 'fields' => 'ids', 'no_found_rows' => true ) );
			$ids  = array_slice( array_merge( $ids, $more ), 0, $limit );
		}
		set_transient( $key, $ids, 12 * HOUR_IN_SECONDS );
		return $ids;
	}

	add_filter( 'the_content', function ( $content ) {
		if ( ! is_singular( 'post' ) || ! in_the_loop() || ! is_main_query() ) {
			return $content;
		}
		$post_id = get_the_ID();
		$ids     = ss_related_posts( $post_id );
		if ( ! $ids ) {
			return $content;
		}
		$ot   = get_category_by_slug( 'old-testament' );
		$nt   = get_category_by_slug( 'new-testament' );
		$cats = wp_get_post_categories( $post_id );
		$bib  = ( $ot && in_array( $ot->term_id, $cats, true ) ) ? $ot : ( ( $nt && in_array( $nt->term_id, $cats, true ) ) ? $nt : null );

		$h  = '<aside class="ss-rel" aria-label="Keep reading"><h2 class="ss-rel-h">Keep reading</h2><div class="ss-rel-grid">';
		foreach ( $ids as $rid ) {
			$thumb = get_the_post_thumbnail( $rid, 'medium', array( 'loading' => 'lazy', 'class' => 'ss-rel-img', 'alt' => '' ) );
			$cat   = get_the_category( $rid );
			$h    .= '<a class="ss-rel-card" href="' . esc_url( get_permalink( $rid ) ) . '">' . ( $thumb ? $thumb : '<span class="ss-rel-img ss-rel-noimg" aria-hidden="true"></span>' )
				. '<span class="ss-rel-cat">' . esc_html( $cat ? $cat[0]->name : '' ) . '</span>'
				. '<span class="ss-rel-t">' . esc_html( wp_strip_all_tags( get_the_title( $rid ) ) ) . '</span></a>';
		}
		$h .= '</div>';
		if ( $bib ) {
			$hub = get_page_by_path( 'bible-characters' );
			$h  .= '<p class="ss-rel-more">Explore more: ';
			if ( $hub ) {
				$h .= '<a href="' . esc_url( get_permalink( $hub ) ) . '">All Bible characters</a> &middot; ';
			}
			$h .= '<a href="' . esc_url( get_category_link( $bib ) ) . '">More ' . esc_html( $bib->name ) . ' stories</a> &middot; <a href="' . esc_url( home_url( '/tag/bible-map/' ) ) . '">Bible maps</a></p>';
		}
		$h .= '</aside>';
		static $css = false;
		if ( ! $css ) {
			$css = true;
			$h  .= '<style>.ss-rel{margin:48px 0 8px;padding-top:24px;border-top:1px solid #e6e2d8}.ss-rel-h{font-size:1.3em;margin:0 0 16px}'
				. '.ss-rel-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:16px}'
				. '.ss-rel-card{display:flex;flex-direction:column;gap:6px;text-decoration:none!important;color:#111!important}'
				. '.ss-rel-img{display:block;width:100%;aspect-ratio:16/9;height:auto;object-fit:cover;border-radius:4px;background:#222}'
				. '.ss-rel-noimg{background:linear-gradient(135deg,#1f1f1f,#4a4a4a)}'
				. '.ss-rel-cat{font-size:.7em;letter-spacing:.1em;text-transform:uppercase;color:#6b6b6b}'
				. '.ss-rel-t{font-weight:700;line-height:1.3}.ss-rel-card:hover .ss-rel-t{color:#dd3333}'
				. '.ss-rel-more{margin-top:18px;font-size:.9em}.ss-rel-more a{color:#dd3333}</style>';
		}
		return $content . $h;
	}, 20 );

	// Lists are cached for 12 hours, so newly published posts appear within half a day.
}

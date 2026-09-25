<?php
/**
 * stevesammons.com SEO essentials (installed as a Code Snippets snippet, front-end scope).
 * Meta descriptions, JSON-LD structured data, robots rules for thin archives, sitemap
 * cleanup, a homepage H1 and a redirect for the old bio URL. Social tags stay with the
 * site's own sammons-social-tags plugin. Source: seo/seo-snippet.php in the site repo.
 */

if ( ! function_exists( 'ss_seo_trim' ) ) {

	function ss_seo_trim( $text, $len = 155 ) {
		$text = trim( preg_replace( '/\s+/', ' ', wp_strip_all_tags( strip_shortcodes( (string) $text ) ) ) );
		if ( mb_strlen( $text ) <= $len ) {
			return $text;
		}
		$cut = mb_substr( $text, 0, $len - 1 );
		$sp  = strrpos( $cut, " " );
		return rtrim( $sp ? mb_substr( $cut, 0, $sp ) : $cut, " ,.;:-" ) . '…';
	}

	function ss_seo_text( $t ) {
		return html_entity_decode( wp_strip_all_tags( (string) $t ), ENT_QUOTES | ENT_HTML5, 'UTF-8' );
	}

	function ss_seo_home_description() {
		return 'Leadership lessons from the people of the Bible, with character profiles and interactive maps, plus practical writing on leadership, faith and marketing by Steve Sammons.';
	}

	function ss_seo_description() {
		if ( is_front_page() || is_home() ) {
			return ss_seo_home_description();
		}
		if ( is_singular() ) {
			$post = get_queried_object();
			if ( ! $post ) {
				return '';
			}
			if ( has_excerpt( $post ) ) {
				return ss_seo_trim( $post->post_excerpt );
			}
			$content = preg_replace( '#<(script|style|noscript|figure|nav)[^>]*>.*?</\1>#is', ' ', $post->post_content );
			return ss_seo_trim( $content );
		}
		if ( is_category() || is_tag() || is_tax() ) {
			$term = get_queried_object();
			if ( $term && ! empty( $term->description ) ) {
				return ss_seo_trim( $term->description );
			}
			if ( $term ) {
				return ss_seo_trim( sprintf( 'Articles by Steve Sammons about %s.', $term->name ) );
			}
		}
		return '';
	}

	add_action( 'wp_head', function () {
		$d = ss_seo_description();
		if ( $d ) {
			echo '<meta name="description" content="' . esc_attr( $d ) . '" />' . "\n";
		}
	}, 2 );

	/* ---------- Structured data ---------- */
	function ss_seo_person() {
		$about = get_page_by_path( 'about' );
		return array(
			'@type'  => 'Person',
			'@id'    => home_url( '/#steve' ),
			'name'   => 'Steve Sammons',
			'url'    => $about ? get_permalink( $about ) : home_url( '/' ),
			'sameAs' => array( 'https://www.linkedin.com/in/sammons' ),
			'description' => 'Marketing executive, author and nonprofit leader who writes about leadership, character and faith.',
		);
	}

	function ss_seo_breadcrumbs() {
		$items = array( array( 'Home', home_url( '/' ) ) );
		if ( is_singular( 'post' ) ) {
			$cats = get_the_category();
			if ( $cats ) {
				$c = $cats[0];
				if ( $c->parent ) {
					$p = get_category( $c->parent );
					$items[] = array( $p->name, get_category_link( $p ) );
				}
				$items[] = array( $c->name, get_category_link( $c ) );
			}
			$items[] = array( get_the_title(), get_permalink() );
		} elseif ( is_page() && ! is_front_page() ) {
			$anc = array_reverse( get_post_ancestors( get_queried_object_id() ) );
			foreach ( $anc as $a ) {
				$items[] = array( get_the_title( $a ), get_permalink( $a ) );
			}
			$items[] = array( get_the_title(), get_permalink() );
		} elseif ( is_category() || is_tag() ) {
			$t = get_queried_object();
			if ( $t && ! empty( $t->parent ) ) {
				$p = get_term( $t->parent );
				$items[] = array( $p->name, get_term_link( $p ) );
			}
			$items[] = array( single_term_title( '', false ), get_term_link( $t ) );
		} else {
			return null;
		}
		$list = array();
		foreach ( $items as $i => $it ) {
			$list[] = array( '@type' => 'ListItem', 'position' => $i + 1, 'name' => ss_seo_text( $it[0] ), 'item' => $it[1] );
		}
		return array( '@type' => 'BreadcrumbList', '@id' => ( is_singular() ? get_permalink() : home_url( add_query_arg( array() ) ) ) . '#breadcrumb', 'itemListElement' => $list );
	}

	add_action( 'wp_head', function () {
		$graph   = array();
		$person  = ss_seo_person();
		$graph[] = $person;
		$graph[] = array(
			'@type'       => 'WebSite',
			'@id'         => home_url( '/#website' ),
			'url'         => home_url( '/' ),
			'name'        => get_bloginfo( 'name' ),
			'description' => get_bloginfo( 'description' ),
			'publisher'   => array( '@id' => $person['@id'] ),
			'inLanguage'  => 'en-US',
			'potentialAction' => array(
				'@type'       => 'SearchAction',
				'target'      => home_url( '/?s={search_term_string}' ),
				'query-input' => 'required name=search_term_string',
			),
		);
		if ( is_singular( 'post' ) ) {
			$id   = get_queried_object_id();
			$img  = get_the_post_thumbnail_url( $id, 'full' );
			$tags = wp_get_post_tags( $id, array( 'fields' => 'names' ) );
			$cats = wp_get_post_categories( $id, array( 'fields' => 'names' ) );
			$art  = array(
				'@type'            => 'BlogPosting',
				'@id'              => get_permalink( $id ) . '#article',
				'headline'         => ss_seo_text( get_the_title( $id ) ),
				'description'      => ss_seo_description(),
				'datePublished'    => get_the_date( 'c', $id ),
				'dateModified'     => get_the_modified_date( 'c', $id ),
				'author'           => array( '@id' => $person['@id'] ),
				'publisher'        => array( '@id' => $person['@id'] ),
				'mainEntityOfPage' => get_permalink( $id ),
				'isPartOf'         => array( '@id' => home_url( '/#website' ) ),
				'inLanguage'       => 'en-US',
				'wordCount'        => str_word_count( wp_strip_all_tags( get_post_field( 'post_content', $id ) ) ),
			);
			if ( $img ) {
				$art['image'] = $img;
			}
			if ( $cats ) {
				$art['articleSection'] = array_values( $cats );
			}
			if ( $tags ) {
				$art['keywords'] = implode( ', ', array_slice( $tags, 0, 12 ) );
			}
			$graph[] = $art;
		} elseif ( is_page() && ! is_front_page() ) {
			$graph[] = array(
				'@type'       => 'WebPage',
				'@id'         => get_permalink() . '#webpage',
				'url'         => get_permalink(),
				'name'        => ss_seo_text( get_the_title() ),
				'description' => ss_seo_description(),
				'isPartOf'    => array( '@id' => home_url( '/#website' ) ),
				'author'      => array( '@id' => $person['@id'] ),
				'dateModified' => get_the_modified_date( 'c' ),
				'inLanguage'  => 'en-US',
			);
		}
		$bc = ss_seo_breadcrumbs();
		if ( $bc ) {
			$graph[] = $bc;
		}
		echo '<script type="application/ld+json">' . wp_json_encode( array( '@context' => 'https://schema.org', '@graph' => $graph ), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE ) . '</script>' . "\n";
	}, 20 );

	/* ---------- Robots: keep thin archives out of search results ---------- */
	add_filter( 'wp_robots', function ( $robots ) {
		$thin = false;
		if ( is_tag() ) {
			$t    = get_queried_object();
			$thin = $t && (int) $t->count < 3;
		}
		if ( is_date() || is_author() || is_search() || is_attachment() || ( is_paged() && ( is_tag() ) ) ) {
			$thin = true;
		}
		if ( $thin ) {
			unset( $robots['max-image-preview'] );
			$robots['noindex'] = true;
			$robots['follow']  = true;
		}
		return $robots;
	} );

	/* ---------- Sitemap: only pages worth indexing ---------- */
	add_filter( 'wp_sitemaps_add_provider', function ( $provider, $name ) {
		return 'users' === $name ? false : $provider;
	}, 10, 2 );
	add_filter( 'wp_sitemaps_post_types', function ( $types ) {
		unset( $types['mailpoet_page'], $types['glossary'] );
		return $types;
	} );
	add_filter( 'wp_sitemaps_taxonomies_query_args', function ( $args, $taxonomy ) {
		if ( 'post_tag' === $taxonomy ) {
			$ids = get_terms( array( 'taxonomy' => 'post_tag', 'hide_empty' => true, 'fields' => 'ids', 'number' => 0 ) );
			$keep = array();
			foreach ( (array) $ids as $tid ) {
				$term = get_term( $tid );
				if ( $term && ! is_wp_error( $term ) && (int) $term->count >= 3 ) {
					$keep[] = (int) $tid;
				}
			}
			$args['include'] = $keep ? $keep : array( 0 );
		}
		return $args;
	}, 10, 2 );

	/* ---------- Homepage heading for search engines and screen readers ---------- */
	add_action( 'loop_start', function ( $q ) {
		static $done = false;
		if ( ! $done && $q->is_main_query() && ( is_front_page() || is_home() ) && ! is_paged() ) {
			$done = true;
			echo '<h1 class="screen-reader-text" style="position:absolute!important;width:1px;height:1px;overflow:hidden;clip:rect(1px,1px,1px,1px);white-space:nowrap">Steve Sammons: Helping leaders build the character worth following</h1>';
		}
	} );


	/* ---------- Homepage share image ---------- */
	add_action( 'wp_head', function () {
		if ( is_front_page() || is_home() ) {
			$img = 'https://stevesammons.com/wp-content/uploads/2026/09/steve-sammons-share.jpg';
			echo '<meta property="og:image" content="' . esc_url( $img ) . '" />' . "\n";
			echo '<meta property="og:image:width" content="1200" /><meta property="og:image:height" content="630" />' . "\n";
			echo '<meta name="twitter:image" content="' . esc_url( $img ) . '" />' . "\n";
		}
	}, 5 );

	/* ---------- Readable text (WCAG AA contrast) ---------- */
	add_action( 'wp_head', function () {
		echo '<style id="ss-contrast">body,select,input[type=search],input[type=text],input[type=email],textarea,.entry-content,html body .entry-content p,html body .entry-content li,html body .entry-content td,html body .entry-content dd{color:#555}'
			. 'blockquote cite,figcaption,.wp-caption-text,.wp-block-image figcaption,.entry-content figcaption,.post-meta,.post-categories,.post-count,.sub-title,.timestamp,.text-small,.comment-metadata,.comment-metadata a,label,.logged-in-as,.pk-color-secondary{color:#6b6b6b}</style>' . "\n";
	}, 999 );

	/* ---------- Old bio URL -> About ---------- */
	add_action( 'template_redirect', function () {
		$path = trim( (string) wp_parse_url( $_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH ), '/' );
		if ( 'stevesammons' === $path && get_page_by_path( 'about' ) ) {
			wp_safe_redirect( home_url( '/about/' ), 301 );
			exit;
		}
	} );
}

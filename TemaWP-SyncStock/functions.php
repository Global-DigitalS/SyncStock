<?php
/**
 * SyncStock - Funciones del tema
 *
 * @package SyncStock
 * @since 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'SYNCSTOCK_VERSION', '1.0.0' );
define( 'SYNCSTOCK_DIR', get_template_directory() );
define( 'SYNCSTOCK_URI', get_template_directory_uri() );

/**
 * Configuración del tema
 */
function syncstock_setup() {
	// Soporte para idioma
	load_theme_textdomain( 'syncstock', SYNCSTOCK_DIR . '/languages' );

	// Soporte para título dinámico
	add_theme_support( 'title-tag' );

	// Soporte para imágenes destacadas
	add_theme_support( 'post-thumbnails' );

	// Soporte para logo personalizado
	add_theme_support( 'custom-logo', array(
		'height'      => 48,
		'width'       => 180,
		'flex-height' => true,
		'flex-width'  => true,
	) );

	// Soporte para HTML5
	add_theme_support( 'html5', array(
		'search-form',
		'comment-form',
		'comment-list',
		'gallery',
		'caption',
		'style',
		'script',
	) );

	// Soporte para editor de bloques
	add_theme_support( 'wp-block-styles' );
	add_theme_support( 'editor-styles' );
	add_theme_support( 'responsive-embeds' );
	add_theme_support( 'align-wide' );

	// Registrar menús de navegación
	register_nav_menus( array(
		'primary'   => __( 'Menú Principal', 'syncstock' ),
		'footer'    => __( 'Menú del Pie de Página', 'syncstock' ),
		'legal'     => __( 'Menú Legal', 'syncstock' ),
	) );

	// Tamaños de imagen personalizados
	add_image_size( 'syncstock-hero', 1200, 675, true );
	add_image_size( 'syncstock-card', 600, 400, true );
	add_image_size( 'syncstock-icon', 80, 80, true );
	add_image_size( 'syncstock-blog-thumb', 400, 250, true );
}
add_action( 'after_setup_theme', 'syncstock_setup' );

/**
 * Cargar estilos y scripts
 */
function syncstock_enqueue_assets() {
	// Google Fonts
	wp_enqueue_style(
		'syncstock-google-fonts',
		'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap',
		array(),
		null
	);

	// Estilos personalizados del tema
	wp_enqueue_style(
		'syncstock-custom',
		SYNCSTOCK_URI . '/assets/css/custom.css',
		array(),
		SYNCSTOCK_VERSION
	);

	// Scripts del tema
	wp_enqueue_script(
		'syncstock-scripts',
		SYNCSTOCK_URI . '/assets/js/theme.js',
		array(),
		SYNCSTOCK_VERSION,
		true
	);
}
add_action( 'wp_enqueue_scripts', 'syncstock_enqueue_assets' );

/**
 * Estilos del editor
 */
function syncstock_editor_assets() {
	wp_enqueue_style(
		'syncstock-google-fonts-editor',
		'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Manrope:wght@400;500;600;700;800&display=swap',
		array(),
		null
	);

	wp_enqueue_style(
		'syncstock-editor-styles',
		SYNCSTOCK_URI . '/assets/css/editor.css',
		array(),
		SYNCSTOCK_VERSION
	);
}
add_action( 'enqueue_block_editor_assets', 'syncstock_editor_assets' );

/**
 * Registrar categoría de patrones de bloques
 */
function syncstock_register_pattern_categories() {
	register_block_pattern_category( 'syncstock', array(
		'label' => __( 'SyncStock', 'syncstock' ),
	) );
	register_block_pattern_category( 'syncstock-hero', array(
		'label' => __( 'SyncStock — Hero', 'syncstock' ),
	) );
	register_block_pattern_category( 'syncstock-features', array(
		'label' => __( 'SyncStock — Características', 'syncstock' ),
	) );
	register_block_pattern_category( 'syncstock-pricing', array(
		'label' => __( 'SyncStock — Precios', 'syncstock' ),
	) );
	register_block_pattern_category( 'syncstock-testimonials', array(
		'label' => __( 'SyncStock — Testimonios', 'syncstock' ),
	) );
	register_block_pattern_category( 'syncstock-cta', array(
		'label' => __( 'SyncStock — CTA', 'syncstock' ),
	) );
	register_block_pattern_category( 'syncstock-content', array(
		'label' => __( 'SyncStock — Contenido', 'syncstock' ),
	) );
}
add_action( 'init', 'syncstock_register_pattern_categories' );

/**
 * Registrar patrones de bloques desde archivos PHP
 */
function syncstock_register_block_patterns() {
	$patterns_dir = SYNCSTOCK_DIR . '/patterns/';

	if ( ! is_dir( $patterns_dir ) ) {
		return;
	}

	$pattern_files = glob( $patterns_dir . '*.php' );

	foreach ( $pattern_files as $file ) {
		// El registro automático de patrones lo maneja WordPress 6.0+
		// Los archivos PHP en /patterns/ con cabeceras válidas se registran automáticamente
	}
}
add_action( 'init', 'syncstock_register_block_patterns' );

/**
 * Desactivar patrones remotos de WordPress.org
 */
add_filter( 'should_load_remote_block_patterns', '__return_false' );

/**
 * Personalizar el excerpt
 */
function syncstock_excerpt_length( $length ) {
	return 25;
}
add_filter( 'excerpt_length', 'syncstock_excerpt_length' );

function syncstock_excerpt_more( $more ) {
	return '…';
}
add_filter( 'excerpt_more', 'syncstock_excerpt_more' );

/**
 * Agregar clases al body
 */
function syncstock_body_classes( $classes ) {
	$classes[] = 'syncstock-theme';

	if ( is_front_page() ) {
		$classes[] = 'syncstock-home';
	}

	return $classes;
}
add_filter( 'body_class', 'syncstock_body_classes' );

/**
 * Widget areas (sidebar del footer)
 */
function syncstock_widgets_init() {
	register_sidebar( array(
		'name'          => __( 'Pie de Página - Columna 1', 'syncstock' ),
		'id'            => 'footer-1',
		'description'   => __( 'Primera columna del pie de página.', 'syncstock' ),
		'before_widget' => '<div class="widget %2$s">',
		'after_widget'  => '</div>',
		'before_title'  => '<h4 class="widget-title">',
		'after_title'   => '</h4>',
	) );

	register_sidebar( array(
		'name'          => __( 'Pie de Página - Columna 2', 'syncstock' ),
		'id'            => 'footer-2',
		'description'   => __( 'Segunda columna del pie de página.', 'syncstock' ),
		'before_widget' => '<div class="widget %2$s">',
		'after_widget'  => '</div>',
		'before_title'  => '<h4 class="widget-title">',
		'after_title'   => '</h4>',
	) );

	register_sidebar( array(
		'name'          => __( 'Pie de Página - Columna 3', 'syncstock' ),
		'id'            => 'footer-3',
		'description'   => __( 'Tercera columna del pie de página.', 'syncstock' ),
		'before_widget' => '<div class="widget %2$s">',
		'after_widget'  => '</div>',
		'before_title'  => '<h4 class="widget-title">',
		'after_title'   => '</h4>',
	) );
}
add_action( 'widgets_init', 'syncstock_widgets_init' );
